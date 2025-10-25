#!/usr/bin/env python3
"""Integration tests for Moonraker TUI with real printer connection"""

import sys
import time
import argparse
from moonraker_client import MoonrakerClient
from config import PRINTER_HOST, PRINTER_PORT


def test_connection(host: str, port: int):
    """Test basic connection to Moonraker"""
    print(f"Testing connection to {host}:{port}...")
    
    client = MoonrakerClient(host, port)
    
    # Test connection
    if client.connect():
        print("✓ WebSocket connection successful")
        time.sleep(2)  # Wait for subscription
        
        # Check for status updates
        messages_received = 0
        for _ in range(10):
            msg = client.get_message()
            if msg:
                messages_received += 1
                print(f"  Received message: {msg.get('type')}")
            time.sleep(0.1)
        
        if messages_received > 0:
            print(f"✓ Received {messages_received} status updates")
        else:
            print("⚠ No status updates received")
        
        client.disconnect()
        return True
    else:
        print("✗ Connection failed")
        return False


def test_printer_info(host: str, port: int):
    """Test getting printer info via HTTP"""
    print(f"\nTesting HTTP API (printer info)...")
    
    client = MoonrakerClient(host, port)
    info = client.get_printer_info()
    
    if info:
        print("✓ Printer info retrieved")
        if "result" in info:
            result = info["result"]
            print(f"  State: {result.get('state', 'unknown')}")
            print(f"  State message: {result.get('state_message', 'N/A')}")
        return True
    else:
        print("✗ Failed to get printer info")
        return False


def test_printer_objects(host: str, port: int):
    """Test querying printer objects"""
    print(f"\nTesting printer objects query...")
    
    client = MoonrakerClient(host, port)
    objects = client.get_printer_objects()
    
    if objects:
        print("✓ Printer objects retrieved")
        for obj_name in objects.keys():
            print(f"  - {obj_name}")
        return True
    else:
        print("✗ Failed to get printer objects")
        return False


def test_gcode_command(host: str, port: int, command: str = "G28"):
    """Test sending a G-code command"""
    print(f"\nTesting G-code command: {command}")
    print("=" * 50)
    
    client = MoonrakerClient(host, port)
    
    # Connect to receive responses
    print("Connecting...")
    if not client.connect():
        print("✗ Connection failed")
        return False
    
    print("✓ Connected")
    time.sleep(1)  # Wait for initial messages
    
    # Clear message queue
    while client.get_message():
        pass
    
    # Send command
    print(f"Sending command: {command}")
    success = client.send_gcode(command)
    
    if success:
        print("✓ Command sent successfully")
    else:
        print("✗ Command send failed")
        
        # Check for error messages
        time.sleep(0.5)
        while True:
            msg = client.get_message()
            if not msg:
                break
            if msg.get("type") == "error":
                print(f"  Error: {msg.get('message')}")
        
        client.disconnect()
        return False
    
    # Wait for response
    print("Waiting for response...")
    response_received = False
    
    for i in range(50):  # Wait up to 5 seconds
        msg = client.get_message()
        if msg:
            msg_type = msg.get("type")
            print(f"  Message type: {msg_type}")
            
            if msg_type == "gcode_response":
                response = msg.get("response", "")
                print(f"  Response: {response}")
                response_received = True
                
            elif msg_type == "error":
                print(f"  Error: {msg.get('message')}")
                
        time.sleep(0.1)
    
    if response_received:
        print("✓ Command executed and response received")
    else:
        print("⚠ No response received (this might be normal for some commands)")
    
    client.disconnect()
    return True


def test_gcode_http_directly(host: str, port: int, command: str = "M115"):
    """Test G-code HTTP endpoint directly with detailed output"""
    print(f"\nTesting G-code HTTP endpoint directly...")
    print(f"Command: {command}")
    print("=" * 50)
    
    import requests
    
    url = f"http://{host}:{port}/printer/gcode/script"
    
    # Try GET request
    print(f"\nAttempting GET request to: {url}")
    try:
        params = {"script": command}
        print(f"Params: {params}")
        response = requests.get(url, params=params, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"GET failed: {e}")
    
    # Try POST request
    print(f"\nAttempting POST request to: {url}")
    try:
        params = {"script": command}
        print(f"Params: {params}")
        response = requests.post(url, params=params, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST failed: {e}")
    
    # Try POST with JSON
    print(f"\nAttempting POST with JSON body to: {url}")
    try:
        data = {"script": command}
        print(f"JSON data: {data}")
        response = requests.post(url, json=data, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST with JSON failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Integration tests for Moonraker TUI")
    parser.add_argument("--host", default=PRINTER_HOST, help="Moonraker host")
    parser.add_argument("--port", type=int, default=PRINTER_PORT, help="Moonraker port")
    parser.add_argument("--command", default="M115", help="G-code command to test")
    parser.add_argument("--test", choices=["all", "connect", "info", "objects", "gcode", "http"], 
                       default="all", help="Which test to run")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Moonraker TUI Integration Tests")
    print("=" * 50)
    print(f"Host: {args.host}:{args.port}")
    print()
    
    results = []
    
    if args.test in ["all", "connect"]:
        results.append(("Connection", test_connection(args.host, args.port)))
    
    if args.test in ["all", "info"]:
        results.append(("Printer Info", test_printer_info(args.host, args.port)))
    
    if args.test in ["all", "objects"]:
        results.append(("Printer Objects", test_printer_objects(args.host, args.port)))
    
    if args.test in ["all", "http"]:
        test_gcode_http_directly(args.host, args.port, args.command)
    
    if args.test in ["all", "gcode"]:
        results.append(("G-code Command", test_gcode_command(args.host, args.port, args.command)))
    
    if results:
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

