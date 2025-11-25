#!/usr/bin/env python3
"""
Mock BLE Device Simulator for Testing

This script simulates an OpenBikeControl BLE device for testing the BLE trainer app.
It can simulate BLE advertisement, services, characteristics, and button presses
without requiring actual hardware.

This is useful for:
- Testing the BLE trainer app without physical devices
- Demonstrating the BLE protocol behavior
- Development and debugging

Platform Support:
- Windows 10+ (build 1709 or later)
- macOS 10.15+
- Linux (with BlueZ 5.43+)

Note: This is a simplified simulator for demonstration purposes only.
Real devices would have more complex state management and error handling.
"""

import asyncio
import struct
import sys
from typing import Optional

try:
    from bless import (
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
    )
    BLESS_AVAILABLE = True
except ImportError:
    BLESS_AVAILABLE = False
    print("Note: Install bless for cross-platform BLE peripheral simulation")
    print("      pip install git+https://github.com/x42en/bless.git@master")

# Import shared protocol parsing functions
from protocol_parser import (
    encode_button_state,
    parse_haptic_feedback,
    parse_app_info
)


# OpenBikeControl Service and Characteristic UUIDs (from BLE.md)
SERVICE_UUID = "d273f680-d548-419d-b9d1-fa0472345229"
BUTTON_STATE_CHAR_UUID = "d273f681-d548-419d-b9d1-fa0472345229"
HAPTIC_FEEDBACK_CHAR_UUID = "d273f682-d548-419d-b9d1-fa0472345229"
APP_INFO_CHAR_UUID = "d273f683-d548-419d-b9d1-fa0472345229"

# Standard BLE Service UUIDs
DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"

# Device Information Service Characteristics
MANUFACTURER_NAME_CHAR_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHAR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHAR_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
HARDWARE_REV_CHAR_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
FIRMWARE_REV_CHAR_UUID = "00002a26-0000-1000-8000-00805f9b34fb"

# Battery Service Characteristics
BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"


