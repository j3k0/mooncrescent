# Mooncrescent

A Python curses-based terminal interface for monitoring and controlling Moonraker/Klipper 3D printers via WebSocket and HTTP APIs.

## Features

- **Real-time Monitoring**: Live temperature, position, and print progress updates
- **Interactive Terminal**: Send G-code commands directly to your printer
- **Tab Auto-completion**: Complete G-code commands and macros
- **Persistent History**: Command history saved between sessions
- **Help System**: Press `?` to see available macros and commands

## Requirements

- Python 3.8 or higher
- Moonraker-enabled 3D printer (Klipper firmware)
- Network connection to your printer

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd mooncrescent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py --host 192.168.1.100 --port 7125
```

### Command-line Options

- `--host`: Moonraker host address (default: 192.168.1.100)
- `--port`: Moonraker port (default: 7125)

### Examples

```bash
# Connect to printer at default IP
python mooncrescent.py

# Connect to printer with custom IP
python mooncrescent.py --host 192.168.1.50

# Connect to printer with hostname
python mooncrescent.py --host mainsailos.local
```

## Keyboard Controls

### Command Input
- `Enter` - Send G-code command
- `Tab` - Auto-complete command
- `↑/↓` - Navigate command history (persisted across sessions)
- `←/→` - Move cursor in command line
- `Home/End` - Jump to start/end of command
- `Backspace` - Delete character before cursor
- `Delete` - Delete character at cursor

### Global Shortcuts
- `?` - Show help (macros and common commands)
- `ESC` or `Ctrl-D` - Quit the application

## UI Layout

```
┌─────────────────────────────────────────────────┐
│ STATUS (top section)                            │
│ State: Printing | Idle | Paused                 │
│ File: filename.gcode                            │
│ Progress: [██████████░░░░░░░░░] 45% (30m/1h5m) │
│ Bed: 60°C/60°C  Nozzle: 210°C/210°C           │
│ Position: X:100.0 Y:100.0 Z:5.50               │
│ Speed: 100% Flow: 100%                          │
├─────────────────────────────────────────────────┤
│ TERMINAL (scrollable middle section)            │
│ > G28                                           │
│ ok                                              │
│ > M104 S210                                     │
│ ok                                              │
│ ...                                             │
├─────────────────────────────────────────────────┤
│ INPUT (bottom section)                          │
│ Command: G28_                                   │
│ [q]uit [p]ause [r]esume [c]ancel [Tab]focus   │
└─────────────────────────────────────────────────┘
```

## Common G-code Commands

- `G28` - Home all axes
- `G28 X` - Home X axis only
- `G28 Y` - Home Y axis only
- `G28 Z` - Home Z axis only
- `M104 S200` - Set hotend temperature to 200°C
- `M140 S60` - Set bed temperature to 60°C
- `M109 S200` - Set hotend temperature and wait
- `M190 S60` - Set bed temperature and wait
- `M106 S255` - Turn fan on (full speed)
- `M107` - Turn fan off
- `M114` - Get current position
- `G0 X100 Y100` - Move to position (rapid)
- `G1 X100 Y100 F3000` - Move to position (linear)

## Configuration

Edit `config.py` to change default settings:

```python
PRINTER_HOST = "192.168.1.100"  # Default printer IP
PRINTER_PORT = 7125              # Default Moonraker port
TERMINAL_HISTORY_SIZE = 1000     # Max terminal lines
UPDATE_INTERVAL = 0.1            # UI refresh rate (seconds)
```

## Troubleshooting

### Connection Failed
- Verify printer IP address and port
- Ensure Moonraker is running on the printer
- Check network connectivity: `ping <printer-ip>`
- Verify firewall settings allow connection to port 7125

### Terminal Display Issues
- Ensure your terminal supports Unicode characters
- Try resizing terminal window if display looks corrupted
- Some terminals may not support all color features

### WebSocket Disconnects
- The client will automatically attempt to reconnect
- Check for network stability issues
- Verify Moonraker is running properly

## Architecture

The application consists of five main components:

1. **main.py** - Entry point, curses setup, and main event loop
2. **moonraker_client.py** - WebSocket/HTTP client for Moonraker API
3. **ui_layout.py** - UI rendering and window management
4. **command_handler.py** - Command input and history management
5. **config.py** - Configuration settings

### Data Flow

1. WebSocket connection receives real-time printer updates
2. Updates are queued in thread-safe message queue
3. Main loop processes messages and updates UI
4. User input is handled and sent via HTTP API
5. Responses are displayed in terminal window

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built for Klipper/Moonraker 3D printer firmware
- Uses the Moonraker API for communication
- Inspired by the need for a lightweight terminal-based printer interface

