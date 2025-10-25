# Moonraker TUI - Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Connect to Your Printer

```bash
# Using default configuration (edit config.py first)
python main.py

# Or specify printer address directly
python main.py --host 192.168.1.100 --port 7125

# Using hostname (if configured on your network)
python main.py --host mainsailos.local
```

## Interface Overview

The TUI is divided into three main sections:

### Status Panel (Top)
Displays real-time printer information:
- **State**: Current printer state (Idle, Printing, Paused, etc.)
- **File**: Currently printing file name
- **Progress**: Visual progress bar with percentage and time
- **Temperatures**: Bed and nozzle temps (current/target)
- **Position**: Current X, Y, Z coordinates
- **Speed/Flow**: Speed and extrusion multipliers
- **Filament**: Total filament used in current print

### Terminal Panel (Middle)
Scrollable command history:
- Commands you send (shown in cyan with `>` prefix)
- Responses from the printer (shown in white)
- Error messages (shown in red)
- System notifications

### Input Panel (Bottom)
Command input area:
- Type G-code commands here
- Command history available with ↑/↓ arrows
- Keyboard shortcuts displayed at bottom

## Common Tasks

### Homing the Printer

```gcode
G28        # Home all axes
G28 X Y    # Home X and Y only
G28 Z      # Home Z only
```

### Setting Temperatures

```gcode
M104 S200  # Set hotend to 200°C
M140 S60   # Set bed to 60°C
M109 S200  # Set hotend to 200°C and wait
M190 S60   # Set bed to 60°C and wait
```

### Moving the Toolhead

```gcode
G0 X100 Y100 Z10      # Rapid move to position
G1 X150 Y150 F3000    # Linear move at 3000mm/min
```

### Fan Control

```gcode
M106 S255  # Fan on (full speed)
M106 S128  # Fan at 50% speed
M107       # Fan off
```

### Checking Status

```gcode
M114  # Get current position
M115  # Get firmware info
M105  # Get temperatures
```

### Emergency Stop

```gcode
M112  # Emergency stop (use with caution!)
```

## Keyboard Shortcuts

### Always Available
- `q` - Quit application
- `Tab` - Switch between terminal scrolling and input modes
- `p` - Pause print
- `r` - Resume print
- `c` - Cancel print (use carefully!)

### Input Mode (Default)
- `Enter` - Send command
- `↑` - Previous command in history
- `↓` - Next command in history
- `←/→` - Move cursor left/right
- `Home` - Jump to start of line
- `End` - Jump to end of line
- `Backspace` - Delete character before cursor
- `Delete` - Delete character at cursor

### Terminal Scroll Mode (Press Tab to activate)
- `↑` - Scroll up one line
- `↓` - Scroll down one line
- `Page Up` - Scroll up one page
- `Page Down` - Scroll down one page

## Tips and Tricks

### 1. Command History
The TUI remembers all commands you've sent. Use ↑/↓ arrows to navigate through previous commands. This is especially useful for:
- Re-running temperature commands
- Repeating movement commands
- Debugging with repeated queries

### 2. Monitoring During Print
While a print is running, the status panel updates automatically:
- Real-time temperature tracking (colors indicate status):
  - **Green**: Temperature is at target (±2°C)
  - **Yellow**: Temperature is warming up (±10°C)
  - **Red**: Temperature is far from target
- Progress bar shows current completion and time estimates
- Position updates show current toolhead location

### 3. Pausing and Resuming
- Press `p` to pause a print (executes pause macro if configured)
- Press `r` to resume
- Pausing is useful for:
  - Changing filament mid-print
  - Inspecting print quality
  - Adjusting settings

### 4. Terminal Scrolling
- By default, terminal auto-scrolls to show newest messages
- Press Tab to enter scroll mode if you need to review history
- Scroll indicator appears when viewing older messages
- Press Tab again to return to input mode

### 5. Pre-heating Workflow
```gcode
M104 S200  # Start heating nozzle
M140 S60   # Start heating bed
G28        # While heating, home axes
# Wait for temps to stabilize, then start print
```

### 6. Safe Shutdown Sequence
```gcode
M104 S0    # Turn off hotend
M140 S0    # Turn off bed
M107       # Turn off fan
G28 X Y    # Home X and Y (optional)
M84        # Disable steppers
```

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Moonraker"

**Solutions**:
1. Verify printer IP: `ping <printer-ip>`
2. Check Moonraker is running: visit `http://<printer-ip>:7125` in browser
3. Verify port number (default is 7125)
4. Check firewall settings

### Display Issues

**Problem**: Terminal looks corrupted or characters are wrong

**Solutions**:
1. Ensure terminal supports Unicode
2. Try resizing terminal window
3. Check terminal color support: `echo $TERM`
4. Try different terminal emulator

### Commands Not Working

**Problem**: Commands sent but no response

**Solutions**:
1. Check if printer is in error state (restart Klipper if needed)
2. Verify WebSocket connection is active (look for disconnect message)
3. Try sending simple command like `M115`
4. Check Moonraker logs on printer

### WebSocket Disconnects

**Problem**: Frequent disconnections

**Solutions**:
1. Check network stability
2. Verify no firewall is blocking WebSocket connections
3. Restart Moonraker service on printer
4. Check printer system resources (CPU/memory)

## Advanced Usage

### Custom Configuration

Edit `config.py` to customize:

```python
# Your printer's address
PRINTER_HOST = "192.168.1.100"
PRINTER_PORT = 7125

# UI refresh rate (seconds)
UPDATE_INTERVAL = 0.1  # 100ms (responsive)

# Terminal history size
TERMINAL_HISTORY_SIZE = 1000  # lines
```

### Running Multiple Instances

You can run multiple instances to monitor different printers:

```bash
# Terminal 1 - Printer A
python main.py --host 192.168.1.100

# Terminal 2 - Printer B  
python main.py --host 192.168.1.101
```

### Integration with Scripts

Create shell scripts for common tasks:

```bash
#!/bin/bash
# preheat.sh - Preheat printer for PLA
python main.py --host $1 <<EOF
M104 S200
M140 S60
EOF
```

## Safety Notes

⚠️ **Important Safety Information**:

1. **Never leave printer unattended** while heating or printing
2. **Be careful with Cancel command** - it will stop the print immediately
3. **Emergency stop (M112)** requires printer restart
4. **Temperature commands** - always verify values before sending
5. **Movement commands** - ensure printer is homed first
6. **Network connection** - lost connection during print is handled by printer, but monitor status

## Getting Help

If you encounter issues:

1. Check printer logs on Moonraker
2. Review Klipper documentation
3. Verify G-code commands in Klipper documentation
4. Check network connectivity and firewall rules
5. Ensure all dependencies are installed correctly

## Additional Resources

- [Klipper Documentation](https://www.klipper3d.org/)
- [Moonraker Documentation](https://moonraker.readthedocs.io/)
- [G-code Reference](https://www.klipper3d.org/G-Codes.html)

