#!/usr/bin/env python3
"""
OpenBikeControl BLE Trainer App Example

This example demonstrates how to connect to an OpenBikeControl BLE device
and receive button state notifications. It shows:
- Device discovery using the OpenBikeControl service UUID
- Connecting to the device
- Subscribing to button state notifications
- Sending haptic feedback
- Parsing and displaying button state data

Requirements:
    pip install bleak

Usage:
    python ble_trainer_app.py
"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# OpenBikeControl Service and Characteristic UUIDs
SERVICE_UUID = "d273f680-d548-419d-b9d1-fa0472345229"
BUTTON_STATE_CHAR_UUID = "d273f681-d548-419d-b9d1-fa0472345229"
HAPTIC_FEEDBACK_CHAR_UUID = "d273f682-d548-419d-b9d1-fa0472345229"
APP_INFO_CHAR_UUID = "d273f683-d548-419d-b9d1-fa0472345229"

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

# Haptic feedback patterns
HAPTIC_PATTERNS = {
    "none": 0x00,
    "short": 0x01,
    "double": 0x02,
    "triple": 0x03,
    "long": 0x04,
    "success": 0x05,
    "warning": 0x06,
    "error": 0x07,
}


def parse_button_state(data: bytes) -> list:
    """
    Parse button state data from BLE notification.
    
    Data format: [Button_ID_1, State_1, Button_ID_2, State_2, ...]
    
    Args:
        data: Raw bytes from BLE notification
        
    Returns:
        List of tuples (button_id, state)
    """
    buttons = []
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            button_id = data[i]
            state = data[i + 1]
            buttons.append((button_id, state))
    return buttons


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


async def send_haptic_feedback(client: BleakClient, pattern: str = "short", 
                               duration: int = 0, intensity: int = 0):
    """
    Send haptic feedback command to the device.
    
    Args:
        client: BleakClient instance
        pattern: Haptic pattern name (see HAPTIC_PATTERNS)
        duration: Duration in 10ms units (0 = use default)
        intensity: Intensity 0-255 (0 = use default)
    """
    pattern_byte = HAPTIC_PATTERNS.get(pattern, HAPTIC_PATTERNS["short"])
    data = bytes([pattern_byte, duration, intensity])
    
    try:
        await client.write_gatt_char(HAPTIC_FEEDBACK_CHAR_UUID, data, response=False)
        print(f"  → Sent haptic feedback: {pattern}")
    except Exception as e:
        print(f"  ⚠ Failed to send haptic feedback: {e}")


async def send_app_info(client: BleakClient, app_id: str = "example-trainer-app",
                       app_version: str = "1.0.0",
                       supported_buttons: list = None):
    """
    Send app information to the device.
    
    Args:
        client: BleakClient instance
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
    
    # Build binary data according to BLE.md specification
    # Format: [Version] [App_ID_Length] [App_ID...] [App_Version_Length] [App_Version...] [Button_Count] [Button_IDs...]
    
    app_id_bytes = app_id.encode('utf-8')[:32]  # Max 32 chars
    app_version_bytes = app_version.encode('utf-8')[:32]  # Max 32 chars
    
    data = bytearray()
    data.append(0x01)  # Version
    data.append(len(app_id_bytes))  # App ID length
    data.extend(app_id_bytes)  # App ID
    data.append(len(app_version_bytes))  # App Version length
    data.extend(app_version_bytes)  # App Version
    data.append(len(supported_buttons))  # Button count
    data.extend(supported_buttons)  # Button IDs
    
    try:
        await client.write_gatt_char(APP_INFO_CHAR_UUID, bytes(data), response=False)
        print(f"  → Sent app info: {app_id} v{app_version} (supports {len(supported_buttons)} button types)")
    except Exception as e:
        print(f"  ⚠ Failed to send app info: {e}")



def button_state_callback(client: BleakClient):
    """
    Create a callback function for button state notifications.
    
    Args:
        client: BleakClient instance for sending haptic feedback
        
    Returns:
        Callback function
    """
    async def callback(sender, data: bytearray):
        """Handle button state notification."""
        buttons = parse_button_state(bytes(data))
        
        print(f"\n📍 Button State Update (received {len(data)} bytes):")
        for button_id, state in buttons:
            print(f"  {format_button_state(button_id, state)}")
            
            # Send haptic feedback on button press
            if state == 1:  # Button pressed
                await send_haptic_feedback(client, "short")
    
    return callback


async def scan_for_devices(timeout: float = 5.0) -> list:
    """
    Scan for OpenBikeControl BLE devices.
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of discovered BLEDevice objects
    """
    print(f"🔍 Scanning for OpenBikeControl devices (service UUID: {SERVICE_UUID})...")
    print(f"   Scan timeout: {timeout} seconds\n")
    
    devices = []
    
    def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
        if SERVICE_UUID.lower() in [uuid.lower() for uuid in advertisement_data.service_uuids]:
            if device not in devices:
                devices.append(device)
                print(f"✓ Found device: {device.name or 'Unknown'}")
                print(f"  Address: {device.address}")
                print(f"  RSSI: {advertisement_data.rssi} dBm")
                print()
    
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()
    
    return devices


async def connect_and_monitor(device: BLEDevice):
    """
    Connect to device and monitor button states.
    
    Args:
        device: BLEDevice to connect to
    """
    print(f"🔗 Connecting to {device.name or device.address}...")
    
    async with BleakClient(device.address) as client:
        print(f"✓ Connected to {device.name or device.address}\n")
        
        # Get device information
        print("📱 Device Information:")
        try:
            for service in client.services:
                if service.uuid.lower() == SERVICE_UUID.lower():
                    print(f"  Service: {service.uuid}")
                    for char in service.characteristics:
                        print(f"    Characteristic: {char.uuid}")
                        print(f"      Properties: {char.properties}")
        except Exception as e:
            print(f"  Could not read device info: {e}")
        
        print()
        
        # Send app information immediately after connecting
        await send_app_info(client)
        print()
        
        # Subscribe to button state notifications
        print("👂 Subscribing to button state notifications...")
        callback = button_state_callback(client)
        await client.start_notify(BUTTON_STATE_CHAR_UUID, callback)
        print("✓ Subscribed! Waiting for button presses...\n")
        print("Press Ctrl+C to stop\n")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹ Stopping...")
        finally:
            await client.stop_notify(BUTTON_STATE_CHAR_UUID)
            print("✓ Unsubscribed from notifications")


async def main():
    """Main application entry point."""
    print("=" * 60)
    print("OpenBikeControl BLE Trainer App Example")
    print("=" * 60)
    print()
    
    # Scan for devices
    devices = await scan_for_devices(timeout=5.0)
    
    if not devices:
        print("❌ No OpenBikeControl devices found.")
        print("\nMake sure your device is:")
        print("  1. Powered on")
        print("  2. In pairing/advertising mode")
        print("  3. Within Bluetooth range")
        print("  4. Advertising the OpenBikeControl service UUID")
        return 1
    
    print(f"Found {len(devices)} device(s)\n")
    
    # If multiple devices found, let user choose
    if len(devices) > 1:
        print("Multiple devices found. Select one:")
        for idx, dev in enumerate(devices):
            print(f"  {idx + 1}. {dev.name or 'Unknown'} ({dev.address})")
        
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
    try:
        await connect_and_monitor(selected_device)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    print("\n✓ Disconnected successfully")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
