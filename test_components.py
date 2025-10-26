#!/usr/bin/env python3
"""Basic component tests for Moonraker TUI"""

import sys


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from mooncrescent import config
        print("✓ config imported")
        
        from mooncrescent import command_handler
        print("✓ command_handler imported")
        
        from mooncrescent import moonraker_client
        print("✓ moonraker_client imported")
        
        from mooncrescent import ui_layout
        print("✓ ui_layout imported")
        
        import mooncrescent
        print("✓ mooncrescent imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_command_handler():
    """Test CommandHandler functionality"""
    print("\nTesting CommandHandler...")
    try:
        from mooncrescent.command_handler import CommandHandler
        
        handler = CommandHandler()
        
        # Test adding characters
        handler.add_char('G')
        handler.add_char('2')
        handler.add_char('8')
        text, pos = handler.get_display_text()
        assert text == "G28", f"Expected 'G28', got '{text}'"
        assert pos == 3, f"Expected cursor at 3, got {pos}"
        print("✓ Character input works")
        
        # Test backspace
        handler.delete_char()
        text, pos = handler.get_display_text()
        assert text == "G2", f"Expected 'G2', got '{text}'"
        print("✓ Backspace works")
        
        # Test cursor movement
        handler.move_cursor(-1)
        text, pos = handler.get_display_text()
        assert pos == 1, f"Expected cursor at 1, got {pos}"
        print("✓ Cursor movement works")
        
        # Test command submission and history
        handler.clear()
        handler.add_char('G')
        handler.add_char('2')
        handler.add_char('8')
        cmd = handler.submit_command()
        assert cmd == "G28", f"Expected 'G28', got '{cmd}'"
        assert handler.command_buffer == "", "Buffer should be empty after submit"
        print("✓ Command submission works")
        
        # Test history
        handler.add_char('M')
        handler.add_char('1')
        handler.add_char('0')
        handler.add_char('4')
        handler.submit_command()
        
        handler.history_up()
        text, pos = handler.get_display_text()
        assert text == "M104", f"Expected 'M104' from history, got '{text}'"
        
        handler.history_up()
        text, pos = handler.get_display_text()
        assert text == "G28", f"Expected 'G28' from history, got '{text}'"
        print("✓ Command history works")
        
        return True
    except Exception as e:
        print(f"✗ CommandHandler test failed: {e}")
        return False


def test_moonraker_client():
    """Test MoonrakerClient initialization"""
    print("\nTesting MoonrakerClient...")
    try:
        from mooncrescent.moonraker_client import MoonrakerClient
        
        # Just test initialization (not actual connection)
        client = MoonrakerClient("192.168.1.100", 7125)
        assert client.host == "192.168.1.100"
        assert client.port == 7125
        assert client.ws_url == "ws://192.168.1.100:7125/websocket"
        assert client.http_url == "http://192.168.1.100:7125"
        print("✓ MoonrakerClient initialization works")
        
        return True
    except Exception as e:
        print(f"✗ MoonrakerClient test failed: {e}")
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting config...")
    try:
        from mooncrescent import config
        
        assert hasattr(config, 'PRINTER_HOST')
        assert hasattr(config, 'PRINTER_PORT')
        assert hasattr(config, 'TERMINAL_HISTORY_SIZE')
        assert hasattr(config, 'UPDATE_INTERVAL')
        print("✓ Config has all required attributes")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Mooncrescent Component Tests")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("CommandHandler", test_command_handler()))
    results.append(("MoonrakerClient", test_moonraker_client()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

