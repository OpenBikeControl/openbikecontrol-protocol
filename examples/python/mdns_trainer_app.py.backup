#!/usr/bin/env python3
"""
OpenBikeControl mDNS Trainer App Example

This example demonstrates how to connect to an OpenBikeControl mDNS device
and receive button state updates via WebSocket. It shows:
- Service discovery using Zeroconf (mDNS/Bonjour)
- WebSocket connection to device
- Receiving and parsing button state messages
- Sending haptic feedback commands
- Handling device status updates

Requirements:
    pip install zeroconf websockets

Usage:
    python mdns_trainer_app.py
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import websockets

# OpenBikeControl mDNS service type
SERVICE_TYPE = "_openbikecontrol._tcp.local."

# Button ID to name mapping (based on PROTOCOL.md)
BUTTON_NAMES = {
    # Gear Shifting (0x01-0x0F)
    0x01: "Shift Up",
    0x02: "Shift Down",
    0x03: "Gear Set",
    # Navigation (0x10-0x1F)
    0x10: "Up/Steer Left",
    0x11: "Down/Steer Right",
    0x12: "Left/Look Left",
    0x13: "Right/Look Right",
    0x14: "Select/Confirm",
    0x15: "Back/Cancel",
    0x16: "Menu",
    0x17: "Home",
    # Social/Emotes (0x20-0x2F)
    0x20: "Wave",
    0x21: "Thumbs Up",
    0x22: "Hammer Time",
    0x23: "Bell",
    0x24: "Screenshot",
    # Training Controls (0x30-0x3F)
    0x30: "ERG Up",
    0x31: "ERG Down",
    0x32: "Skip Interval",
    0x33: "Pause",
    0x34: "Resume",
    0x35: "Lap",
    # View Controls (0x40-0x4F)
    0x40: "Camera Angle",
    0x41: "Camera 1",
    0x42: "Camera 2",
    0x43: "Camera 3",
    0x44: "HUD Toggle",
    0x45: "Map Toggle",
    # Power-ups (0x50-0x5F)
    0x50: "Power-up 1",
    0x51: "Power-up 2",
    0x52: "Power-up 3",
}


class DeviceInfo:
    """Information about a discovered OpenBikeControl device."""
    
    def __init__(self, name: str, addresses: list, port: int, properties: dict):
        self.name = name
        self.addresses = addresses
        self.port = port
        self.properties = properties
    
    def __str__(self):
        return f"{self.name} at {self.addresses[0]}:{self.port}"
    
    def get_websocket_url(self) -> str:
        """Get WebSocket URL for this device."""
        return f"ws://{self.addresses[0]}:{self.port}/api/ws"


class OpenBikeControlListener(ServiceListener):
    """Zeroconf listener for OpenBikeControl devices."""
    
    def __init__(self):
        self.devices = []
        self.device_found_event = asyncio.Event()
    
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a new service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [addr for addr in info.parsed_addresses()]
            if addresses:
                properties = {}
                for key, value in info.properties.items():
                    try:
                        properties[key.decode('utf-8')] = value.decode('utf-8')
                    except:
                        properties[key.decode('utf-8')] = value
                
                device = DeviceInfo(
                    name=name,
                    addresses=addresses,
                    port=info.port,
                    properties=properties
                )
                self.devices.append(device)
                
                print(f"✓ Found device: {properties.get('name', 'Unknown')}")
                print(f"  Service: {name}")
                print(f"  Address: {addresses[0]}:{info.port}")
                print(f"  ID: {properties.get('id', 'N/A')}")
                print(f"  Manufacturer: {properties.get('manufacturer', 'N/A')}")
                print(f"  Model: {properties.get('model', 'N/A')}")
                print()
                
                self.device_found_event.set()
    
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        pass
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        pass


def format_button_state(button_id: int, state: int) -> str:
    """
    Format button state for display.
    
    Args:
        button_id: Button identifier
        state: Button state (0=released, 1=pressed, 2-255=analog)
        
    Returns:
        Formatted string
    """
    button_name = BUTTON_NAMES.get(button_id, f"Button 0x{button_id:02X}")
    
    if state == 0:
        state_str = "RELEASED"
    elif state == 1:
        state_str = "PRESSED"
    else:
        # Analog value (2-255)
        percentage = int((state - 2) / (255 - 2) * 100)
        state_str = f"ANALOG {percentage}%"
    
    return f"{button_name}: {state_str}"


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
    return dt.strftime("%H:%M:%S.%f")[:-3]


async def send_haptic_feedback(websocket, pattern: str = "short", 
                               duration: int = 0, intensity: int = 0):
    """
    Send haptic feedback command to the device.
    
    Args:
        websocket: WebSocket connection
        pattern: Haptic pattern name
        duration: Duration in milliseconds (0 = use default)
        intensity: Intensity 0-255 (0 = use default)
    """
    message = {
        "type": "haptic_feedback",
        "pattern": pattern,
        "duration": duration,
        "intensity": intensity
    }
    
    try:
        await websocket.send(json.dumps(message))
        print(f"  → Sent haptic feedback: {pattern}")
    except Exception as e:
        print(f"  ⚠ Failed to send haptic feedback: {e}")


async def send_app_info(websocket, app_id: str = "example-trainer-app", 
                       app_version: str = "1.0.0", 
                       supported_buttons: list = None):
    """
    Send app information to the device.
    
    Args:
        websocket: WebSocket connection
        app_id: App identifier string
        app_version: App version string
        supported_buttons: List of supported button IDs (empty list = all buttons)
    """
    if supported_buttons is None:
        # Default: support common buttons for trainer apps
        supported_buttons = [
            0x01, 0x02,  # Shift Up/Down
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15,  # Navigation
            0x20, 0x21,  # Wave, Thumbs Up
            0x30, 0x31, 0x32, 0x33, 0x34,  # Training Controls
        ]
    
    message = {
        "type": "app_info",
        "app_id": app_id,
        "app_version": app_version,
        "supported_buttons": supported_buttons
    }
    
    try:
        await websocket.send(json.dumps(message))
        print(f"  → Sent app info: {app_id} v{app_version} (supports {len(supported_buttons)} button types)")
    except Exception as e:
        print(f"  ⚠ Failed to send app info: {e}")



async def handle_message(websocket, message: dict):
    """
    Handle incoming WebSocket message.
    
    Args:
        websocket: WebSocket connection
        message: Parsed JSON message
    """
    msg_type = message.get("type")
    
    if msg_type == "button_state":
        # Button state change
        timestamp = message.get("timestamp", 0)
        buttons = message.get("buttons", [])
        
        print(f"\n📍 Button State Update [{format_timestamp(timestamp)}]:")
        for button in buttons:
            button_id = button.get("id")
            state = button.get("state")
            if button_id is not None and state is not None:
                print(f"  {format_button_state(button_id, state)}")
                
                # Send haptic feedback on button press
                if state == 1:  # Button pressed
                    await send_haptic_feedback(websocket, "short")
    
    elif msg_type == "device_status":
        # Device status update
        timestamp = message.get("timestamp", 0)
        battery = message.get("battery")
        connected = message.get("connected", True)
        
        print(f"\n🔋 Device Status Update [{format_timestamp(timestamp)}]:")
        if battery is not None:
            print(f"  Battery: {battery}%")
        print(f"  Connected: {'Yes' if connected else 'No'}")
    
    elif msg_type == "haptic_feedback_response":
        # Haptic feedback response
        timestamp = message.get("timestamp", 0)
        success = message.get("success", False)
        status = "✓" if success else "✗"
        print(f"  {status} Haptic feedback {'acknowledged' if success else 'failed'} [{format_timestamp(timestamp)}]")
    
    else:
        print(f"\n⚠ Unknown message type: {msg_type}")
        print(f"  Message: {message}")


async def connect_and_monitor(device: DeviceInfo):
    """
    Connect to device via WebSocket and monitor button states.
    
    Args:
        device: DeviceInfo object with connection details
    """
    url = device.get_websocket_url()
    print(f"🔗 Connecting to {device.name}...")
    print(f"   WebSocket URL: {url}\n")
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to {device.name}\n")
            
            # Send app information immediately after connecting
            await send_app_info(websocket)
            print()
            
            print("👂 Listening for messages...")
            print("Press Ctrl+C to stop\n")
            
            # Receive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await handle_message(websocket, data)
                except json.JSONDecodeError as e:
                    print(f"⚠ Failed to parse message: {e}")
                    print(f"  Raw message: {message}")
                except Exception as e:
                    print(f"⚠ Error handling message: {e}")
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("✓ Disconnected successfully")
    return 0


async def discover_devices(timeout: float = 5.0) -> list:
    """
    Discover OpenBikeControl devices using mDNS/Zeroconf.
    
    Args:
        timeout: Discovery duration in seconds
        
    Returns:
        List of DeviceInfo objects
    """
    print(f"🔍 Discovering OpenBikeControl devices (service type: {SERVICE_TYPE})...")
    print(f"   Discovery timeout: {timeout} seconds\n")
    
    zeroconf = Zeroconf()
    listener = OpenBikeControlListener()
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    
    try:
        # Wait for timeout or until a device is found
        await asyncio.sleep(timeout)
    finally:
        browser.cancel()
        zeroconf.close()
    
    return listener.devices


async def main():
    """Main application entry point."""
    print("=" * 60)
    print("OpenBikeControl mDNS Trainer App Example")
    print("=" * 60)
    print()
    
    # Discover devices
    devices = await discover_devices(timeout=5.0)
    
    if not devices:
        print("❌ No OpenBikeControl devices found.")
        print("\nMake sure your device is:")
        print("  1. Powered on")
        print("  2. Connected to the same network")
        print("  3. Advertising the mDNS service")
        return 1
    
    print(f"Found {len(devices)} device(s)\n")
    
    # If multiple devices found, let user choose
    if len(devices) > 1:
        print("Multiple devices found. Select one:")
        for idx, dev in enumerate(devices):
            device_name = dev.properties.get('name', 'Unknown')
            print(f"  {idx + 1}. {device_name} ({dev.addresses[0]}:{dev.port})")
        
        try:
            choice = int(input("\nEnter device number: ")) - 1
            if choice < 0 or choice >= len(devices):
                print("Invalid choice")
                return 1
            selected_device = devices[choice]
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled")
            return 1
    else:
        selected_device = devices[0]
    
    print()
    
    # Connect and monitor
    return await connect_and_monitor(selected_device)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
