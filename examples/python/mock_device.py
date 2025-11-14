#!/usr/bin/env python3
"""
Mock Device Simulator for Testing

This script simulates an OpenBikeControl device for testing the trainer app examples.
It can simulate both BLE and mDNS protocols without requiring actual hardware.

This is useful for:
- Testing the example apps without physical devices
- Demonstrating the protocol behavior
- Development and debugging

Note: This is a simplified simulator for demonstration purposes only.
Real devices would have more complex state management and error handling.
"""

import asyncio
import json
import time
from datetime import datetime

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Note: Install aiohttp for WebSocket simulation: pip install aiohttp")


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
            "ble-service-uuids": "d273f680-d548-419d-b9d1-fa0472345229",
            "manufacturer": "ExampleCorp",
            "model": "MC-100"
        }
    
    def simulate_button_press(self, button_id: int):
        """Simulate a button press and release."""
        timestamp = int(time.time() * 1000)
        
        # Button press
        press_msg = {
            "type": "button_state",
            "timestamp": timestamp,
            "buttons": [{"id": button_id, "state": 1}]
        }
        
        # Button release (100ms later)
        release_msg = {
            "type": "button_state",
            "timestamp": timestamp + 100,
            "buttons": [{"id": button_id, "state": 0}]
        }
        
        return press_msg, release_msg
    
    def get_status_message(self):
        """Get device status message."""
        return {
            "type": "device_status",
            "timestamp": int(time.time() * 1000),
            "battery": self.battery,
            "connected": True
        }


async def websocket_handler(request):
    """Handle WebSocket connections from trainer apps."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    device = request.app['device']
    device.connected_clients.add(ws)
    print(f"✓ Client connected from {request.remote}")
    
    # Send initial status
    await ws.send_str(json.dumps(device.get_status_message()))
    
    # Simulate some button presses
    button_sequence = [
        (1.0, 0x01),  # Shift Up after 1s
        (2.0, 0x02),  # Shift Down after 2s
        (3.0, 0x14),  # Select after 3s
        (4.0, 0x20),  # Wave after 4s
    ]
    
    async def simulate_buttons():
        """Background task to simulate button presses."""
        for delay, button_id in button_sequence:
            await asyncio.sleep(delay)
            if ws.closed:
                break
            
            press_msg, release_msg = device.simulate_button_press(button_id)
            
            # Send press
            await ws.send_str(json.dumps(press_msg))
            print(f"  → Sent button press: 0x{button_id:02X}")
            
            # Wait a bit
            await asyncio.sleep(0.1)
            
            # Send release
            await ws.send_str(json.dumps(release_msg))
            print(f"  → Sent button release: 0x{button_id:02X}")
    
    # Start button simulation
    button_task = asyncio.create_task(simulate_buttons())
    
    # Handle incoming messages
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                msg_type = data.get("type")
                
                if msg_type == "haptic_feedback":
                    # Acknowledge haptic feedback
                    pattern = data.get("pattern", "unknown")
                    print(f"  ← Received haptic feedback: {pattern}")
                    
                    response = {
                        "type": "haptic_feedback_response",
                        "timestamp": int(time.time() * 1000),
                        "success": True
                    }
                    await ws.send_str(json.dumps(response))
                else:
                    print(f"  ← Received unknown message type: {msg_type}")
            
            except json.JSONDecodeError:
                print(f"  ⚠ Failed to parse message: {msg.data}")
        
        elif msg.type == web.WSMsgType.ERROR:
            print(f"  ⚠ WebSocket error: {ws.exception()}")
    
    # Cleanup
    button_task.cancel()
    device.connected_clients.discard(ws)
    print(f"✗ Client disconnected")
    
    return ws


async def start_mock_server(host='0.0.0.0', port=8080):
    """Start mock mDNS/WebSocket server."""
    if not AIOHTTP_AVAILABLE:
        print("❌ aiohttp is required for the mock server")
        print("   Install with: pip install aiohttp")
        return
    
    app = web.Application()
    app['device'] = MockDevice()
    app.router.add_get('/api/ws', websocket_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    device_info = app['device'].get_device_info()
    
    print("=" * 60)
    print("Mock OpenBikeControl Device - WebSocket Server")
    print("=" * 60)
    print()
    print(f"Device: {device_info['name']}")
    print(f"Model: {device_info['manufacturer']} {device_info['model']}")
    print(f"ID: {device_info['id']}")
    print()
    print(f"WebSocket URL: ws://{host}:{port}/api/ws")
    print()
    print("The device will simulate button presses when a client connects:")
    print("  1s: Shift Up (0x01)")
    print("  2s: Shift Down (0x02)")
    print("  3s: Select (0x14)")
    print("  4s: Wave (0x20)")
    print()
    print("Connect using the mDNS trainer app:")
    print("  python mdns_trainer_app.py")
    print()
    print("Note: For full mDNS discovery, you would need to advertise")
    print("      the service using zeroconf. This example only provides")
    print("      the WebSocket endpoint for direct connection testing.")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping server...")
    finally:
        await runner.cleanup()


def print_usage():
    """Print usage information."""
    print("=" * 60)
    print("Mock OpenBikeControl Device Simulator")
    print("=" * 60)
    print()
    print("This script simulates an OpenBikeControl device for testing.")
    print()
    print("Usage:")
    print("  python mock_device.py")
    print()
    print("The mock device will:")
    print("  - Start a WebSocket server on port 8080")
    print("  - Accept connections from trainer apps")
    print("  - Simulate button presses automatically")
    print("  - Respond to haptic feedback commands")
    print()
    print("Requirements:")
    print("  pip install aiohttp")
    print()


if __name__ == "__main__":
    print_usage()
    
    if not AIOHTTP_AVAILABLE:
        import sys
        sys.exit(1)
    
    try:
        asyncio.run(start_mock_server())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
