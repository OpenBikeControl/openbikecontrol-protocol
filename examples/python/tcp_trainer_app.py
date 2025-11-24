#!/usr/bin/env python3
"""
OpenBikeControl TCP Trainer App Example

This example demonstrates how to connect to an OpenBikeControl device via TCP
and receive button state updates. It shows:
- Service discovery using Zeroconf (mDNS/Bonjour)
- TCP connection to device
- Receiving and parsing button state messages
- Sending haptic feedback commands
- Handling device status updates

Requirements:
    pip install zeroconf

Usage:
    python tcp_trainer_app.py
"""

import asyncio
import sys
import struct
from datetime import datetime
from typing import Optional
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

# Import shared protocol parsing functions
from protocol_parser import (
    parse_button_state,
    parse_device_status,
    format_button_state,
    encode_haptic_feedback,
    encode_app_info,
    MSG_TYPE_BUTTON_STATE,
    MSG_TYPE_DEVICE_STATUS,
    MSG_TYPE_HAPTIC_FEEDBACK,
    MSG_TYPE_APP_INFO,
    BUTTON_NAMES
)

# OpenBikeControl mDNS service type
SERVICE_TYPE = "_openbikecontrol._tcp.local."


class DeviceInfo:
    """Information about a discovered OpenBikeControl device."""
    
    def __init__(self, name: str, addresses: list, port: int, properties: dict):
        self.name = name
        self.addresses = addresses
        self.port = port
        self.properties = properties
    
    def __str__(self):
        return f"{self.name} at {self.addresses[0]}:{self.port}"


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


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
    return dt.strftime("%H:%M:%S.%f")[:-3]


async def send_haptic_feedback(writer: asyncio.StreamWriter, pattern: str = "short", 
                               duration: int = 0, intensity: int = 0):
    """
    Send haptic feedback command to the device.
    
    Args:
        writer: StreamWriter for TCP connection
        pattern: Haptic pattern name
        duration: Duration in 10ms units (0 = use default)
        intensity: Intensity 0-255 (0 = use default)
    """
    message = encode_haptic_feedback(pattern, duration, intensity, include_msg_type=True)
    
    try:
        writer.write(message)
        await writer.drain()
        print(f"  → Sent haptic feedback: {pattern}")
    except Exception as e:
        print(f"  ⚠ Failed to send haptic feedback: {e}")


async def send_app_info(writer: asyncio.StreamWriter, app_id: str = "example-trainer-app", 
                       app_version: str = "1.0.0", 
                       supported_buttons: list = None):
    """
    Send app information to the device.
    
    Args:
        writer: StreamWriter for TCP connection
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
    
    message = encode_app_info(app_id, app_version, supported_buttons, include_msg_type=True)
    
    try:
        writer.write(message)
        await writer.drain()
        print(f"  → Sent app info: {app_id} v{app_version} (supports {len(supported_buttons)} button types)")
    except Exception as e:
        print(f"  ⚠ Failed to send app info: {e}")


async def handle_button_state_message(data: bytes, writer: asyncio.StreamWriter):
    """Handle incoming button state message."""
    buttons = parse_button_state(data)
    
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    print(f"\n📍 Button State Update [{format_timestamp(timestamp_ms)}]:")
    for button_id, state in buttons:
        print(f"  {format_button_state(button_id, state)}")
        
        # Send haptic feedback on button press
        if state == 1:  # Button pressed
            await send_haptic_feedback(writer, "short")


async def handle_device_status_message(data: bytes):
    """Handle incoming device status message."""
    status = parse_device_status(data)
    
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    print(f"\n🔋 Device Status Update [{format_timestamp(timestamp_ms)}]:")
    if status["battery"] is not None:
        print(f"  Battery: {status['battery']}%")
    print(f"  Connected: {'Yes' if status['connected'] else 'No'}")


async def read_tcp_messages(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Read and handle TCP messages from the device.
    
    Args:
        reader: StreamReader for TCP connection
        writer: StreamWriter for TCP connection
    """
    try:
        while True:
            # Read message type byte
            msg_type_data = await reader.read(1)
            if not msg_type_data:
                break  # Connection closed
            
            msg_type = msg_type_data[0]
            
            if msg_type == MSG_TYPE_BUTTON_STATE:
                # Button state message - variable length
                # Read pairs of (button_id, state) until we get a new message type
                # For simplicity, we'll read in small chunks and parse
                chunk = await reader.read(128)  # Read up to 128 bytes
                if not chunk:
                    break
                
                # Reconstruct full message with message type
                full_message = msg_type_data + chunk
                await handle_button_state_message(full_message, writer)
            
            elif msg_type == MSG_TYPE_DEVICE_STATUS:
                # Device status message - fixed 2 more bytes
                status_data = await reader.read(2)
                if len(status_data) < 2:
                    break
                
                full_message = msg_type_data + status_data
                await handle_device_status_message(full_message)
            
            else:
                print(f"\n⚠ Unknown message type: 0x{msg_type:02X}")
                # Skip unknown message - try to continue
                await reader.read(64)  # Read and discard some bytes
    
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"\n❌ Error reading messages: {e}")


async def connect_and_monitor(device: DeviceInfo):
    """
    Connect to device via TCP and monitor button states.
    
    Args:
        device: DeviceInfo object with connection details
    """
    host = device.addresses[0]
    port = device.port
    
    print(f"🔗 Connecting to {device.name}...")
    print(f"   TCP: {host}:{port}\n")
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"✓ Connected to {device.name}\n")
        
        # Send app information immediately after connecting
        await send_app_info(writer)
        print()
        
        print("👂 Listening for messages...")
        print("Press Ctrl+C to stop\n")
        
        # Read and handle messages
        await read_tcp_messages(reader, writer)
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused - is the device running?")
        return 1
    except OSError as e:
        print(f"❌ Connection error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        if 'writer' in locals():
            writer.close()
            await writer.wait_closed()
    
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
    print("OpenBikeControl TCP Trainer App Example")
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
