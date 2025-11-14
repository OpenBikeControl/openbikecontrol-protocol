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

Note: This is a simplified simulator for demonstration purposes only.
Real devices would have more complex state management and error handling.
"""

import asyncio
import struct
import time
from typing import Any

try:
    from bluez_peripheral.gatt.service import Service
    from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
    from bluez_peripheral.advert import Advertisement
    from bluez_peripheral.util import *
    BLUEZ_AVAILABLE = True
except ImportError:
    BLUEZ_AVAILABLE = False
    print("Note: Install bluez-peripheral for BLE peripheral simulation: pip install bluez-peripheral")


# OpenBikeControl Service and Characteristic UUIDs (from BLE.md)
SERVICE_UUID = "d273f680-d548-419d-b9d1-fa0472345229"
BUTTON_STATE_CHAR_UUID = "d273f681-d548-419d-b9d1-fa0472345229"
HAPTIC_FEEDBACK_CHAR_UUID = "d273f682-d548-419d-b9d1-fa0472345229"

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


class OpenBikeControlService(Service):
    """OpenBikeControl BLE GATT Service implementation."""
    
    def __init__(self):
        super().__init__(SERVICE_UUID, True)
        self._button_state_value = bytes([0x00, 0x00])
    
    @characteristic(BUTTON_STATE_CHAR_UUID, CharFlags.READ | CharFlags.NOTIFY)
    def button_state(self, options):
        """Button State characteristic (READ/NOTIFY)."""
        return self._button_state_value
    
    @characteristic(HAPTIC_FEEDBACK_CHAR_UUID, CharFlags.WRITE | CharFlags.WRITE_WITHOUT_RESPONSE)
    def haptic_feedback(self, options):
        """Haptic Feedback characteristic (WRITE)."""
        pass
    
    @haptic_feedback.setter
    def haptic_feedback(self, value, options):
        """Handle haptic feedback writes."""
        if len(value) >= 3:
            pattern = value[0]
            duration = value[1]
            intensity = value[2]
            
            pattern_names = {
                0x00: "none",
                0x01: "short",
                0x02: "double",
                0x03: "triple",
                0x04: "long",
                0x05: "success",
                0x06: "warning",
                0x07: "error"
            }
            pattern_name = pattern_names.get(pattern, f"0x{pattern:02X}")
            
            print(f"  ← Received haptic feedback: pattern={pattern_name}, "
                  f"duration={duration}×10ms, intensity={intensity}")
    
    def update_button_state(self, button_id: int, state: int):
        """Update button state and notify clients."""
        self._button_state_value = struct.pack('<BB', button_id, state)
        self.button_state.changed(self._button_state_value)


class DeviceInformationService(Service):
    """Device Information BLE GATT Service."""
    
    def __init__(self, manufacturer: str, model: str, serial: str, hw_rev: str, fw_rev: str):
        super().__init__(DEVICE_INFO_SERVICE_UUID, True)
        self._manufacturer = manufacturer.encode('utf-8')
        self._model = model.encode('utf-8')
        self._serial = serial.encode('utf-8')
        self._hw_rev = hw_rev.encode('utf-8')
        self._fw_rev = fw_rev.encode('utf-8')
    
    @characteristic(MANUFACTURER_NAME_CHAR_UUID, CharFlags.READ)
    def manufacturer_name(self, options):
        return self._manufacturer
    
    @characteristic(MODEL_NUMBER_CHAR_UUID, CharFlags.READ)
    def model_number(self, options):
        return self._model
    
    @characteristic(SERIAL_NUMBER_CHAR_UUID, CharFlags.READ)
    def serial_number(self, options):
        return self._serial
    
    @characteristic(HARDWARE_REV_CHAR_UUID, CharFlags.READ)
    def hardware_revision(self, options):
        return self._hw_rev
    
    @characteristic(FIRMWARE_REV_CHAR_UUID, CharFlags.READ)
    def firmware_revision(self, options):
        return self._fw_rev


class BatteryService(Service):
    """Battery BLE GATT Service."""
    
    def __init__(self, battery_level: int = 85):
        super().__init__(BATTERY_SERVICE_UUID, True)
        self._battery_level = battery_level
    
    @characteristic(BATTERY_LEVEL_CHAR_UUID, CharFlags.READ | CharFlags.NOTIFY)
    def battery_level(self, options):
        return struct.pack('<B', self._battery_level)


class MockBLEDevice:
    """Simulates an OpenBikeControl BLE device."""
    
    def __init__(self, name: str = "Mock OpenBike Remote"):
        self.name = name
        self.battery = 85
        self.button_simulation_task = None
        self.is_running = False
        
        # Device information
        self.manufacturer = "ExampleCorp"
        self.model = "MC-100"
        self.serial = "1234567890"
        self.hardware_rev = "1.0"
        self.firmware_rev = "1.0.0"
        
        # Services
        self.obc_service = None
        self.device_info_service = None
        self.battery_service = None
        self.adapter = None
        self.advertisement = None
    
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
    
    async def setup_ble_server(self):
        """Set up the BLE GATT server with all required services and characteristics."""
        if not BLUEZ_AVAILABLE:
            raise RuntimeError("bluez-peripheral library is required for BLE simulation")
        
        # Get the Bluetooth adapter
        self.adapter = await Adapter.get_first()
        
        # Set adapter alias (device name)
        await self.adapter.set_alias(self.name)
        
        print(f"✓ BLE adapter configured: {self.name}")
        
        # Create services
        self.obc_service = OpenBikeControlService()
        self.device_info_service = DeviceInformationService(
            self.manufacturer, self.model, self.serial,
            self.hardware_rev, self.firmware_rev
        )
        self.battery_service = BatteryService(self.battery)
        
        # Register services
        await self.obc_service.register(self.adapter)
        print(f"  Registered OpenBikeControl service: {SERVICE_UUID}")
        
        await self.device_info_service.register(self.adapter)
        print(f"  Registered Device Information service: {DEVICE_INFO_SERVICE_UUID}")
        
        await self.battery_service.register(self.adapter)
        print(f"  Registered Battery service: {BATTERY_SERVICE_UUID}")
        
        # Create and start advertisement
        self.advertisement = Advertisement(
            self.name,
            [SERVICE_UUID],  # Advertise OpenBikeControl service UUID
            0x0340,  # Appearance: Generic Remote Control
            60  # Timeout in seconds (0 = no timeout)
        )
        
        await self.advertisement.register(self.adapter)
        print(f"  Advertising with service UUID: {SERVICE_UUID}")
    
    async def simulate_button_press(self, button_id: int):
        """Simulate a button press and release with BLE notifications."""
        if not self.obc_service:
            return
        
        # Button press
        self.obc_service.update_button_state(button_id, 0x01)
        print(f"  → Sent button press notification: 0x{button_id:02X}")
        
        # Wait a bit for press duration
        await asyncio.sleep(0.1)
        
        # Button release
        self.obc_service.update_button_state(button_id, 0x00)
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
        
        if self.advertisement:
            await self.advertisement.unregister()
        
        if self.obc_service:
            await self.obc_service.unregister()
        
        if self.device_info_service:
            await self.device_info_service.unregister()
        
        if self.battery_service:
            await self.battery_service.unregister()
        
        print("✓ BLE device stopped")


async def start_mock_ble_device():
    """Start the mock BLE device."""
    if not BLUEZ_AVAILABLE:
        print("❌ bluez-peripheral library is required for BLE peripheral simulation")
        print("   Install with: pip install bluez-peripheral")
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
    print("  pip install bluez-peripheral bleak")
    print()
    print("Note: BLE peripheral functionality requires:")
    print("  - Linux: BlueZ 5.43+ and appropriate permissions")
    print("    Run with: sudo python mock_device_ble.py")
    print("  - macOS: Limited support, may not work")
    print("  - Windows: Not supported (BlueZ required)")
    print()


if __name__ == "__main__":
    print_usage()
    
    if not BLUEZ_AVAILABLE:
        import sys
        sys.exit(1)
    
    try:
        asyncio.run(start_mock_ble_device())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
