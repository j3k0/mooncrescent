# Changelog

All notable changes to Mooncrescent will be documented in this file.

## [Unreleased]

### Added
- **File Management System**
  - `ls` command to list available gcode files (sorted oldest to newest)
  - `ls -l` for detailed listing with estimated time and filament usage
  - `print <filename>` to start printing a specific file
  - `reprint` to restart the last printed file
  - Tab completion for filenames in `print` and `info` commands
  
- **File Metadata Viewer**
  - `info <filename>` command to display detailed file information
  - Shows file size, estimated print time, filament usage (meters and grams)
  - Displays layer heights, temperatures, and slicer information
  - Uses Moonraker's metadata API for accurate estimates

- **File ID System**
  - Quick file references with #N syntax (#0 = newest, #1 = second newest, etc.)
  - File IDs displayed in all `ls` outputs
  - Use IDs in commands: `print #0`, `info #1`
  - Automatic ID mapping updated when files are listed

- **Glob Pattern Filtering**
  - Filter files with shell-style wildcards: `ls *TPU*`, `ls *calibration*`
  - Works with `-l` flag in any order: `ls -l *pattern*` or `ls *pattern* -l`
  - Case-insensitive matching using fnmatch

- **Print History Tracking**
  - `history` command to view last 20 completed/cancelled prints
  - Automatic logging to `~/.mooncrescent_print_history`
  - Tracks filename, duration, filament used, and completion status
  - Visual status markers (✓ completed, ✗ cancelled)
  - State detection for print start, completion, and cancellation

- **Z-Offset Baby Stepping**
  - `z +0.05` to raise nozzle by 0.05mm
  - `z -0.02` to lower nozzle by 0.02mm
  - `z save` to save current offset to Klipper config
  - Uses `SET_GCODE_OFFSET Z_ADJUST` with immediate movement
  - Perfect for first-layer tuning during prints

- **Additional Commands**
  - `FIRMWARE_RESTART` added to known commands for post-emergency-stop recovery

### Changed
- Project renamed from "Moonraker TUI" to "Mooncrescent"
- History file renamed from `~/.moonraker_tui_history` to `~/.mooncrescent_history`
- Main executable renamed from `main.py` to `mooncrescent.py`
- Enhanced help menu with organized sections and examples
- Tab completion now includes special commands (ls, info, history, z)
- File list cache shared between commands for better performance

### Technical
- Added `get_file_metadata()` method to MoonrakerClient
- Added `get_files_list()` method with sorting by modification time
- File ID mapping system with automatic updates
- Glob pattern support using fnmatch module
- State tracking for print lifecycle events
- Configuration option for print history file location

## [0.2.0] - Mooncrescent Release

### Breaking Changes

### Changed
- **BREAKING**: Removed h and q shortcuts that interfered with G-code commands
- **BREAKING**: Changed quit shortcut to ESC or Ctrl-D (safer, no accidental quits)
- **BREAKING**: Changed help shortcut to ? (question mark)
- Removed pause/resume/cancel keyboard shortcuts (p, r, c) - use G-code commands instead for safety
- Removed Tab focus switching - input is always focused, making it behave more like a terminal
- Changed Tab key to trigger auto-completion instead of focus switching
- Updated help text in input panel to reflect new shortcuts

### Added
- History persistence: Commands automatically saved to ~/.moonraker_tui_history
- Auto-load history on startup, auto-save on exit
- History limited to 1000 most recent commands
- [h]elp command to display available macros and common G-code commands
- Tab auto-completion for G-code commands and macros
- API methods to fetch available macros from Moonraker
- API methods to get G-code help from printer
- Comprehensive auto-completion with common prefix matching
- Test suite for new macro and help features

### Fixed
- UI rendering bug where input box border drew over terminal separator line
- Input window now uses clean horizontal line separator
- Increased INPUT_HEIGHT from 2 to 3 lines to accommodate proper layout

## [0.1.0] - Initial Release

### Added
- WebSocket client for real-time status updates
- HTTP client for G-code commands and print control
- Curses-based TUI with three-panel layout (status, terminal, input)
- Status panel showing temperatures, position, progress, speed/flow
- Scrollable terminal with command history
- Command input with cursor control and history
- Color-coded display (commands, responses, errors, status indicators)
- Support for SSH tunnels (localhost forwarding)
- Component and integration test suites
- Comprehensive documentation (README, USAGE, TESTING)
- Configuration system with sensible defaults

### Features
- Real-time temperature monitoring
- Print progress tracking
- Live position updates
- Command history with up/down arrows
- Clean terminal-like interface
- Automatic reconnection on disconnect
- Thread-safe WebSocket communication
- Graceful error handling

