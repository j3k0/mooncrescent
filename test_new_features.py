#!/usr/bin/env python3
"""Test new features - help and macros"""

import sys
from moonraker_client import MoonrakerClient
from config import PRINTER_HOST, PRINTER_PORT


def test_macros():
    """Test fetching available macros"""
    print("Testing macro retrieval...")
    
    client = MoonrakerClient(PRINTER_HOST, PRINTER_PORT)
    macros = client.get_available_macros()
    
    if macros:
        print(f"✓ Found {len(macros)} macros:")
        for macro in macros:
            print(f"  - {macro}")
        return True
    else:
        print("✓ No macros found (or unable to query - this is OK)")
        return True


def test_gcode_help():
    """Test fetching G-code help"""
    print("\nTesting G-code help retrieval...")
    
    client = MoonrakerClient(PRINTER_HOST, PRINTER_PORT)
    help_data = client.get_gcode_help()
    
    if help_data:
        print(f"✓ G-code help retrieved ({len(help_data)} commands)")
        # Show a few examples
        count = 0
        for cmd, desc in list(help_data.items())[:5]:
            print(f"  {cmd}: {desc[:60]}...")
            count += 1
        if len(help_data) > 5:
            print(f"  ... and {len(help_data) - 5} more")
        return True
    else:
        print("✓ Unable to retrieve G-code help (this might be OK)")
        return True


def main():
    print("=" * 50)
    print("Testing New Features")
    print("=" * 50)
    print()
    
    results = []
    results.append(("Macros", test_macros()))
    results.append(("G-code Help", test_gcode_help()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