class MockBLEDevice:
    """Simulates an OpenBikeControl BLE device using the bless library."""

    def __init__(self, name: str = "OpenBike"):
        self.name = name
        self.battery = 85
        self.button_simulation_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Device information
        self.manufacturer = "ExampleCorp"
        self.model = "MC-100"
        self.serial = "1234567890"
        self.hardware_rev = "1.0"
        self.firmware_rev = "1.0.0"

        # BLE server
        self.server: Optional[BlessServer] = None
        self._button_state_value = bytes([0x00, 0x00])

    def get_device_info(self):
        """Get device information."""
        return {
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial": self.serial,
            "hardware_rev": self.hardware_rev,
            "firmware_rev": self.firmware_rev,
            "battery": self.battery
        }

    def _haptic_write_callback(self, characteristic, value: bytes):
        """Handle haptic feedback writes."""
        try:
            haptic_info = parse_haptic_feedback(value)
            pattern = haptic_info["pattern"]
            duration = haptic_info["duration"]
            intensity = haptic_info["intensity"]
            
            print(f"  ← Received haptic feedback: pattern={pattern}, "
                  f"duration={duration}×10ms, intensity={intensity}")
        except Exception as e:
            print(f"  ⚠ Failed to parse haptic feedback: {e}")

    def _app_info_write_callback(self, characteristic, value: bytes):
        """Handle app info writes."""
        try:
            app_info = parse_app_info(value)
            app_id = app_info["app_id"]
            app_version = app_info["app_version"]
            button_ids = app_info["supported_buttons"]
            
            print(f"  ← Received app info:")
            print(f"     App ID: {app_id}")
            print(f"     Version: {app_version}")
            print(f"     Supported buttons: {len(button_ids)} types")
            if button_ids:
                button_id_str = ", ".join(f"0x{btn:02X}" for btn in button_ids[:10])
                if len(button_ids) > 10:
                    button_id_str += f", ... ({len(button_ids) - 10} more)"
                print(f"     Button IDs: {button_id_str}")
        except Exception as e:
            print(f"  ⚠ Error parsing app info: {e}")

    def _write_callback_router(self, characteristic, value: bytes):
        """Route write requests to appropriate handlers."""
        char_uuid = str(characteristic.uuid).lower()
        
        if HAPTIC_FEEDBACK_CHAR_UUID.lower() in char_uuid:
            self._haptic_write_callback(characteristic, value)
        elif APP_INFO_CHAR_UUID.lower() in char_uuid:
            self._app_info_write_callback(characteristic, value)
        else:
            print(f"  ← Received write to unknown characteristic: {characteristic.uuid}")


    async def setup_ble_server(self):
        """Set up the BLE GATT server with all required services and characteristics."""
        if not BLESS_AVAILABLE:
            raise RuntimeError("bless library is required for BLE simulation. "
                             "Install with: pip install git+https://github.com/x42en/bless.git@master")

        print(f"✓ Creating BLE server: {self.name}")

        # Create server
        self.server = BlessServer(name=self.name)

        # Set write callback router for all writable characteristics
        self.server.write_request_func = self._write_callback_router

        # Add OpenBikeControl Service
        await self.server.add_new_service(SERVICE_UUID)
        print(f"  Registered OpenBikeControl service: {SERVICE_UUID}")

        # Add Button State characteristic (READ/NOTIFY)
        await self.server.add_new_characteristic(
            SERVICE_UUID,
            BUTTON_STATE_CHAR_UUID,
            GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify,
            None,
            GATTAttributePermissions.readable
        )
        print(f"    - Button State (READ/NOTIFY): {BUTTON_STATE_CHAR_UUID}")

        # Add Haptic Feedback characteristic (WRITE)
        await self.server.add_new_characteristic(
            SERVICE_UUID,
            HAPTIC_FEEDBACK_CHAR_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )
        print(f"    - Haptic Feedback (WRITE): {HAPTIC_FEEDBACK_CHAR_UUID}")

        # Add App Information characteristic (WRITE)
        await self.server.add_new_characteristic(
            SERVICE_UUID,
            APP_INFO_CHAR_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )
        print(f"    - App Information (WRITE): {APP_INFO_CHAR_UUID}")

        # Add Device Information Service
        await self.server.add_new_service(DEVICE_INFO_SERVICE_UUID)
        print(f"  Registered Device Information service: {DEVICE_INFO_SERVICE_UUID}")

        # Add device info characteristics
        await self.server.add_new_characteristic(
            DEVICE_INFO_SERVICE_UUID,
            MANUFACTURER_NAME_CHAR_UUID,
            GATTCharacteristicProperties.read,
            self.manufacturer.encode('utf-8'),
            GATTAttributePermissions.readable
        )
        await self.server.add_new_characteristic(
            DEVICE_INFO_SERVICE_UUID,
            MODEL_NUMBER_CHAR_UUID,
            GATTCharacteristicProperties.read,
            self.model.encode('utf-8'),
            GATTAttributePermissions.readable
        )
        await self.server.add_new_characteristic(
            DEVICE_INFO_SERVICE_UUID,
            SERIAL_NUMBER_CHAR_UUID,
            GATTCharacteristicProperties.read,
            self.serial.encode('utf-8'),
            GATTAttributePermissions.readable
        )
        await self.server.add_new_characteristic(
            DEVICE_INFO_SERVICE_UUID,
            HARDWARE_REV_CHAR_UUID,
            GATTCharacteristicProperties.read,
            self.hardware_rev.encode('utf-8'),
            GATTAttributePermissions.readable
        )
        await self.server.add_new_characteristic(
            DEVICE_INFO_SERVICE_UUID,
            FIRMWARE_REV_CHAR_UUID,
            GATTCharacteristicProperties.read,
            self.firmware_rev.encode('utf-8'),
            GATTAttributePermissions.readable
        )

        # Add Battery Service
        await self.server.add_new_service(BATTERY_SERVICE_UUID)
        print(f"  Registered Battery service: {BATTERY_SERVICE_UUID}")

        # Add battery level characteristic
        await self.server.add_new_characteristic(
            BATTERY_SERVICE_UUID,
            BATTERY_LEVEL_CHAR_UUID,
            GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify,
            None,
            GATTAttributePermissions.readable
        )

        # Start the server
        await self.server.start(10, False)
        print(f"  Advertising with service UUID: {SERVICE_UUID}")

    async def update_button_state(self, button_id: int, state: int):
        """Update button state and notify clients."""
        if not self.server:
            return

        self._button_state_value = encode_button_state([(button_id, state)])
        self.server.get_characteristic(BUTTON_STATE_CHAR_UUID).value = self._button_state_value
        self.server.update_value(SERVICE_UUID, BUTTON_STATE_CHAR_UUID)

    async def simulate_button_press(self, button_id: int):
        """Simulate a button press and release with BLE notifications."""
        if not self.server:
            return

        # Button press
        await self.update_button_state(button_id, 0x01)
        print(f"  → Sent button press notification: 0x{button_id:02X}")

        # Wait a bit for press duration
        await asyncio.sleep(0.1)

        # Button release
        await self.update_button_state(button_id, 0x00)
        print(f"  → Sent button release notification: 0x{button_id:02X}")

    async def simulate_buttons_loop(self):
        """Background task to simulate button presses periodically."""
        # Button sequence to simulate
        button_sequence = [
            (3.0, 0x01),   # Shift Up after 3s
            (3.0, 0x02),   # Shift Down after 3s
            (3.0, 0x14),   # Select after 3s
            (3.0, 0x20),   # Wave after 3s
        ]

        print("\n👉 Starting button simulation...")
        print("   Buttons will be pressed every few seconds")

        while self.is_running:
            for delay, button_id in button_sequence:
                if not self.is_running:
                    break

                await asyncio.sleep(delay)

                if self.is_running:
                    await self.simulate_button_press(button_id)

    async def start(self):
        """Start the BLE device simulation."""
        self.is_running = True

        # Setup BLE server with services
        await self.setup_ble_server()

        # Start button simulation
        self.button_simulation_task = asyncio.create_task(self.simulate_buttons_loop())

        print("\n" + "=" * 60)
        print("Mock OpenBikeControl BLE Device - Running")
        print("=" * 60)
        print()
        print(f"Device Name: {self.name}")
        print(f"Manufacturer: {self.manufacturer}")
        print(f"Model: {self.model}")
        print(f"Serial: {self.serial}")
        print(f"Battery: {self.battery}%")
        print()
        print("Services and Characteristics:")
        print(f"  • OpenBikeControl Service: {SERVICE_UUID}")
        print(f"    - Button State (READ/NOTIFY): {BUTTON_STATE_CHAR_UUID}")
        print(f"    - Haptic Feedback (WRITE): {HAPTIC_FEEDBACK_CHAR_UUID}")
        print(f"  • Device Information Service: {DEVICE_INFO_SERVICE_UUID}")
        print(f"  • Battery Service: {BATTERY_SERVICE_UUID}")
        print()
        print("The device will simulate button presses:")
        print("  Every 3s: Shift Up (0x01)")
        print("  Every 3s: Shift Down (0x02)")
        print("  Every 3s: Select (0x14)")
        print("  Every 3s: Wave (0x20)")
        print()
        print("Connect using the BLE trainer app:")
        print("  python ble_trainer_app.py")
        print()
        print("Press Ctrl+C to stop")
        print()

    async def stop(self):
        """Stop the BLE device simulation."""
        print("\n\n⏹ Stopping BLE device...")
        self.is_running = False

        if self.button_simulation_task:
            self.button_simulation_task.cancel()
            try:
                await self.button_simulation_task
            except asyncio.CancelledError:
                pass

        if self.server:
            await self.server.stop()

        print("✓ BLE device stopped")


