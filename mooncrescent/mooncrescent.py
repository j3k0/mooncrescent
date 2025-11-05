#!/usr/bin/env python3
"""Mooncrescent - Terminal UI for Moonraker/Klipper 3D Printers"""

import curses
import argparse
import sys
import time
import locale
from typing import Optional

from .config import PRINTER_HOST, PRINTER_PORT, UPDATE_INTERVAL, HISTORY_FILE, FILTER_PATTERNS, FILTER_OK_RESPONSES, PRINT_HISTORY_FILE
from .moonraker_client import MoonrakerClient
from .ui_layout import UILayout
from .command_handler import CommandHandler


class MoonrakerTUI:
    """Main TUI application"""
    
    def __init__(self, stdscr, host: str, port: int):
        self.stdscr = stdscr
        self.host = host
        self.port = port
        
        # Initialize components
        self.client: Optional[MoonrakerClient] = None
        self.ui: Optional[UILayout] = None
        self.cmd_handler = CommandHandler()
        
        # Load command history from disk
        self.cmd_handler.load_history(HISTORY_FILE)
        
        # State
        self.running = True
        self.file_list_cache = []  # Cache for file list (for tab completion)
        self.file_list_cache_time = 0  # Last time we fetched file list
        self.file_id_map = {}  # Map file IDs (#0, #1, etc.) to filenames (#0 = newest)
        
        # Print history tracking
        self.last_print_state = None
        self.current_print_start_time = None
        
        # Setup
        self._setup_curses()
        
    def _setup_curses(self):
        """Configure curses settings"""
        # Hide cursor initially
        curses.curs_set(0)
        
        # Enable keypad mode
        self.stdscr.keypad(True)
        
        # Non-blocking input
        self.stdscr.nodelay(True)
        
        # No echo
        curses.noecho()
        
        # Enable raw mode
        curses.cbreak()
        
    def run(self):
        """Main application loop"""
        try:
            # Initialize UI
            self.ui = UILayout(self.stdscr)
            self.ui.add_terminal_line("Mooncrescent starting...", is_command=False)
            self.ui.add_terminal_line(f"Connecting to {self.host}:{self.port}...", is_command=False)
            self.ui.render()
            
            # Connect to Moonraker
            self.client = MoonrakerClient(self.host, self.port)
            if not self.client.connect():
                self.ui.add_terminal_line("Failed to connect to Moonraker", is_error=True)
                self.ui.add_terminal_line("Press ESC to quit", is_command=False)
                self.ui.render()
                
                # Wait for quit
                self.stdscr.nodelay(False)
                while True:
                    key = self.stdscr.getch()
                    if key == ord('q'):
                        break
                return
            
            self.ui.add_terminal_line("Connected successfully!", is_command=False)
            self.ui.set_connected(True)
            
            # Get initial state
            initial_state = self.client.get_printer_objects()
            if initial_state:
                self.ui.update_status(initial_state)
                
            # Main event loop
            last_update = time.time()
            
            while self.running:
                current_time = time.time()
                
                # Handle keyboard input (returns True if UI needs immediate update)
                input_changed = self._handle_input()
                
                # Process messages from WebSocket
                self._process_messages()
                
                # Update UI immediately after user input
                if input_changed:
                    self._update_ui()
                    last_update = current_time  # Reset timer
                # Or periodic UI update for status changes
                elif current_time - last_update >= UPDATE_INTERVAL:
                    self._update_ui()
                    last_update = current_time
                    
                # Small sleep to avoid CPU spinning
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
            
    def _handle_input(self):
        """Handle keyboard input, returns True if UI needs immediate update"""
        try:
            key = self.stdscr.getch()
            
            if key == -1:  # No input
                return False
                
            # Quit shortcuts (ESC or CTRL-D)
            if key == 27 or key == 4:  # ESC or CTRL-D
                self.running = False
                return False
                
            # Help shortcut
            elif key == ord('?'):
                self._show_help()
                return True  # Help added text to terminal, needs update
                
            # Command input handling
            if key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                # Submit command
                command = self.cmd_handler.submit_command()
                if command:
                    self._send_command(command)
                return True  # Command line cleared, needs update
                    
            elif key == ord('\t'):  # Tab - auto-complete
                self._handle_tab_complete()
                return True  # Completion may have changed text
                
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                self.cmd_handler.delete_char()
                return True  # Text changed
                
            elif key == curses.KEY_DC:  # Delete key
                self.cmd_handler.delete_char_forward()
                return True  # Text changed
                
            elif key == curses.KEY_LEFT:
                self.cmd_handler.move_cursor(-1)
                return True  # Cursor moved
                
            elif key == curses.KEY_RIGHT:
                self.cmd_handler.move_cursor(1)
                return True  # Cursor moved
                
            elif key == curses.KEY_HOME:
                self.cmd_handler.move_cursor_home()
                return True  # Cursor moved
                
            elif key == curses.KEY_END:
                self.cmd_handler.move_cursor_end()
                return True  # Cursor moved
                
            elif key == curses.KEY_UP:
                self.cmd_handler.history_up()
                return True  # Text changed (history navigation)
                
            elif key == curses.KEY_DOWN:
                self.cmd_handler.history_down()
                return True  # Text changed (history navigation)
                
            elif key == curses.KEY_PPAGE:  # Page Up - scroll terminal up (to older content)
                self.ui.scroll_terminal(-10)
                return True  # Terminal scrolled
                
            elif key == curses.KEY_NPAGE:  # Page Down - scroll terminal down (to newer content)
                self.ui.scroll_terminal(10)
                return True  # Terminal scrolled
                
            elif key == curses.KEY_RESIZE:
                self.ui.resize()
                return True  # Screen resized
                
            elif 32 <= key <= 126:  # Printable characters
                self.cmd_handler.add_char(chr(key))
                return True  # Text changed
            
            return False  # Unknown key, no update needed
                    
        except curses.error:
            return False
            
    def _send_command(self, command: str):
        """Send G-code command to printer or handle special commands"""
        self.ui.add_terminal_line(f"> {command}", is_command=True)
        
        if not self.client:
            self.ui.add_terminal_line("Not connected", is_error=True)
            return
        
        # Handle special commands
        cmd_lower = command.strip().lower()
        
        # List files command (handle both "ls" and "ls -l")
        if cmd_lower.startswith("ls"):
            args = command[2:].strip()  # Get everything after "ls"
            self._handle_list_files(args)
            return
            
        # Reprint last file command
        if cmd_lower == "reprint":
            self._handle_reprint()
            return
            
        # Print file command
        if cmd_lower.startswith("print "):
            filename = command[6:].strip()  # Get filename after "print "
            self._handle_print_file(filename)
            return
        
        # Info file command
        if cmd_lower.startswith("info "):
            filename = command[5:].strip()
            self._handle_file_info(filename)
            return
        
        # History command
        if cmd_lower == "history":
            self._handle_history()
            return
        
        # Z-offset adjustment
        if cmd_lower.startswith("z "):
            args = command[2:].strip()
            self._handle_z_offset(args)
            return
        
        # Regular G-code command
        success = self.client.send_gcode(command)
        if not success:
            self.ui.add_terminal_line("Failed to send command", is_error=True)
            
    def _update_file_id_map(self, files: list):
        """Update file ID mapping (#0 = newest file, #1 = second newest, etc.)"""
        self.file_id_map = {}
        # Files are sorted oldest to newest, so reverse for ID assignment
        for i, file_info in enumerate(reversed(files)):
            filename = file_info.get("path", file_info.get("filename", ""))
            self.file_id_map[f"#{i}"] = filename
    
    def _resolve_filename(self, filename_or_id: str) -> str:
        """Resolve #N syntax to actual filename, or return filename as-is"""
        if filename_or_id.startswith("#"):
            return self.file_id_map.get(filename_or_id, filename_or_id)
        return filename_or_id
    
    def _handle_list_files(self, args: str = ""):
        """List available gcode files (oldest to newest)
        
        Args:
            args: Command arguments (e.g., "-l" for detailed view, "*pattern*" for filtering)
        """
        import fnmatch
        
        # Parse arguments: extract -l flag and glob pattern
        show_details = "-l" in args.lower()
        
        # Remove -l flag to get the pattern
        pattern = args.replace("-l", "").replace("-L", "").strip()
        
        files = self.client.get_files_list()
        
        if not files:
            self.ui.add_terminal_line("No files found or unable to query", is_command=False)
            return
        
        # Apply glob filter if pattern provided
        if pattern:
            filtered_files = []
            for file_info in files:
                filename = file_info.get("path", file_info.get("filename", ""))
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    filtered_files.append(file_info)
            files = filtered_files
            
            if not files:
                self.ui.add_terminal_line(f"No files matching '{pattern}'", is_command=False)
                return
        
        # Update file ID mapping with current file list
        self._update_file_id_map(files)
        
        if show_details:
            # Detailed view with metadata
            self.ui.add_terminal_line(f"{'ID':<5} {'SIZE':<10} {'TIME':<8} {'FILAMENT':<10} {'FILENAME'}", is_command=False)
            self.ui.add_terminal_line("-" * 70, is_command=False)
            
            for i, file_info in enumerate(files):
                filename = file_info.get("path", file_info.get("filename", "unknown"))
                
                # Get file ID (reverse index since #0 = newest)
                file_id = f"#{len(files) - 1 - i}"
                
                # Get metadata for each file (this may be slow for many files)
                metadata = self.client.get_file_metadata(filename)
                
                # Size
                size = file_info.get("size", 0)
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f}MB"
                else:
                    size_str = f"{size / 1024:.0f}KB"
                
                # Estimated time
                time_str = "?"
                if metadata and "estimated_time" in metadata:
                    time_sec = metadata["estimated_time"]
                    hours = int(time_sec // 3600)
                    minutes = int((time_sec % 3600) // 60)
                    time_str = f"{hours}h{minutes:02d}m"
                
                # Filament
                filament_str = "?"
                if metadata and "filament_total" in metadata:
                    filament_m = metadata["filament_total"] / 1000
                    filament_str = f"{filament_m:.1f}m"
                
                self.ui.add_terminal_line(
                    f"{file_id:<5} {size_str:<10} {time_str:<8} {filament_str:<10} {filename}", 
                    is_command=False
                )
        else:
            # Simple view with file IDs
            self.ui.add_terminal_line(f"Found {len(files)} file(s):", is_command=False)
            for i, file_info in enumerate(files):
                filename = file_info.get("path", file_info.get("filename", "unknown"))
                size = file_info.get("size", 0)
                
                # Get file ID (reverse index since #0 = newest)
                file_id = f"#{len(files) - 1 - i}"
                
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size / 1024:.2f} KB"
                self.ui.add_terminal_line(f"  {file_id:<5} {filename} ({size_str})", is_command=False)
            
    def _handle_reprint(self):
        """Reprint the last file"""
        # Get current filename from print_stats
        print_stats = self.client.printer_state.get("print_stats", {})
        filename = print_stats.get("filename", "")
        
        if not filename:
            self.ui.add_terminal_line("No previous file to reprint", is_error=True)
            return
            
        self.ui.add_terminal_line(f"Starting print: {filename}", is_command=False)
        success = self.client.start_print(filename)
        
        if success:
            self.ui.add_terminal_line("Print started successfully", is_command=False)
        else:
            self.ui.add_terminal_line("Failed to start print", is_error=True)
            
    def _handle_print_file(self, filename: str):
        """Start printing a specific file"""
        if not filename:
            self.ui.add_terminal_line("Usage: print <filename> or print #N", is_error=True)
            return
        
        # Resolve #N syntax to actual filename
        original_input = filename
        filename = self._resolve_filename(filename)
        
        if original_input.startswith("#") and filename == original_input:
            self.ui.add_terminal_line(f"Unknown file ID: {original_input}. Use 'ls' to see available files.", is_error=True)
            return
            
        self.ui.add_terminal_line(f"Starting print: {filename}", is_command=False)
        success = self.client.start_print(filename)
        
        if success:
            self.ui.add_terminal_line("Print started successfully", is_command=False)
        else:
            self.ui.add_terminal_line("Failed to start print", is_error=True)
            
    def _handle_file_info(self, filename: str):
        """Display detailed info about a file"""
        if not filename:
            self.ui.add_terminal_line("Usage: info <filename> or info #N", is_error=True)
            return
        
        # Resolve #N syntax to actual filename
        original_input = filename
        filename = self._resolve_filename(filename)
        
        if original_input.startswith("#") and filename == original_input:
            self.ui.add_terminal_line(f"Unknown file ID: {original_input}. Use 'ls' to see available files.", is_error=True)
            return
        
        metadata = self.client.get_file_metadata(filename)
        
        if not metadata:
            self.ui.add_terminal_line(f"Could not get info for: {filename}", is_error=True)
            return
        
        self.ui.add_terminal_line("=" * 50, is_command=False)
        self.ui.add_terminal_line(f"File: {filename}", is_command=False)
        self.ui.add_terminal_line("=" * 50, is_command=False)
        
        # Size
        size = metadata.get("size", 0)
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{size / 1024:.2f} KB"
        self.ui.add_terminal_line(f"Size: {size_str}", is_command=False)
        
        # Estimated time
        if "estimated_time" in metadata:
            time_sec = metadata["estimated_time"]
            hours = int(time_sec // 3600)
            minutes = int((time_sec % 3600) // 60)
            self.ui.add_terminal_line(f"Estimated time: {hours}h {minutes}m", is_command=False)
        
        # Filament usage
        if "filament_total" in metadata:
            filament_mm = metadata["filament_total"]
            filament_m = filament_mm / 1000
            # Rough estimate: 1m of 1.75mm filament ≈ 2.4g
            filament_g = filament_m * 2.4
            self.ui.add_terminal_line(f"Filament: {filament_m:.1f}m (~{filament_g:.1f}g)", is_command=False)
        
        # Layer heights
        if "first_layer_height" in metadata:
            self.ui.add_terminal_line(f"First layer: {metadata['first_layer_height']}mm", is_command=False)
        if "layer_height" in metadata:
            self.ui.add_terminal_line(f"Layer height: {metadata['layer_height']}mm", is_command=False)
        
        # Temperatures
        if "first_layer_bed_temp" in metadata:
            self.ui.add_terminal_line(f"Bed temp: {metadata['first_layer_bed_temp']}°C", is_command=False)
        if "first_layer_extr_temp" in metadata:
            self.ui.add_terminal_line(f"Hotend temp: {metadata['first_layer_extr_temp']}°C", is_command=False)
        
        # Slicer info
        if "slicer" in metadata:
            self.ui.add_terminal_line(f"Slicer: {metadata['slicer']}", is_command=False)
        
        self.ui.add_terminal_line("=" * 50, is_command=False)
    
    def _log_print_completion(self, print_stats: dict, status: str):
        """Log completed print to history file"""
        import os
        from datetime import datetime
        
        filename = print_stats.get("filename", "unknown")
        duration = print_stats.get("print_duration", 0)
        filament = print_stats.get("filament_used", 0)
        
        history_file = os.path.expanduser(PRINT_HISTORY_FILE)
        
        try:
            with open(history_file, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                filament_g = filament * 2.4  # Rough estimate
                f.write(f"{timestamp}|{filename}|{status}|{hours}h {minutes}m|{filament_g:.1f}g\n")
        except Exception:
            pass  # Silently fail
    
    def _handle_history(self):
        """Display print history"""
        import os
        
        history_file = os.path.expanduser(PRINT_HISTORY_FILE)
        
        if not os.path.exists(history_file):
            self.ui.add_terminal_line("No print history found", is_command=False)
            return
        
        try:
            with open(history_file, 'r') as f:
                lines = f.readlines()
            
            # Show last 20 prints
            lines = lines[-20:]
            
            self.ui.add_terminal_line("=" * 70, is_command=False)
            self.ui.add_terminal_line("Print History (last 20)", is_command=False)
            self.ui.add_terminal_line("=" * 70, is_command=False)
            
            for line in reversed(lines):  # Most recent first
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    timestamp, filename, status, duration, filament = parts
                    status_marker = "✓" if status == "completed" else "✗"
                    self.ui.add_terminal_line(
                        f"[{timestamp}] {status_marker} {filename} - {duration} - {filament}",
                        is_command=False
                    )
            
            self.ui.add_terminal_line("=" * 70, is_command=False)
        except Exception as e:
            self.ui.add_terminal_line(f"Error reading history: {e}", is_error=True)
    
    def _handle_z_offset(self, args: str):
        """Adjust Z offset for baby stepping
        
        Usage:
            z +0.05    - Raise nozzle by 0.05mm
            z -0.02    - Lower nozzle by 0.02mm
            z save     - Save current offset to config
        """
        if args == "save":
            # Save current Z offset to Klipper config
            self.client.send_gcode("SAVE_CONFIG")
            self.ui.add_terminal_line("Z offset saved to config (printer will restart)", is_command=False)
            return
        
        try:
            # Parse offset value (e.g., "+0.05" or "-0.02")
            offset = float(args)
            
            # Send SET_GCODE_OFFSET command with Z_ADJUST
            # MOVE=1 tells Klipper to move the toolhead immediately
            self.client.send_gcode(f"SET_GCODE_OFFSET Z_ADJUST={offset} MOVE=1")
            self.ui.add_terminal_line(f"Z offset adjusted by {offset:+.3f}mm", is_command=False)
        except ValueError:
            self.ui.add_terminal_line("Usage: z +0.05 | z -0.02 | z save", is_error=True)
            
    def _show_help(self):
        """Display help with available macros and common commands"""
        self.ui.add_terminal_line("=" * 50, is_command=False)
        self.ui.add_terminal_line("HELP - Available Commands", is_command=False)
        self.ui.add_terminal_line("=" * 50, is_command=False)
        
        # File management commands
        self.ui.add_terminal_line("", is_command=False)
        self.ui.add_terminal_line("File Management:", is_command=False)
        self.ui.add_terminal_line("  ls [pattern]       - List files (e.g., ls *TPU*)", is_command=False)
        self.ui.add_terminal_line("  ls -l [pattern]    - List with details (#ID, time, filament)", is_command=False)
        self.ui.add_terminal_line("  print <file>|#N    - Start printing (e.g., print #0)", is_command=False)
        self.ui.add_terminal_line("  reprint            - Reprint the last file", is_command=False)
        self.ui.add_terminal_line("  info <file>|#N     - Show detailed info (e.g., info #0)", is_command=False)
        self.ui.add_terminal_line("  history            - Show print history", is_command=False)
        self.ui.add_terminal_line("", is_command=False)
        self.ui.add_terminal_line("  Note: #0 = newest file, #1 = second newest, etc.", is_command=False)
        
        # Common G-code commands
        self.ui.add_terminal_line("", is_command=False)
        self.ui.add_terminal_line("Common G-code Commands:", is_command=False)
        self.ui.add_terminal_line("  G28        - Home all axes", is_command=False)
        self.ui.add_terminal_line("  G28 X Y    - Home X and Y axes", is_command=False)
        self.ui.add_terminal_line("  M104 S200  - Set hotend temp to 200°C", is_command=False)
        self.ui.add_terminal_line("  M140 S60   - Set bed temp to 60°C", is_command=False)
        self.ui.add_terminal_line("  M109 S200  - Set hotend temp and wait", is_command=False)
        self.ui.add_terminal_line("  M190 S60   - Set bed temp and wait", is_command=False)
        self.ui.add_terminal_line("  M106 S255  - Fan on (full speed)", is_command=False)
        self.ui.add_terminal_line("  M107       - Fan off", is_command=False)
        self.ui.add_terminal_line("  M114       - Get current position", is_command=False)
        self.ui.add_terminal_line("  M115       - Get firmware info", is_command=False)
        self.ui.add_terminal_line("  FIRMWARE_RESTART - Restart firmware", is_command=False)
        
        # Z-offset control
        self.ui.add_terminal_line("", is_command=False)
        self.ui.add_terminal_line("Z-Offset Control:", is_command=False)
        self.ui.add_terminal_line("  z +0.05            - Raise nozzle by 0.05mm", is_command=False)
        self.ui.add_terminal_line("  z -0.02            - Lower nozzle by 0.02mm", is_command=False)
        self.ui.add_terminal_line("  z save             - Save Z offset to config", is_command=False)
        
        # Fetch and display available macros
        if self.client:
            macros = self.client.get_available_macros()
            if macros:
                self.ui.add_terminal_line("", is_command=False)
                self.ui.add_terminal_line("Available Macros:", is_command=False)
                for macro in macros:
                    self.ui.add_terminal_line(f"  {macro}", is_command=False)
            else:
                self.ui.add_terminal_line("", is_command=False)
                self.ui.add_terminal_line("(No macros found or unable to query)", is_command=False)
        
        self.ui.add_terminal_line("", is_command=False)
        self.ui.add_terminal_line("Keyboard Shortcuts:", is_command=False)
        self.ui.add_terminal_line("  ?          - Show this help", is_command=False)
        self.ui.add_terminal_line("  Tab        - Auto-complete command", is_command=False)
        self.ui.add_terminal_line("  Up/Down    - Command history", is_command=False)
        self.ui.add_terminal_line("  ESC/Ctrl-D - Quit", is_command=False)
        self.ui.add_terminal_line("=" * 50, is_command=False)
        
    def _handle_tab_complete(self):
        """Handle tab completion for G-code commands, macros, and filenames"""
        current_text, cursor_pos = self.cmd_handler.get_display_text()
        
        if not current_text:
            return
        
        # Check if we're completing a filename after "print " or "info "
        if current_text.lower().startswith("print "):
            self._complete_filename(current_text, cursor_pos, "print ")
            return
        elif current_text.lower().startswith("info "):
            self._complete_filename(current_text, cursor_pos, "info ")
            return
            
        # Get word at cursor
        word_start = current_text.rfind(' ', 0, cursor_pos) + 1
        word = current_text[word_start:cursor_pos].upper()
        
        if not word:
            return
            
        # Build list of possible completions
        completions = []
        
        # Special commands (ls, print, reprint, info, history, z)
        special_commands = ["ls", "ls -l", "print", "reprint", "info", "history", "z"]
        for cmd in special_commands:
            if cmd.upper().startswith(word):
                completions.append(cmd)
        
        # Common G-code commands
        common_commands = [
            "G28", "G28 X", "G28 Y", "G28 Z", "G28 X Y",
            "G0", "G1", "G90", "G91",
            "M104", "M109", "M140", "M190",
            "M106", "M107", "M114", "M115", "M105",
            "M84", "M112", "FIRMWARE_RESTART"
        ]
        
        for cmd in common_commands:
            if cmd.startswith(word):
                completions.append(cmd)
        
        # Add macros if available
        if self.client:
            macros = self.client.get_available_macros()
            for macro in macros:
                if macro.upper().startswith(word):
                    completions.append(macro)
        
        # If only one completion, auto-complete
        if len(completions) == 1:
            completion = completions[0]
            # Replace the word with completion
            new_text = current_text[:word_start] + completion
            # If it's "print", add a space for filename entry
            if completion.lower() == "print":
                new_text += " "
            self.cmd_handler.command_buffer = new_text
            self.cmd_handler.cursor_position = len(new_text)
            
        # If multiple completions, show them
        elif len(completions) > 1:
            self.ui.add_terminal_line(f"Completions: {', '.join(completions)}", is_command=False)
            
            # Find common prefix
            if completions:
                common_prefix = completions[0]
                for comp in completions[1:]:
                    # Find common prefix between common_prefix and comp
                    i = 0
                    while i < len(common_prefix) and i < len(comp) and common_prefix[i] == comp[i]:
                        i += 1
                    common_prefix = common_prefix[:i]
                
                # If common prefix is longer than what we have, complete to it
                if len(common_prefix) > len(word):
                    new_text = current_text[:word_start] + common_prefix
                    self.cmd_handler.command_buffer = new_text
                    self.cmd_handler.cursor_position = len(new_text)
                    
    def _complete_filename(self, current_text: str, cursor_pos: int, prefix: str = "print "):
        """Handle filename completion for print/info commands"""
        # Refresh file list cache if older than 30 seconds
        current_time = time.time()
        if current_time - self.file_list_cache_time > 30:
            if self.client:
                files = self.client.get_files_list()
                self.file_list_cache = [f.get("path", f.get("filename", "")) for f in files]
                self.file_list_cache_time = current_time
                # Also update file ID mapping
                self._update_file_id_map(files)
        
        # Get the partial filename after prefix (e.g., "print " or "info ")
        partial = current_text[len(prefix):cursor_pos]
        
        # Find matching files
        completions = []
        for filename in self.file_list_cache:
            if filename.startswith(partial):
                completions.append(filename)
        
        # If no partial filename and no completions yet, show all files (Tab right after "print ")
        if not partial and not completions:
            completions = self.file_list_cache[:]
        
        # If only one completion, auto-complete
        if len(completions) == 1:
            new_text = prefix + completions[0]
            self.cmd_handler.command_buffer = new_text
            self.cmd_handler.cursor_position = len(new_text)
            
        # If multiple completions, show them
        elif len(completions) > 1:
            self.ui.add_terminal_line(f"Files: {', '.join(completions)}", is_command=False)
            
            # Find common prefix
            if completions:
                common_prefix = completions[0]
                for comp in completions[1:]:
                    i = 0
                    while i < len(common_prefix) and i < len(comp) and common_prefix[i] == comp[i]:
                        i += 1
                    common_prefix = common_prefix[:i]
                
                # If common prefix is longer than what we have, complete to it
                if len(common_prefix) > len(partial):
                    new_text = prefix + common_prefix
                    self.cmd_handler.command_buffer = new_text
                    self.cmd_handler.cursor_position = len(new_text)
        elif not completions and partial:
            self.ui.add_terminal_line("No matching files found", is_command=False)
            
    def _process_messages(self):
        """Process messages from Moonraker client"""
        if not self.client:
            return
            
        while True:
            message = self.client.get_message()
            if not message:
                break
                
            msg_type = message.get("type")
            
            if msg_type == "status_update":
                # Update printer state
                data = message.get("data", {})
                self.ui.update_status(data)
                
                # Track print state changes for history
                print_stats = data.get("print_stats", {})
                current_state = print_stats.get("state", "")
                
                if current_state == "printing" and self.last_print_state != "printing":
                    # Print started
                    self.current_print_start_time = time.time()
                    
                elif current_state == "complete" and self.last_print_state == "printing":
                    # Print completed - log it
                    self._log_print_completion(print_stats, "completed")
                    
                elif current_state == "cancelled" and self.last_print_state == "printing":
                    # Print cancelled - log it
                    self._log_print_completion(print_stats, "cancelled")
                
                self.last_print_state = current_state
                
            elif msg_type == "gcode_response":
                # Display G-code response
                response = message.get("response", "")
                if response.strip():
                    # Apply pattern filters (skip known spam)
                    should_skip = False
                    for pattern in FILTER_PATTERNS:
                        if pattern.lower() in response.lower():
                            should_skip = True
                            break
                    
                    if should_skip:
                        continue  # Skip messages matching filter patterns
                    
                    if FILTER_OK_RESPONSES and response.strip().lower() == "ok":
                        continue  # Skip standalone "ok" responses
                    
                    # Check if it's an error
                    is_error = response.lower().startswith("error") or "!!" in response
                    self.ui.add_terminal_line(response, is_command=False, is_error=is_error)
                    
            elif msg_type == "connection":
                # Connection status changed
                connected = message.get("connected", False)
                self.ui.set_connected(connected)
                if connected:
                    self.ui.add_terminal_line("Connected to Moonraker", is_command=False)
                else:
                    self.ui.add_terminal_line("Disconnected from Moonraker", is_error=True)
                    
            elif msg_type == "error":
                # Error message
                error_msg = message.get("message", "Unknown error")
                self.ui.add_terminal_line(f"Error: {error_msg}", is_error=True)
                
    def _update_ui(self):
        """Update UI display"""
        if self.ui:
            text, cursor_pos = self.cmd_handler.get_display_text()
            self.ui.render(text, cursor_pos)
            
    def _cleanup(self):
        """Cleanup resources"""
        # Save command history to disk
        self.cmd_handler.save_history(HISTORY_FILE)
        
        if self.client:
            self.client.disconnect()
        if self.ui:
            self.ui.cleanup()


def main():
    """Entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Mooncrescent - Terminal UI for Moonraker/Klipper 3D Printers")
    parser.add_argument("--host", default=PRINTER_HOST, help="Moonraker host address")
    parser.add_argument("--port", type=int, default=PRINTER_PORT, help="Moonraker port")
    args = parser.parse_args()
    
    # Set locale for proper Unicode support
    locale.setlocale(locale.LC_ALL, '')
    
    try:
        # Run curses application
        curses.wrapper(lambda stdscr: MoonrakerTUI(stdscr, args.host, args.port).run())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

