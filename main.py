#!/usr/bin/env python3
"""Moonraker TUI - Terminal User Interface for 3D Printer Control"""

import curses
import argparse
import sys
import time
import locale
from typing import Optional

from config import PRINTER_HOST, PRINTER_PORT, UPDATE_INTERVAL
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
        
        # State
        self.running = True
        self.focused_on_input = True
        
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
            self.ui.add_terminal_line("Moonraker TUI starting...", is_command=False)
            self.ui.add_terminal_line(f"Connecting to {self.host}:{self.port}...", is_command=False)
            self.ui.render()
            
            # Connect to Moonraker
            self.client = MoonrakerClient(self.host, self.port)
            if not self.client.connect():
                self.ui.add_terminal_line("Failed to connect to Moonraker", is_error=True)
                self.ui.add_terminal_line("Press 'q' to quit", is_command=False)
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
                
            # Global shortcuts
            if key == ord('q') or key == ord('Q'):
                self.running = False
                return
                
            elif key == ord('\t'):  # Tab - switch focus
                self.focused_on_input = not self.focused_on_input
                if not self.focused_on_input:
                    curses.curs_set(0)
                else:
                    curses.curs_set(1)
                return
                
            elif key == ord('p') or key == ord('P'):  # Pause
                if self.client:
                    self.client.pause_print()
                    self.ui.add_terminal_line("Pausing print...", is_command=False)
                return
                
            elif key == ord('r') or key == ord('R'):  # Resume
                if self.client:
                    self.client.resume_print()
                    self.ui.add_terminal_line("Resuming print...", is_command=False)
                return
                
            elif key == ord('c') or key == ord('C'):  # Cancel (with confirmation)
                if not self.focused_on_input:
                    # Simple cancel confirmation
                    if self.client:
                        self.client.cancel_print()
                        self.ui.add_terminal_line("Canceling print...", is_command=False)
                return
            
            # Terminal scrolling (when not focused on input)
            if not self.focused_on_input:
                if key == curses.KEY_UP:
                    self.ui.scroll_terminal(1)
                elif key == curses.KEY_DOWN:
                    self.ui.scroll_terminal(-1)
                elif key == curses.KEY_PPAGE:  # Page Up
                    self.ui.scroll_terminal(10)
                elif key == curses.KEY_NPAGE:  # Page Down
                    self.ui.scroll_terminal(-10)
                return
            
            # Command input handling (when focused on input)
            if self.focused_on_input:
                if key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                    # Submit command
                    command = self.cmd_handler.submit_command()
                    if command:
                        self._send_command(command)
                        
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
        if self.client:
            self.client.disconnect()
        if self.ui:
            self.ui.cleanup()


def main():
    """Entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Moonraker TUI - 3D Printer Terminal Interface")
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

