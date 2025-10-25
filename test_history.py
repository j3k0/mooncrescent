#!/usr/bin/env python3
"""Test history persistence"""

import os
import tempfile
from command_handler import CommandHandler


def test_history_persistence():
    """Test that history is saved and loaded correctly"""
    print("Testing history persistence...")
    
    # Use a temporary file for testing
    temp_file = tempfile.mktemp(suffix=".history")
    
    try:
        # Create handler and add some commands
        handler1 = CommandHandler()
        handler1.command_buffer = "G28"
        handler1.submit_command()
        handler1.command_buffer = "M104 S200"
        handler1.submit_command()
        handler1.command_buffer = "M140 S60"
        handler1.submit_command()
        
        print(f"  Added 3 commands to history")
        
        # Save history
        handler1.save_history(temp_file)
        print(f"  Saved history to {temp_file}")
        
        # Check file exists
        if not os.path.exists(temp_file):
            print("✗ History file not created")
            return False
            
        # Create new handler and load history
        handler2 = CommandHandler()
        handler2.load_history(temp_file)
        
        print(f"  Loaded history, got {len(handler2.command_history)} commands")
        
        # Verify history
        if len(handler2.command_history) != 3:
            print(f"✗ Expected 3 commands, got {len(handler2.command_history)}")
            return False
            
        if handler2.command_history[0] != "G28":
            print(f"✗ Expected 'G28', got '{handler2.command_history[0]}'")
            return False
            
        if handler2.command_history[1] != "M104 S200":
            print(f"✗ Expected 'M104 S200', got '{handler2.command_history[1]}'")
            return False
            
        if handler2.command_history[2] != "M140 S60":
            print(f"✗ Expected 'M140 S60', got '{handler2.command_history[2]}'")
            return False
            
        print("✓ History persistence works correctly")
        return True
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_history_navigation():
    """Test navigating through saved history"""
    print("\nTesting history navigation...")
    
    handler = CommandHandler()
    
    # Add some commands
    handler.command_buffer = "G28"
    handler.submit_command()
    handler.command_buffer = "M104 S200"
    handler.submit_command()
    
    # Navigate up
    handler.history_up()
    text, _ = handler.get_display_text()
    
    if text != "M104 S200":
        print(f"✗ Expected 'M104 S200', got '{text}'")
        return False
        
    # Navigate up again
    handler.history_up()
    text, _ = handler.get_display_text()
    
    if text != "G28":
        print(f"✗ Expected 'G28', got '{text}'")
        return False
        
    # Navigate down
    handler.history_down()
    text, _ = handler.get_display_text()
    
    if text != "M104 S200":
        print(f"✗ Expected 'M104 S200', got '{text}'")
        return False
        
    print("✓ History navigation works correctly")
    return True


def main():
    print("=" * 50)
    print("History Persistence Tests")
    print("=" * 50)
    print()
    
    results = []
    results.append(("Persistence", test_history_persistence()))
    results.append(("Navigation", test_history_navigation()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    print("=" * 50)
    
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

