# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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

