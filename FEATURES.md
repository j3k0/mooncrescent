# Feature Guide

## Overview

Mooncrescent is designed to behave like a terminal with helpful features while avoiding dangerous accidental commands.

## Key Design Principles

1. **Safety First**: No keyboard shortcuts that could accidentally cancel/pause prints
2. **Terminal-Like**: Always focused on input, behaves like a real terminal
3. **Helpful**: Auto-completion and help are readily available
4. **Simple**: Clean interface without mode switching

## Features

### 1. Help Command

Press `h` or type it anytime to see available commands and macros.

```
> h
```

Displays:
- Common G-code commands with descriptions
- All available macros from your printer configuration
- Keyboard shortcuts
- Usage tips

The help fetches live data from your printer, so it always shows your current macros.

### 2. Tab Auto-Completion

Press `Tab` to complete G-code commands and macros.

**Examples:**

```
> G<Tab>
Completions: G0, G1, G28, G28 X, G28 X Y, G28 Y, G28 Z, G90, G91

> G2<Tab>
Auto-completes to: G28

> M1<Tab>
Completions: M104, M105, M106, M107, M109, M112, M114, M115
```

**Smart Completion:**
- One match: Auto-completes immediately
- Multiple matches: Shows all options and completes common prefix
- Works with macros too!

**Completion Sources:**
- Common G-code commands (G28, M104, M140, etc.)
- Your printer's custom macros (fetched live)

### 3. Command History

Navigate previous commands with arrow keys.

- `↑` (Up Arrow): Previous command
- `↓` (Down Arrow): Next command

History persists during your session and avoids duplicate consecutive commands.

### 4. Real-Time Status Display

The status panel updates automatically:

```
┌─────────────────────────────────────────────────┐
│ STATUS                                          │
│ State: Printing                                 │
│ File: test_print.gcode                          │
│ Progress: [██████████░░░░░░░░░] 45% (30m/1h5m) │
│ Bed: 60.0°C/60°C  Nozzle: 210.0°C/210°C       │
│ Position: X:100.00 Y:100.00 Z:5.50             │
│ Speed: 100% Flow: 100%                          │
└─────────────────────────────────────────────────┘
```

**Color Coding:**
- **Green**: Temperature at target (±2°C)
- **Yellow**: Temperature warming up (±10°C)
- **Red**: Temperature far from target
- **Cyan**: Your commands
- **White**: Printer responses
- **Red**: Errors

### 5. Terminal Output

All commands and responses are logged in the terminal:

```
> M115
// FIRMWARE_NAME:Klipper FIRMWARE_VERSION:v0.13.0
> M104 S200
ok
> G28
// Homing...
```

### 6. Clean UI

```
┌─────────────────────────────────────────────────┐
│ STATUS (always visible)                         │
└─────────────────────────────────────────────────┘
│ TERMINAL (scrollable history)                   │
│ > Your commands here                            │
│ Responses here                                  │
├─────────────────────────────────────────────────┤
Command: G28_
[q]uit [h]elp [Tab]complete
```

No confusing modes or focus switching - it just works like a terminal.

## Common Workflows

### Getting Started

1. Start Mooncrescent: `python mooncrescent.py`
2. Press `h` to see help
3. Start typing a command, press Tab to complete
4. Press Enter to send

### Homing the Printer

```
> G<Tab>
> G28<Enter>
```

Or with specific axes:
```
> G28 X Y<Enter>
```

### Setting Temperatures

```
> M<Tab>
> M104 S200<Enter>    # Set hotend to 200°C
> M140 S60<Enter>     # Set bed to 60°C
```

### Using Macros

Your printer's macros appear in auto-completion:

```
> PRE<Tab>
Auto-completes to: PREHEAT_PLA

> PREHEAT_PLA<Enter>
```

### Controlling a Print

Use G-code commands instead of keyboard shortcuts:

```
> PAUSE<Enter>        # If you have a PAUSE macro
> RESUME<Enter>       # If you have a RESUME macro
> CANCEL_PRINT<Enter> # If you have a CANCEL_PRINT macro
```

