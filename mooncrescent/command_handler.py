"""Command input handling and history management"""

import os


class CommandHandler:
    """Manages command input, cursor position, and command history"""
    
    def __init__(self):
        self.command_buffer = ""
        self.cursor_position = 0
        self.command_history = []
        self.history_index = -1  # -1 means not navigating history
        self.temp_buffer = ""  # Store current input when navigating history
        
    def add_char(self, char: str):
        """Add a character at cursor position"""
        if len(char) == 1:
            self.command_buffer = (
                self.command_buffer[:self.cursor_position] + 
                char + 
                self.command_buffer[self.cursor_position:]
            )
            self.cursor_position += 1
            
    def delete_char(self):
        """Delete character before cursor (backspace)"""
        if self.cursor_position > 0:
            self.command_buffer = (
                self.command_buffer[:self.cursor_position - 1] + 
                self.command_buffer[self.cursor_position:]
            )
            self.cursor_position -= 1
            
    def delete_char_forward(self):
        """Delete character at cursor (delete key)"""
        if self.cursor_position < len(self.command_buffer):
            self.command_buffer = (
                self.command_buffer[:self.cursor_position] + 
                self.command_buffer[self.cursor_position + 1:]
            )
            
    def move_cursor(self, direction: int):
        """Move cursor left (-1) or right (1)"""
        new_pos = self.cursor_position + direction
        if 0 <= new_pos <= len(self.command_buffer):
            self.cursor_position = new_pos
            
    def move_cursor_home(self):
        """Move cursor to start of line"""
        self.cursor_position = 0
        
    def move_cursor_end(self):
        """Move cursor to end of line"""
        self.cursor_position = len(self.command_buffer)
        
    def submit_command(self) -> str:
        """Submit command, add to history, clear buffer"""
        command = self.command_buffer.strip()
        if command:
            # Add to history (avoid duplicates of last command)
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)
        
        # Clear buffer and reset state
        self.command_buffer = ""
        self.cursor_position = 0
        self.history_index = -1
        self.temp_buffer = ""
        
        return command
        
    def history_up(self):
        """Navigate to previous command in history"""
        if not self.command_history:
            return
            
        # First time navigating history - save current buffer
        if self.history_index == -1:
            self.temp_buffer = self.command_buffer
            self.history_index = len(self.command_history)
            
        if self.history_index > 0:
            self.history_index -= 1
            self.command_buffer = self.command_history[self.history_index]
            self.cursor_position = len(self.command_buffer)
            
    def history_down(self):
        """Navigate to next command in history"""
        if self.history_index == -1:
            return
            
        self.history_index += 1
        
        if self.history_index >= len(self.command_history):
            # Restore temporary buffer
            self.command_buffer = self.temp_buffer
            self.history_index = -1
        else:
            self.command_buffer = self.command_history[self.history_index]
            
        self.cursor_position = len(self.command_buffer)
        
    def get_display_text(self) -> tuple[str, int]:
        """Get current command text and cursor position for display"""
        return (self.command_buffer, self.cursor_position)
        
    def load_history(self, history_file: str):
        """Load command history from file"""
        try:
            expanded_path = os.path.expanduser(history_file)
            if os.path.exists(expanded_path):
                with open(expanded_path, 'r') as f:
                    self.command_history = [line.strip() for line in f if line.strip()]
        except Exception:
            # Silently fail if we can't load history
            pass
    
    def save_history(self, history_file: str):
        """Save command history to file"""
        try:
            expanded_path = os.path.expanduser(history_file)
            # Create directory if it doesn't exist
            directory = os.path.dirname(expanded_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Write history (limit to last 1000 commands)
            with open(expanded_path, 'w') as f:
                for cmd in self.command_history[-1000:]:
                    f.write(cmd + '\n')
        except Exception:
            # Silently fail if we can't save history
            pass
        
    def clear(self):
        """Clear command buffer"""
        self.command_buffer = ""
        self.cursor_position = 0
        self.history_index = -1


# Common GCode commands for reference
COMMON_GCODES = {
    # File management
    "ls": "List available gcode files",
    "print": "Start printing a file (usage: print <filename>)",
    "reprint": "Reprint the last file",
    "info": "Show detailed file information",
    "history": "Show print history",
    "z": "Adjust Z offset (z +0.05, z -0.02, z save)",
    
    # Homing
    "G28": "Home all axes",
    "G28 X": "Home X axis",
    "G28 Y": "Home Y axis", 
    "G28 Z": "Home Z axis",
    
    # Temperature control
    "M104 S200": "Set hotend temp to 200°C",
    "M140 S60": "Set bed temp to 60°C",
    "M109 S200": "Set hotend temp and wait",
    "M190 S60": "Set bed temp and wait",
    
    # Fan control
    "M106 S255": "Fan on full speed",
    "M107": "Fan off",
    
    # Movement
    "G0": "Rapid move",
    "G1": "Linear move",
    
    # Status and info
    "M114": "Get current position",
    "M115": "Get firmware info",
    
    # System commands
    "FIRMWARE_RESTART": "Restart firmware (after emergency stop)",
}