async def start_mock_ble_device():
    """Start the mock BLE device."""
    if not BLESS_AVAILABLE:
        print("❌ bless library is required for cross-platform BLE peripheral simulation")
        print("   Install with: pip install git+https://github.com/x42en/bless.git@master")
        print()
        print("   Note: The latest version of bless is compatible with bleak>=0.21.0")
        return

    device = MockBLEDevice()

    try:
        await device.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        await device.stop()


def print_usage():
    """Print usage information."""
    print("=" * 60)
    print("Mock OpenBikeControl BLE Device Simulator")
    print("=" * 60)
    print()
    print("This script simulates an OpenBikeControl BLE device for testing.")
    print()
    print("Usage:")
    print("  python mock_device_ble.py")
    print()
    print("The mock BLE device will:")
    print("  - Advertise as a BLE peripheral")
    print("  - Implement OpenBikeControl service and characteristics")
    print("  - Implement Device Information and Battery services")
    print("  - Accept connections from trainer apps")
    print("  - Simulate button presses automatically")
    print("  - Respond to haptic feedback commands")
    print()
    print("Requirements:")
    print("  pip install git+https://github.com/x42en/bless.git@master")
    print()
    print("Platform Support:")
    print("  - Windows 10+ (build 1709 or later)")
    print("  - macOS 10.15+ (Catalina or later)")
    print("  - Linux (with BlueZ 5.43+)")
    print()
    print("Note: The latest version of bless is compatible with bleak>=0.21.0,")
    print("      so you can now run both the mock device and the BLE client app")
    print("      in the same environment without version conflicts.")
    print()


if __name__ == "__main__":
    print_usage()

    if not BLESS_AVAILABLE:
        sys.exit(1)

    try:
        asyncio.run(start_mock_ble_device())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
