# Testing Guide

## Overview

The Moonraker TUI project includes two types of tests:

1. **Component Tests** (`test_components.py`) - Unit tests for individual modules
2. **Integration Tests** (`test_integration.py`) - Tests against a real Moonraker instance

## Component Tests

Tests basic functionality without requiring a printer connection:

```bash
python test_components.py
```

Tests include:
- Module imports
- Configuration loading
- CommandHandler (input, history, cursor movement)
- MoonrakerClient initialization

## Integration Tests

Tests against a live Moonraker instance. **Requires a running printer.**

### Basic Usage

```bash
# Test with default config (127.0.0.1:7125)
python test_integration.py

# Test specific host/port
python test_integration.py --host 192.168.1.100 --port 7125

# Test specific command
python test_integration.py --command G28
```

### Available Tests

```bash
# Run all tests
python test_integration.py --test all

# Test connection only
python test_integration.py --test connect

# Test printer info retrieval
python test_integration.py --test info

# Test object queries
python test_integration.py --test objects

# Test G-code command (default: M115)
python test_integration.py --test gcode --command M115

# Test HTTP endpoint directly
python test_integration.py --test http --command M115
```

### Integration Test Checklist

The integration tests verify:

- ✅ WebSocket connection establishes
- ✅ Status updates are received
- ✅ HTTP API endpoints respond
- ✅ Printer info can be retrieved
- ✅ Printer objects can be queried
- ✅ G-code commands can be sent
- ✅ Responses are received via WebSocket

### Testing with Real Commands

**⚠️ Warning**: Some commands will actually control your printer!

```bash
# Safe read-only commands
python test_integration.py --test gcode --command M115  # Firmware info
python test_integration.py --test gcode --command M114  # Current position
python test_integration.py --test gcode --command M105  # Temperatures

# Movement commands (ensure printer is homed and safe!)
python test_integration.py --test gcode --command G28   # Home all axes

# Temperature commands (use appropriate temps for your printer!)
python test_integration.py --test gcode --command "M104 S200"  # Set hotend
```

## Manual Testing with TUI

To manually test the full application:

```bash
# Start the TUI
python main.py --host 127.0.0.1

# Test these features:
# 1. Connection - should connect and show status
# 2. Status display - temperatures, position update in real-time
# 3. Command sending - type M115 and press Enter
# 4. Response display - should see firmware info in terminal
# 5. Command history - press Up arrow to recall M115
# 6. Scrolling - press Tab, then Up/Down to scroll
# 7. Print control - if printing, test p/r/c keys
# 8. Quit - press 'q' to exit cleanly
```

## Known Issues & Limitations

### SSH Tunnels

When using SSH tunnels (e.g., `127.0.0.1` forwarded to remote printer):
- Connection and status work perfectly
- Command sending works but may have increased latency
- Long-running commands (G28) work fine with 120s timeout
- Ensure tunnel is stable for best experience

### Command Timeouts

Some commands take time to execute:
- **G28** (homing): 10-30 seconds depending on printer
- **G29** (bed leveling): 2-10 minutes
- **M109/M190** (heat and wait): 30 seconds - 5 minutes

The timeout is set to 120 seconds. Commands that take longer will timeout on HTTP but still execute. Responses come via WebSocket.

### WebSocket Responses

Not all commands produce `gcode_response` messages:
- Silent commands (like G28) may only update status
- Errors always produce responses
- Query commands (M114, M115) always respond

## Automated Testing Best Practices

### Before Committing

Always run both test suites:

```bash
# Component tests (fast, no printer needed)
python test_components.py

# Integration tests (requires printer)
python test_integration.py --test all --command M115
```

### Continuous Integration

For CI/CD pipelines:

```bash
# Only run component tests (no printer available)
python test_components.py
```

### Adding New Tests

When adding new features:

1. Add component tests for logic/parsing
2. Add integration tests for API interactions
3. Test manually in TUI for UX
4. Document any printer-specific requirements

## Troubleshooting Tests

### "Connection failed"

- Verify Moonraker is running: `curl http://127.0.0.1:7125/server/info`
- Check SSH tunnel (if using): `netstat -an | grep 7125`
- Verify firewall allows port 7125

### "Timeout" errors

- Some commands take time (this is normal)
- Verify printer is not in error state
- Check if command actually executed (may timeout but still work)

### "No response received"

- Some commands don't produce responses (normal)
- Check printer state in Mainsail/Fluidd web interface
- Verify WebSocket connection is active

## Test Coverage

Current test coverage:

- ✅ Module imports and initialization
- ✅ Configuration management
- ✅ Command input handling
- ✅ Command history navigation
- ✅ WebSocket connection
- ✅ HTTP API calls
- ✅ Status updates
- ✅ G-code command execution
- ⬜ UI rendering (requires mock curses)
- ⬜ Keyboard input handling (requires mock curses)
- ⬜ Error recovery scenarios
- ⬜ Network failure handling

## Future Testing Improvements

1. Mock curses for UI testing
2. Mock Moonraker for offline testing
3. Error injection tests
4. Performance/stress tests
5. Memory leak tests for long-running sessions

