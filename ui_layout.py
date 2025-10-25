"""UI layout and rendering using curses"""

import curses
from collections import deque
from typing import Dict, Any, Optional
from config import STATUS_HEIGHT, INPUT_HEIGHT, TERMINAL_HISTORY_SIZE


class UILayout:
    """Manages curses windows and rendering"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.status_win = None
        self.terminal_win = None
        self.input_win = None
        
        # Terminal history
        self.terminal_lines = deque(maxlen=TERMINAL_HISTORY_SIZE)
        self.terminal_scroll_offset = 0
        
        # Screen dimensions
        self.height = 0
        self.width = 0
        
        # Current printer data
        self.printer_data: Dict[str, Any] = {}
        self.connected = False
        
        # Color pairs
        self.COLOR_COMMAND = 1
        self.COLOR_RESPONSE = 2
        self.COLOR_ERROR = 3
        self.COLOR_OK = 4
        self.COLOR_WARNING = 5
        self.COLOR_HEADER = 6
        
        self._init_colors()
        self.create_windows()
        
    def _init_colors(self):
        """Initialize color pairs"""
        curses.start_color()
        curses.use_default_colors()
        
        # Define color pairs
        curses.init_pair(self.COLOR_COMMAND, curses.COLOR_CYAN, -1)
        curses.init_pair(self.COLOR_RESPONSE, curses.COLOR_WHITE, -1)
        curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)
        curses.init_pair(self.COLOR_OK, curses.COLOR_GREEN, -1)
        curses.init_pair(self.COLOR_WARNING, curses.COLOR_YELLOW, -1)
        curses.init_pair(self.COLOR_HEADER, curses.COLOR_WHITE, -1)
        
    def create_windows(self):
        """Create the three main windows"""
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Status window (top)
        self.status_win = curses.newwin(STATUS_HEIGHT, self.width, 0, 0)
        
        # Terminal window (middle - scrollable)
        terminal_height = self.height - STATUS_HEIGHT - INPUT_HEIGHT
        self.terminal_win = curses.newwin(
            terminal_height, self.width, STATUS_HEIGHT, 0
        )
        self.terminal_win.scrollok(True)
        
        # Input window (bottom)
        self.input_win = curses.newwin(
            INPUT_HEIGHT, self.width, self.height - INPUT_HEIGHT, 0
        )
        
    def update_status(self, data: Dict[str, Any]):
        """Update status window with printer data"""
        self.printer_data = data
        
    def set_connected(self, connected: bool):
        """Set connection status"""
        self.connected = connected
        
    def render_status(self):
        """Render the status window"""
        self.status_win.clear()
        self.status_win.box()
        
        try:
            # Connection status
            if self.connected:
                self.status_win.addstr(0, 2, " STATUS ", curses.A_BOLD)
            else:
                self.status_win.addstr(
                    0, 2, " DISCONNECTED ", 
                    curses.color_pair(self.COLOR_ERROR) | curses.A_BOLD
                )
                self.status_win.refresh()
                return
            
            # Print state
            print_stats = self.printer_data.get("print_stats", {})
            state = print_stats.get("state", "unknown")
            
            state_color = self.COLOR_RESPONSE
            if state == "printing":
                state_color = self.COLOR_OK
            elif state == "paused":
                state_color = self.COLOR_WARNING
            elif state == "error":
                state_color = self.COLOR_ERROR
                
            self.status_win.addstr(1, 2, "State: ")
            self.status_win.addstr(
                1, 9, state.capitalize(), 
                curses.color_pair(state_color) | curses.A_BOLD
            )
            
            # Filename
            filename = print_stats.get("filename", "N/A")
            if len(filename) > self.width - 10:
                filename = "..." + filename[-(self.width - 13):]
            self.status_win.addstr(2, 2, f"File: {filename}")
            
            # Progress bar
            display_status = self.printer_data.get("display_status", {})
            progress = display_status.get("progress", 0.0)
            progress_pct = int(progress * 100)
            
            total_duration = print_stats.get("total_duration", 0)
            print_duration = print_stats.get("print_duration", 0)
            
            # Format time
            def format_time(seconds):
                if seconds is None or seconds == 0:
                    return "--:--"
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                if hours > 0:
                    return f"{hours}h{minutes}m"
                return f"{minutes}m"
            
            time_str = f"({format_time(print_duration)}/{format_time(total_duration)})"
            
            # Progress bar
            bar_width = 20
            filled = int(bar_width * progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            self.status_win.addstr(3, 2, f"Progress: [{bar}] {progress_pct}% {time_str}")
            
            # Temperatures
            heater_bed = self.printer_data.get("heater_bed", {})
            bed_temp = heater_bed.get("temperature", 0)
            bed_target = heater_bed.get("target", 0)
            
            extruder = self.printer_data.get("extruder", {})
            nozzle_temp = extruder.get("temperature", 0)
            nozzle_target = extruder.get("target", 0)
            
            self.status_win.addstr(4, 2, "Bed: ")
            
            # Bed color
            bed_color = self._get_temp_color(bed_temp, bed_target)
            self.status_win.addstr(
                4, 7, f"{bed_temp:.1f}°C", 
                curses.color_pair(bed_color)
            )
            self.status_win.addstr(4, 17, f"/{bed_target:.0f}°C")
            
            self.status_win.addstr(4, 27, "Nozzle: ")
            
            # Nozzle color
            nozzle_color = self._get_temp_color(nozzle_temp, nozzle_target)
            self.status_win.addstr(
                4, 35, f"{nozzle_temp:.1f}°C",
                curses.color_pair(nozzle_color)
            )
            self.status_win.addstr(4, 45, f"/{nozzle_target:.0f}°C")
            
            # Position
            toolhead = self.printer_data.get("toolhead", {})
            position = toolhead.get("position", [0, 0, 0, 0])
            
            if len(position) >= 3:
                x, y, z = position[0], position[1], position[2]
                self.status_win.addstr(
                    5, 2, f"Position: X:{x:.2f} Y:{y:.2f} Z:{z:.2f}"
                )
            
            # Speed and flow
            gcode_move = self.printer_data.get("gcode_move", {})
            speed_factor = gcode_move.get("speed_factor", 1.0) * 100
            extrude_factor = gcode_move.get("extrude_factor", 1.0) * 100
            
            self.status_win.addstr(
                6, 2, f"Speed: {speed_factor:.0f}%  Flow: {extrude_factor:.0f}%"
            )
            
            # Filament used
            filament_used = print_stats.get("filament_used", 0)
            if filament_used > 0:
                filament_m = filament_used / 1000  # Convert mm to m
                self.status_win.addstr(7, 2, f"Filament: {filament_m:.2f}m")
            
        except curses.error:
            # Window too small or other curses error
            pass
            
        self.status_win.refresh()
        
    def _get_temp_color(self, current: float, target: float) -> int:
        """Get color for temperature display"""
        if target == 0:
            return self.COLOR_RESPONSE
        
        diff = abs(current - target)
        if diff < 2:
            return self.COLOR_OK
        elif diff < 10:
            return self.COLOR_WARNING
        else:
            return self.COLOR_ERROR
            
    def add_terminal_line(self, text: str, is_command: bool = False, is_error: bool = False):
        """Add a line to terminal history"""
        color = self.COLOR_COMMAND if is_command else self.COLOR_RESPONSE
        if is_error:
            color = self.COLOR_ERROR
            
        self.terminal_lines.append((text, color))
        
        # Auto-scroll to bottom when new line is added
        self.terminal_scroll_offset = 0
        
    def scroll_terminal(self, direction: int):
        """Scroll terminal up (1) or down (-1)"""
        terminal_height = self.height - STATUS_HEIGHT - INPUT_HEIGHT - 2  # Minus borders
        max_scroll = max(0, len(self.terminal_lines) - terminal_height)
        
        self.terminal_scroll_offset -= direction
        self.terminal_scroll_offset = max(0, min(self.terminal_scroll_offset, max_scroll))
        
    def render_terminal(self):
        """Render terminal window with scrolling"""
        self.terminal_win.clear()
        self.terminal_win.box()
        
        try:
            terminal_height = self.height - STATUS_HEIGHT - INPUT_HEIGHT - 2
            
            # Calculate visible range
            total_lines = len(self.terminal_lines)
            start_idx = max(0, total_lines - terminal_height - self.terminal_scroll_offset)
            end_idx = total_lines - self.terminal_scroll_offset
            
            # Render visible lines
            y = 1
            for i in range(start_idx, end_idx):
                if i >= 0 and i < len(self.terminal_lines):
                    line, color = self.terminal_lines[i]
                    
                    # Truncate line if too long
                    max_width = self.width - 3
                    if len(line) > max_width:
                        line = line[:max_width - 3] + "..."
                        
                    self.terminal_win.addstr(
                        y, 1, line,
                        curses.color_pair(color)
                    )
                    y += 1
                    
            # Show scroll indicator if scrolled
            if self.terminal_scroll_offset > 0:
                indicator = f" ↑ Scrolled ({self.terminal_scroll_offset}) "
                self.terminal_win.addstr(
                    0, self.width // 2 - len(indicator) // 2, 
                    indicator,
                    curses.color_pair(self.COLOR_WARNING)
                )
                
        except curses.error:
            pass
            
        self.terminal_win.refresh()
        
    def render_input(self, command_text: str, cursor_pos: int):
        """Render input window"""
        self.input_win.clear()
        
        try:
            # Draw separator line at top
            self.input_win.hline(0, 0, curses.ACS_HLINE, self.width)
            
            # Command prompt
            prompt = "Command: "
            self.input_win.addstr(1, 0, prompt)
            
            # Command text
            max_cmd_width = self.width - len(prompt) - 1
            visible_text = command_text
            
            # Handle text longer than window
            if len(command_text) > max_cmd_width:
                # Scroll to show cursor
                if cursor_pos > max_cmd_width - 5:
                    start = cursor_pos - max_cmd_width + 5
                    visible_text = command_text[start:]
                    cursor_pos = cursor_pos - start
                else:
                    visible_text = command_text[:max_cmd_width]
                    
            self.input_win.addstr(1, len(prompt), visible_text)
            
            # Help text (updated shortcuts)
            help_text = "[ESC/^D]quit [?]help [Tab]complete"
            if len(help_text) < self.width:
                self.input_win.addstr(2, 0, help_text, curses.A_DIM)
            
            # Position cursor
            curses.curs_set(1)
            self.input_win.move(1, len(prompt) + cursor_pos)
            
        except curses.error:
            pass
            
        self.input_win.refresh()
        
    def render(self, command_text: str = "", cursor_pos: int = 0):
        """Render all windows"""
        self.render_status()
        self.render_terminal()
        self.render_input(command_text, cursor_pos)
        
    def resize(self):
        """Handle terminal resize"""
        self.height, self.width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.create_windows()
        
    def cleanup(self):
        """Cleanup curses"""
        curses.curs_set(1)
        curses.endwin()

