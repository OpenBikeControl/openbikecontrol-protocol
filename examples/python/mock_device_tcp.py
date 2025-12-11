#!/usr/bin/env python3
"""
Mock TCP Device Simulator for Testing

This script simulates an OpenBikeControl device for testing the trainer app examples.
It implements the TCP protocol with binary data format as specified in MDNS.md.

This is useful for:
- Testing the example apps without physical devices
- Demonstrating the protocol behavior
- Development and debugging

Note: This is a simplified simulator for demonstration purposes only.
Real devices would have more complex state management and error handling.
"""

import asyncio
import time
from datetime import datetime

try:
    from zeroconf import ServiceInfo
    from zeroconf.asyncio import AsyncZeroconf
    import socket
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    print("Note: Install zeroconf for mDNS advertising: pip install zeroconf")

# Import shared protocol parsing functions
from protocol_parser import (
    encode_button_state,
    encode_device_status,
    parse_haptic_feedback,
    parse_app_info,
    MSG_TYPE_HAPTIC_FEEDBACK,
    MSG_TYPE_APP_INFO
)


class MockDevice:
    """Simulates an OpenBikeControl device."""
    
    def __init__(self):
        self.battery = 85
        self.connected_clients = set()
    
    def get_device_info(self):
        """Get device information for mDNS advertisement."""
        return {
            "version": "1",
            "id": "aabbccddeeff",
            "name": "Mock OpenBike Remote",
            "service-uuids": "d273f680-d548-419d-b9d1-fa0472345229",
            "manufacturer": "ExampleCorp",
            "model": "MC-100"
        }
    
    def simulate_button_press(self, button_id: int):
        """Simulate a button press and release."""
        # Button press
        press_msg = encode_button_state([(button_id, 0x01)])
        
        # Button release
        release_msg = encode_button_state([(button_id, 0x00)])
        
        return press_msg, release_msg
    
    def get_status_message(self):
        """Get device status message."""
        return encode_device_status(self.battery, True)


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                       device: MockDevice):
    """Handle TCP client connection."""
    addr = writer.get_extra_info('peername')
    print(f"✓ Client connected from {addr}")
    device.connected_clients.add(writer)
    
    try:
        # Send initial status
        writer.write(device.get_status_message())
        await writer.drain()
        
        # Simulate some button presses
        button_sequence = [
            (1.0, 0x01),  # Shift Up after 1s
            (2.0, 0x02),  # Shift Down after 2s
            (3.0, 0x14),  # Select after 3s
            (4.0, 0x20, 1),  # Emote: Wave (enum value 1) after 4s
            (5.0, 0x40, 0),  # Camera: View 1 (enum value 0) after 5s
        ]
        
        async def simulate_buttons():
            """Background task to simulate button presses."""
            for item in button_sequence:
                if len(item) == 2:
                    delay, button_id = item
                    analog_value = None
                else:
                    delay, button_id, analog_value = item
                
                await asyncio.sleep(delay)
                if writer.is_closing():
                    break
                
                if analog_value is not None:
                    # Analog/enum button - send analog value directly
                    msg = encode_button_state([(button_id, analog_value)])
                    writer.write(msg)
                    await writer.drain()
                    print(f"  → Sent analog/enum button: 0x{button_id:02X} = {analog_value}")
                else:
                    # Digital button - press and release
                    press_msg, release_msg = device.simulate_button_press(button_id)
                    
                    # Send press
                    writer.write(press_msg)
                    await writer.drain()
                    print(f"  → Sent button press: 0x{button_id:02X}")
                    
                    # Wait a bit
                    await asyncio.sleep(0.1)
                    
                    # Send release
                    writer.write(release_msg)
                    await writer.drain()
                    print(f"  → Sent button release: 0x{button_id:02X}")
        
        # Start button simulation
        button_task = asyncio.create_task(simulate_buttons())
        
        # Handle incoming messages
        while True:
            # Read message type byte
            msg_type_data = await reader.read(1)
            if not msg_type_data:
                break  # Connection closed
            
            msg_type = msg_type_data[0]
            
            if msg_type == MSG_TYPE_HAPTIC_FEEDBACK:
                # Haptic feedback message - fixed 3 more bytes
                haptic_data = await reader.read(3)
                if len(haptic_data) < 3:
                    break
                
                full_message = msg_type_data + haptic_data
                try:
                    haptic_info = parse_haptic_feedback(full_message)
                    pattern = haptic_info["pattern"]
                    print(f"  ← Received haptic feedback: {pattern}")
                except Exception as e:
                    print(f"  ⚠ Failed to parse haptic feedback: {e}")
            
            elif msg_type == MSG_TYPE_APP_INFO:
                # App info message - variable length
                # Read the rest of the message
                # First, read version and lengths to determine total size
                header = await reader.read(3)  # version, app_id_len, first byte of app_id or app_id_len value
                if len(header) < 2:
                    break
                
                version = header[0]
                app_id_len = header[1]
                
                # Read the rest based on lengths
                remaining = await reader.read(app_id_len + 1 + 32 + 1 + 255)  # Over-read to get everything
                
                # Reconstruct full message
                full_message = msg_type_data + header + remaining
                
                try:
                    app_info = parse_app_info(full_message)
                    app_id = app_info["app_id"]
                    app_version = app_info["app_version"]
                    supported_buttons = app_info["supported_buttons"]
                    
                    print(f"  ← Received app info:")
                    print(f"     App ID: {app_id}")
                    print(f"     Version: {app_version}")
                    print(f"     Supported buttons: {len(supported_buttons)} types")
                    if supported_buttons:
                        button_ids = ", ".join(f"0x{btn:02X}" for btn in supported_buttons[:10])
                        if len(supported_buttons) > 10:
                            button_ids += f", ... ({len(supported_buttons) - 10} more)"
                        print(f"     Button IDs: {button_ids}")
                except Exception as e:
                    print(f"  ⚠ Failed to parse app info: {e}")
            
            else:
                print(f"  ← Received unknown message type: 0x{msg_type:02X}")
                # Skip unknown message
                await reader.read(64)
    
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"  ⚠ Error handling client: {e}")
    finally:
        # Cleanup
        if 'button_task' in locals():
            button_task.cancel()
            try:
                await button_task
            except asyncio.CancelledError:
                pass
        
        device.connected_clients.discard(writer)
        writer.close()
        await writer.wait_closed()
        print(f"✗ Client disconnected from {addr}")


