"""Configuration settings for Moonraker TUI"""

# Printer connection settings
PRINTER_HOST = "127.0.0.1"  # or "mainsailos.local"
PRINTER_PORT = 7125

# Connection settings
WEBSOCKET_TIMEOUT = 30
CONNECTION_RETRY_DELAY = 5  # seconds

# UI settings
TERMINAL_HISTORY_SIZE = 1000
UPDATE_INTERVAL = 0.1  # seconds (100ms for responsive UI)

# Status window height
STATUS_HEIGHT = 10

# Input window height
INPUT_HEIGHT = 3

# History file
HISTORY_FILE = "~/.mooncrescent_history"

