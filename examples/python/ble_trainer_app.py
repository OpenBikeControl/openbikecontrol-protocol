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

# Import shared protocol parsing functions
from protocol_parser import (
    parse_button_state,
    format_button_state,
    encode_haptic_feedback,
    encode_app_info,
    BUTTON_NAMES
)

# OpenBikeControl Service and Characteristic UUIDs
SERVICE_UUID = "d273f680-d548-419d-b9d1-fa0472345229"
BUTTON_STATE_CHAR_UUID = "d273f681-d548-419d-b9d1-fa0472345229"
HAPTIC_FEEDBACK_CHAR_UUID = "d273f682-d548-419d-b9d1-fa0472345229"
APP_INFO_CHAR_UUID = "d273f683-d548-419d-b9d1-fa0472345229"


async def send_haptic_feedback(client: BleakClient, pattern: str = "short", 
                               duration: int = 0, intensity: int = 0):
    """
    Send haptic feedback command to the device.
    
    Args:
        client: BleakClient instance
        pattern: Haptic pattern name
        duration: Duration in 10ms units (0 = use default)
        intensity: Intensity 0-255 (0 = use default)
    """
    data = encode_haptic_feedback(pattern, duration, intensity)
    
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
            0x18, 0x19,  # Steer Left/Right
            0x20,  # Emote
            0x30, 0x31, 0x32, 0x33, 0x34,  # Training Controls
            0x40,  # Camera View
        ]
    
    data = encode_app_info(app_id, app_version, supported_buttons)
    
    try:
        await client.write_gatt_char(APP_INFO_CHAR_UUID, data, response=False)
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