async def start_tcp_server(device: MockDevice, host='0.0.0.0', port=8080):
    """Start TCP server for client connections."""
    
    async def client_connected(reader, writer):
        await handle_client(reader, writer, device)
    
    server = await asyncio.start_server(client_connected, host, port)
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f"  TCP server listening on {addrs}")
    
    return server


async def start_mock_server(host='0.0.0.0', port=8080):
    """Start mock TCP server with zeroconf advertising."""
    device = MockDevice()
    device_info = device.get_device_info()
    
    # Start TCP server
    server = await start_tcp_server(device, host, port)
    
    # Set up zeroconf service advertising
    aiozc = None
    service_info = None
    
    if ZEROCONF_AVAILABLE:
        try:
            # Get local IP address for advertising
            hostname = socket.gethostname()
            if host == '0.0.0.0':
                local_ip = socket.gethostbyname(hostname)
            else:
                local_ip = host
            
            # Create service info according to MDNS.md specification
            service_type = "_openbikecontrol._tcp.local."
            service_name = f"{device_info['name']}.{service_type}"
            
            # Prepare TXT record properties
            properties = {
                'version': device_info['version'],
                'id': device_info['id'],
                'name': device_info['name'],
                'service-uuids': device_info['service-uuids'],
                'manufacturer': device_info['manufacturer'],
                'model': device_info['model']
            }
            
            # Convert IP address to bytes
            addresses = [socket.inet_aton(local_ip)]
            
            # Create and register service
            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=addresses,
                port=port,
                properties=properties,
                server=f"{hostname}.local."
            )
            
            aiozc = AsyncZeroconf()
            await aiozc.async_register_service(service_info)
            
            print("=" * 60)
            print("Mock OpenBikeControl Device - TCP Server")
            print("=" * 60)
            print()
            print(f"Device: {device_info['name']}")
            print(f"Model: {device_info['manufacturer']} {device_info['model']}")
            print(f"ID: {device_info['id']}")
            print()
            print(f"TCP Address: {local_ip}:{port}")
            print()
            print("✓ mDNS service advertising enabled")
            print(f"  Service: {service_name}")
            print(f"  Type: {service_type}")
            print(f"  Address: {local_ip}:{port}")
            print()
        except Exception as e:
            print("=" * 60)
            print("Mock OpenBikeControl Device - TCP Server")
            print("=" * 60)
            print()
            print(f"Device: {device_info['name']}")
            print(f"Model: {device_info['manufacturer']} {device_info['model']}")
            print(f"ID: {device_info['id']}")
            print()
            print(f"TCP Address: {host}:{port}")
            print()
            print(f"⚠ Failed to advertise via mDNS: {e}")
            print("  TCP server is still running for direct connections.")
            print()
    else:
        print("=" * 60)
        print("Mock OpenBikeControl Device - TCP Server")
        print("=" * 60)
        print()
        print(f"Device: {device_info['name']}")
        print(f"Model: {device_info['manufacturer']} {device_info['model']}")
        print(f"ID: {device_info['id']}")
        print()
        print(f"TCP Address: {host}:{port}")
        print()
        print("Note: For mDNS discovery, install zeroconf: pip install zeroconf")
        print("      The TCP endpoint is available for direct connection.")
        print()
    
    print("The device will simulate button presses when a client connects:")
    print("  1s: Shift Up (0x01)")
    print("  2s: Shift Down (0x02)")
    print("  3s: Select (0x14)")
    print("  4s: Emote = Wave (0x20, enum value 1)")
    print("  5s: Camera = View 1 (0x40, enum value 0)")
    print()
    print("Connect using the TCP trainer app:")
    print("  python tcp_trainer_app.py")
    print("  or: python mdns_trainer_app.py")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Keep running
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping server...")
    finally:
        # Cleanup zeroconf service
        if aiozc and service_info:
            try:
                await aiozc.async_unregister_service(service_info)
                await aiozc.async_close()
                print("✓ mDNS service unregistered")
            except Exception as e:
                print(f"⚠ Error unregistering mDNS service: {e}")
        
        server.close()
        await server.wait_closed()


def print_usage():
    """Print usage information."""
    print("=" * 60)
    print("Mock OpenBikeControl Device Simulator (TCP)")
    print("=" * 60)
    print()
    print("This script simulates an OpenBikeControl device for testing.")
    print()
    print("Usage:")
    print("  python mock_device_tcp.py")
    print()
    print("The mock device will:")
    print("  - Start a TCP server on port 8080")
    print("  - Advertise via mDNS/zeroconf (if zeroconf is installed)")
    print("  - Accept connections from trainer apps")
    print("  - Simulate button presses automatically")
    print("  - Respond to haptic feedback commands")
    print()
    print("Requirements:")
    print("  pip install zeroconf")
    print()


if __name__ == "__main__":
    print_usage()
    
    try:
        asyncio.run(start_mock_server())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
