#!/usr/bin/env python3
"""Mooncrescent - Terminal UI for Moonraker/Klipper 3D Printers"""

import curses
import argparse
import sys
import time
import locale
from typing import Optional

from config import PRINTER_HOST, PRINTER_PORT, UPDATE_INTERVAL, HISTORY_FILE, FILTER_GCODE_COMMENTS, FILTER_OK_RESPONSES
from moonraker_client import MoonrakerClient
from ui_layout import UILayout
from command_handler import CommandHandler


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
                
                # Handle keyboard input
                self._handle_input()
                
                # Process messages from WebSocket
                self._process_messages()
                
                # Periodic UI update
                if current_time - last_update >= UPDATE_INTERVAL:
                    self._update_ui()
                    last_update = current_time
                    
                # Small sleep to avoid CPU spinning
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
            
    def _handle_input(self):
        """Handle keyboard input"""
        try:
            key = self.stdscr.getch()
            
            if key == -1:  # No input
                return
                
            # Quit shortcuts (ESC or CTRL-D)
            if key == 27 or key == 4:  # ESC or CTRL-D
                self.running = False
                return
                
            # Help shortcut
            elif key == ord('?'):
                self._show_help()
                return
                
            # Command input handling
            if key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                # Submit command
                command = self.cmd_handler.submit_command()
                if command:
                    self._send_command(command)
                    
            elif key == ord('\t'):  # Tab - auto-complete
                self._handle_tab_complete()
                
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                self.cmd_handler.delete_char()
                
            elif key == curses.KEY_DC:  # Delete key
                self.cmd_handler.delete_char_forward()
                
            elif key == curses.KEY_LEFT:
                self.cmd_handler.move_cursor(-1)
                
            elif key == curses.KEY_RIGHT:
                self.cmd_handler.move_cursor(1)
                
            elif key == curses.KEY_HOME:
                self.cmd_handler.move_cursor_home()
                
            elif key == curses.KEY_END:
                self.cmd_handler.move_cursor_end()
                
            elif key == curses.KEY_UP:
                self.cmd_handler.history_up()
                
            elif key == curses.KEY_DOWN:
                self.cmd_handler.history_down()
                
            elif key == curses.KEY_RESIZE:
                self.ui.resize()
                
            elif 32 <= key <= 126:  # Printable characters
                self.cmd_handler.add_char(chr(key))
                    
        except curses.error:
            pass
            
    def _send_command(self, command: str):
        """Send G-code command to printer"""
        self.ui.add_terminal_line(f"> {command}", is_command=True)
        
        if self.client:
            success = self.client.send_gcode(command)
            if not success:
                self.ui.add_terminal_line("Failed to send command", is_error=True)
        else:
            self.ui.add_terminal_line("Not connected", is_error=True)
            
    def _show_help(self):
        """Display help with available macros and common commands"""
        self.ui.add_terminal_line("=" * 50, is_command=False)
        self.ui.add_terminal_line("HELP - Available Commands", is_command=False)
        self.ui.add_terminal_line("=" * 50, is_command=False)
        
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
        """Handle tab completion for G-code commands and macros"""
        current_text, cursor_pos = self.cmd_handler.get_display_text()
        
        if not current_text:
            return
            
        # Get word at cursor
        word_start = current_text.rfind(' ', 0, cursor_pos) + 1
        word = current_text[word_start:cursor_pos].upper()
        
        if not word:
            return
            
        # Build list of possible completions
        completions = []
        
        # Common G-code commands
        common_commands = [
            "G28", "G28 X", "G28 Y", "G28 Z", "G28 X Y",
            "G0", "G1", "G90", "G91",
            "M104", "M109", "M140", "M190",
            "M106", "M107", "M114", "M115", "M105",
            "M84", "M112"
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
                
            elif msg_type == "gcode_response":
                # Display G-code response
                response = message.get("response", "")
                if response.strip():
                    # Apply filters
                    if FILTER_GCODE_COMMENTS and response.strip().startswith("//"):
                        continue  # Skip G-code comments
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

