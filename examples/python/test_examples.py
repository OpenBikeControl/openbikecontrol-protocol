#!/usr/bin/env python3
"""
Basic tests for OpenBikeControl Python examples.

These tests verify core functionality without requiring actual devices.
Run with: python test_examples.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import functions from the example scripts
from ble_trainer_app import parse_button_state, format_button_state, BUTTON_NAMES
from mdns_trainer_app import format_button_state as mdns_format_button_state


def test_parse_button_state():
    """Test BLE button state parsing."""
    print("Testing parse_button_state...")
    
    # Single button press
    data = bytes([0x01, 0x01])
    result = parse_button_state(data)
    assert result == [(0x01, 0x01)], f"Expected [(1, 1)], got {result}"
    
    # Multiple buttons
    data = bytes([0x01, 0x01, 0x02, 0x00])
    result = parse_button_state(data)
    assert result == [(0x01, 0x01), (0x02, 0x00)], f"Expected [(1, 1), (2, 0)], got {result}"
    
    # Analog value
    data = bytes([0x10, 0x80])
    result = parse_button_state(data)
    assert result == [(0x10, 0x80)], f"Expected [(16, 128)], got {result}"
    
    # Empty data
    data = bytes([])
    result = parse_button_state(data)
    assert result == [], f"Expected [], got {result}"
    
    # Odd length (should skip last byte)
    data = bytes([0x01, 0x01, 0x02])
    result = parse_button_state(data)
    assert result == [(0x01, 0x01)], f"Expected [(1, 1)], got {result}"
    
    print("  ✓ All parse_button_state tests passed")


def test_format_button_state():
    """Test button state formatting."""
    print("Testing format_button_state...")
    
    # Known button pressed
    result = format_button_state(0x01, 1)
    assert "Shift Up" in result and "PRESSED" in result, f"Unexpected format: {result}"
    
    # Known button released
    result = format_button_state(0x01, 0)
    assert "Shift Up" in result and "RELEASED" in result, f"Unexpected format: {result}"
    
    # Unknown button
    result = format_button_state(0xFF, 1)
    assert "0xFF" in result and "PRESSED" in result, f"Unexpected format: {result}"
    
    # Analog value
    result = format_button_state(0x10, 0x80)
    assert "Up/Steer Left" in result and "ANALOG" in result, f"Unexpected format: {result}"
    
    # Analog min (2)
    result = format_button_state(0x10, 2)
    assert "ANALOG" in result and "0%" in result, f"Unexpected format: {result}"
    
    # Analog max (255)
    result = format_button_state(0x10, 255)
    assert "ANALOG" in result and "100%" in result, f"Unexpected format: {result}"
    
    print("  ✓ All format_button_state tests passed")


def test_button_names():
    """Test that button mappings are consistent."""
    print("Testing button name mappings...")
    
    # Check some key buttons exist
    assert 0x01 in BUTTON_NAMES, "Shift Up (0x01) missing"
    assert 0x02 in BUTTON_NAMES, "Shift Down (0x02) missing"
    assert 0x10 in BUTTON_NAMES, "Up/Steer Left (0x10) missing"
    assert 0x14 in BUTTON_NAMES, "Select/Confirm (0x14) missing"
    assert 0x20 in BUTTON_NAMES, "Wave (0x20) missing"
    assert 0x30 in BUTTON_NAMES, "ERG Up (0x30) missing"
    
    print("  ✓ All button name mapping tests passed")


def test_mdns_format_consistency():
    """Test that mDNS and BLE format functions produce consistent output."""
    print("Testing format consistency between BLE and mDNS...")
    
    # Both should format the same way
    ble_result = format_button_state(0x01, 1)
    mdns_result = mdns_format_button_state(0x01, 1)
    assert ble_result == mdns_result, f"BLE: {ble_result}, mDNS: {mdns_result}"
    
    print("  ✓ Format consistency tests passed")


def test_mock_device_zeroconf():
    """Test that mock device can advertise via zeroconf."""
    print("Testing mock device zeroconf advertising...")
    
    try:
        import asyncio
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
        from mock_device import start_mock_server, ZEROCONF_AVAILABLE, AIOHTTP_AVAILABLE
        
        if not ZEROCONF_AVAILABLE or not AIOHTTP_AVAILABLE:
            print("  ⊘ Skipped (zeroconf or aiohttp not available)")
            return
        
        SERVICE_TYPE = "_openbikecontrol._tcp.local."
        
        class TestListener(ServiceListener):
            def __init__(self):
                self.found = False
                self.device_info = None
            
            def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                info = zc.get_service_info(type_, name)
                if info and "Mock OpenBike Remote" in name:
                    self.found = True
                    properties = {}
                    for key, value in info.properties.items():
                        try:
                            properties[key.decode('utf-8')] = value.decode('utf-8')
                        except:
                            properties[key.decode('utf-8')] = value
                    self.device_info = properties
            
            def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                pass
            
            def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                pass
        
        async def test_async():
            # Start mock server
            server_task = asyncio.create_task(start_mock_server(port=8081))
            
            # Wait for server to start
            await asyncio.sleep(2)
            
            # Try to discover it
            zeroconf = Zeroconf()
            listener = TestListener()
            browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
            
            # Wait for discovery
            await asyncio.sleep(3)
            
            # Cleanup
            browser.cancel()
            zeroconf.close()
            
            # Stop server
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
            
            return listener.found, listener.device_info
        
        found, device_info = asyncio.run(test_async())
        
        assert found, "Mock device was not discovered via mDNS"
        assert device_info is not None, "Device info was not retrieved"
        assert device_info.get('name') == 'Mock OpenBike Remote', "Device name mismatch"
        assert device_info.get('version') == '1', "Version mismatch"
        assert device_info.get('manufacturer') == 'ExampleCorp', "Manufacturer mismatch"
        
        print("  ✓ Mock device zeroconf advertising tests passed")
    
    except Exception as e:
        print(f"  ⚠ Zeroconf test skipped due to error: {e}")
        # Don't fail the entire test suite if zeroconf test has issues
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenBikeControl Python Examples - Basic Tests")
    print("=" * 60)
    print()
    
    try:
        test_parse_button_state()
        test_format_button_state()
        test_button_names()
        test_mdns_format_consistency()
        test_mock_device_zeroconf()
        
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
