"""Moonraker WebSocket and HTTP client"""

import json
import threading
import time
from queue import Queue
from typing import Callable, Optional, Dict, Any

import requests
import websocket


class MoonrakerClient:
    """Client for communicating with Moonraker API"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.ws_url = f"ws://{host}:{port}/websocket"
        self.http_url = f"http://{host}:{port}"
        
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.connected = False
        self.running = False
        
        # Message queue for thread-safe communication
        self.message_queue: Queue = Queue()
        
        # Callback for status updates
        self.update_callback: Optional[Callable] = None
        
        # Request ID counter
        self.request_id = 0
        
        # Store latest printer state
        self.printer_state: Dict[str, Any] = {}
        
    def connect(self) -> bool:
        """Connect to Moonraker WebSocket"""
        try:
            self.running = True
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Start WebSocket in separate thread
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()
            
            # Wait a bit for connection
            time.sleep(1)
            
            return self.connected
            
        except Exception as e:
            self.message_queue.put({
                "type": "error",
                "message": f"Connection failed: {e}"
            })
            return False
            
    def disconnect(self):
        """Disconnect from Moonraker"""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=2)
        self.connected = False
        
    def _run_websocket(self):
        """Run WebSocket connection (in separate thread)"""
        while self.running:
            try:
                self.ws.run_forever()
                if self.running:
                    # Connection lost, wait before retry
                    time.sleep(5)
            except Exception as e:
                self.message_queue.put({
                    "type": "error", 
                    "message": f"WebSocket error: {e}"
                })
                time.sleep(5)
                
    def _on_open(self, ws):
        """WebSocket opened - subscribe to printer objects"""
        self.connected = True
        self.message_queue.put({
            "type": "connection",
            "connected": True
        })
        
        # Subscribe to printer object updates
        subscribe_request = {
            "jsonrpc": "2.0",
            "method": "printer.objects.subscribe",
            "params": {
                "objects": {
                    "print_stats": [
                        "state", "filename", "total_duration", 
                        "print_duration", "filament_used", "info"
                    ],
                    "display_status": ["progress", "message"],
                    "toolhead": [
                        "position", "homed_axes", "print_time", 
                        "estimated_print_time"
                    ],
                    "heater_bed": ["temperature", "target"],
                    "extruder": ["temperature", "target", "power"],
                    "gcode_move": [
                        "speed_factor", "extrude_factor", "speed", 
                        "absolute_coordinates"
                    ]
                }
            },
            "id": self._get_request_id()
        }
        
        ws.send(json.dumps(subscribe_request))
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Check if it's a notification (status update)
            if "method" in data and data["method"] == "notify_status_update":
                if "params" in data and len(data["params"]) > 0:
                    status = data["params"][0]
                    
                    # Update printer state
                    for obj_name, obj_data in status.items():
                        if obj_name not in self.printer_state:
                            self.printer_state[obj_name] = {}
                        self.printer_state[obj_name].update(obj_data)
                    
                    # Send to main thread
                    self.message_queue.put({
                        "type": "status_update",
                        "data": self.printer_state
                    })
                    
            # Check if it's a response to our request
            elif "result" in data:
                if "status" in data["result"]:
                    # Initial state response
                    for obj_name, obj_data in data["result"]["status"].items():
                        self.printer_state[obj_name] = obj_data
                        
                    self.message_queue.put({
                        "type": "status_update",
                        "data": self.printer_state
                    })
                    
            # Check for gcode response
            elif "method" in data and data["method"] == "notify_gcode_response":
                if "params" in data and len(data["params"]) > 0:
                    response = data["params"][0]
                    self.message_queue.put({
                        "type": "gcode_response",
                        "response": response
                    })
                    
        except json.JSONDecodeError as e:
            self.message_queue.put({
                "type": "error",
                "message": f"Failed to parse message: {e}"
            })
            
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        self.message_queue.put({
            "type": "error",
            "message": f"WebSocket error: {error}"
        })
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.connected = False
        self.message_queue.put({
            "type": "connection",
            "connected": False
        })
        
    def _get_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
        
    def send_gcode(self, command: str) -> bool:
        """Send G-code command via HTTP"""
        try:
            url = f"{self.http_url}/printer/gcode/script"
            params = {"script": command}
            # Long timeout for commands that take time (homing, heating, etc.)
            # The response comes via WebSocket anyway
            response = requests.post(url, params=params, timeout=120)
            
            if response.status_code == 200:
                return True
            else:
                self.message_queue.put({
                    "type": "error",
                    "message": f"GCode failed: {response.text}"
                })
                return False
                
        except requests.exceptions.Timeout:
            # Command was sent but took too long - this is actually OK
            # The response will come via WebSocket
            self.message_queue.put({
                "type": "gcode_response",
                "response": "(command sent, waiting for completion...)"
            })
            return True
                
        except requests.exceptions.RequestException as e:
            self.message_queue.put({
                "type": "error",
                "message": f"Failed to send command: {e}"
            })
            return False
            
    def get_printer_info(self) -> Optional[Dict]:
        """Get printer info via HTTP"""
        try:
            url = f"{self.http_url}/printer/info"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.exceptions.RequestException:
            return None
            
    def get_printer_objects(self) -> Optional[Dict]:
        """Query printer objects via HTTP"""
        try:
            url = f"{self.http_url}/printer/objects/query"
            params = {
                "print_stats": "",
                "display_status": "",
                "toolhead": "",
                "heater_bed": "",
                "extruder": "",
                "gcode_move": ""
            }
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "status" in data["result"]:
                    return data["result"]["status"]
            return None
            
        except requests.exceptions.RequestException:
            return None
            
    def pause_print(self) -> bool:
        """Pause current print"""
        try:
            url = f"{self.http_url}/printer/print/pause"
            response = requests.post(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def resume_print(self) -> bool:
        """Resume paused print"""
        try:
            url = f"{self.http_url}/printer/print/resume"
            response = requests.post(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def cancel_print(self) -> bool:
        """Cancel current print"""
        try:
            url = f"{self.http_url}/printer/print/cancel"
            response = requests.post(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def start_print(self, filename: str) -> bool:
        """Start printing a file"""
        try:
            url = f"{self.http_url}/printer/print/start"
            data = {"filename": filename}
            response = requests.post(url, json=data, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def get_gcode_help(self) -> Optional[Dict]:
        """Get available G-code commands and help"""
        try:
            url = f"{self.http_url}/printer/gcode/help"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    return data["result"]
            return None
            
        except requests.exceptions.RequestException:
            return None
            
    def get_available_macros(self) -> list:
        """Get list of available G-code macros"""
        try:
            # Query for all configfile data which includes macros
            url = f"{self.http_url}/printer/objects/query"
            params = {"configfile": ""}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "status" in data["result"]:
                    config = data["result"]["status"].get("configfile", {})
                    settings = config.get("settings", {})
                    
                    # Extract macros (they start with "gcode_macro ")
                    macros = []
                    for key in settings.keys():
                        if key.startswith("gcode_macro "):
                            macro_name = key.replace("gcode_macro ", "")
                            macros.append(macro_name)
                    
                    return sorted(macros)
            return []
            
        except requests.exceptions.RequestException:
            return []
            
    def get_message(self) -> Optional[Dict]:
        """Get next message from queue (non-blocking)"""
        if not self.message_queue.empty():
            return self.message_queue.get()
        return None