Or use M-codes:
```
> M24<Enter>          # Resume print
> M25<Enter>          # Pause print
```

### Checking Status

```
> M114<Enter>         # Current position
> M115<Enter>         # Firmware info
> M105<Enter>         # Current temperatures
```

## Keyboard Reference

| Key | Action |
|-----|--------|
| `?` | Show help |
| `Tab` | Auto-complete command |
| `↑` | Previous command (persisted) |
| `↓` | Next command (persisted) |
| `Enter` | Send command |
| `←` / `→` | Move cursor |
| `Home` / `End` | Jump to start/end |
| `Backspace` | Delete before cursor |
| `Delete` | Delete at cursor |
| `ESC` / `Ctrl-D` | Quit application |

## Why These Design Choices?

### No Pause/Resume/Cancel Shortcuts

**Removed:** `p`, `r`, `c` keyboard shortcuts

**Reason:** Too easy to press accidentally. A single mistyped key could cancel a 10-hour print.

**Alternative:** Use proper G-code commands or macros that you type intentionally:
- `PAUSE` macro
- `RESUME` macro  
- `CANCEL_PRINT` macro

This requires conscious action and typing, preventing accidents.

### No Focus Switching

**Removed:** Tab focus switching between terminal and input

**Reason:** Adds confusion and mode-like behavior. You should always be able to type.

**Result:** Clean, terminal-like experience. No modes, no confusion.

### Tab for Completion

**Added:** Tab auto-completion

**Reason:** This is what terminals do. It's intuitive and helpful.

**Benefits:**
- Faster command entry
- Discover available commands
- Avoid typos
- Learn macro names

### Safe Keyboard Shortcuts

**Changed:** 
- Quit: From `q` to `ESC` or `Ctrl-D`
- Help: From `h` to `?`

**Reason:** The old shortcuts (`h`, `q`) would trigger while typing G-code commands that contain those letters. For example:
- Typing "M109" would trigger help at the 'h'
- Typing "HEAT_BED" would trigger help at the 'h'
- Typing "QUERY_ADC" would trigger quit at the 'q'

**Result:** 
- `ESC` and `Ctrl-D` are standard terminal quit shortcuts that can't be accidentally typed
- `?` clearly signals intent to get help and won't interfere with any G-code
- You can now type any command without fear of triggering shortcuts

### Command History Persistence

**Added:** History saved to `~/.moonraker_tui_history`

**Reason:** Like bash/zsh, your command history should persist between sessions.

**Benefits:**
- Find commands you ran yesterday
- Build your personal command library
- No need to remember complex macro names
- Limited to 1000 most recent commands

## Tips & Tricks

### Discover Available Macros

Press `?` to see all macros defined in your printer config.

### Quick Temperature Commands

```
> M104 S200<Enter>    # Start heating hotend
> M140 S60<Enter>     # Start heating bed  
> G28<Enter>          # Home while heating
```

### Emergency Stop

```
> M112<Enter>         # Emergency stop (requires firmware restart)
```

Use with extreme caution!

### Check Print Progress

Just look at the status panel - it updates automatically.

### Finding a Command

Start typing and press Tab to see what's available:

```
> M1<Tab>
Completions: M104, M105, M106, M107, M109, M112, M114, M115
```

### Repeating Last Command

Press `↑` to get your last command, modify if needed, press Enter.

## Comparison: Before vs After

| Feature | Before | After |
|---------|--------|-------|
| Pause print | Press `p` | Type `PAUSE` or `M25` |
| Resume print | Press `r` | Type `RESUME` or `M24` |
| Cancel print | Press `c` | Type `CANCEL_PRINT` |
| Tab key | Switch focus | Auto-complete |
| Help | (none) | Press `h` |
| Input focus | Toggle with Tab | Always active |
| Safety | ⚠️ Risky | ✅ Safe |
| Terminal-like | ❌ No | ✅ Yes |

## Future Ideas

Potential future enhancements:

- History search (Ctrl+R)
- Command aliases
- Multi-line commands
- Macro editor
- File browser
- Plot temperature graphs
- Webcam view
- Touch support

Feedback welcome!

