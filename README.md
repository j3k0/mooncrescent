# Mooncrescent

Terminal interface for monitoring and controlling Moonraker/Klipper 3D printers.

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

### From PyPI (Recommended)

```bash
pip install mooncrescent
```

### From Source

1. Clone or download this repository:
```bash
git clone https://github.com/j3k0/mooncrescent.git
cd mooncrescent
```

2. Install in development mode:
```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# If installed from PyPI
mooncrescent

# If running from source
python -m mooncrescent
```

### Command-line Options

- `--host`: Moonraker host address (default: 127.0.0.1)
- `--port`: Moonraker port (default: 7125)

### Examples

```bash
# Connect to printer at default IP
mooncrescent

# Connect to printer with custom IP
mooncrescent --host 192.168.1.50

# Connect to printer with hostname
mooncrescent --host mainsailos.local
```

## Keyboard Controls

### Command Input
- `Enter` - Send G-code command
- `Tab` - Auto-complete command
- `↑/↓` - Navigate command history (persisted across sessions)
- The usual to move the cursor and delete stuff: `←/→`, `Home/End`, `Backspace`, `Delete`...

### Terminal Scrolling
- `Page Up` - Scroll terminal output up
- `Page Down` - Scroll terminal output down

### Global Shortcuts
- `?` - Show help (macros and common commands)
- `ESC` or `Ctrl-D` - Quit the application

## Configuration

Edit `config.py` to change default settings:

```python
PRINTER_HOST = "127.0.0.1"       # Default printer IP
PRINTER_PORT = 7125              # Default Moonraker port
TERMINAL_HISTORY_SIZE = 1000     # Max terminal lines
UPDATE_INTERVAL = 0.1            # UI refresh rate for status (seconds)
                                 # Try 2.0 for slow computers (input is always instant)

# Terminal filtering
FILTER_PATTERNS = [              # Patterns to filter out
    "// pressure_advance:",      # Orca Slicer adaptive PA spam
]
FILTER_OK_RESPONSES = False      # Filter standalone "ok" messages
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

