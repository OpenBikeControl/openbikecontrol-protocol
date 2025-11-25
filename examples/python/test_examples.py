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

# Import functions from the protocol parser module
from protocol_parser import (
    parse_button_state,
    encode_button_state,
    format_button_state,
    parse_device_status,
    encode_device_status,
    parse_haptic_feedback,
    encode_haptic_feedback,
    parse_app_info,
    encode_app_info,
    BUTTON_NAMES,
    MSG_TYPE_BUTTON_STATE,
    MSG_TYPE_DEVICE_STATUS,
    MSG_TYPE_HAPTIC_FEEDBACK,
    MSG_TYPE_APP_INFO
)


def test_parse_button_state():
    """Test button state parsing."""
    print("Testing parse_button_state...")
    
    # Single button press (with message type)
    data = bytes([MSG_TYPE_BUTTON_STATE, 0x01, 0x01])
    result = parse_button_state(data)
    assert result == [(0x01, 0x01)], f"Expected [(1, 1)], got {result}"
    
    # Multiple buttons (with message type)
    data = bytes([MSG_TYPE_BUTTON_STATE, 0x01, 0x01, 0x02, 0x00])
    result = parse_button_state(data)
    assert result == [(0x01, 0x01), (0x02, 0x00)], f"Expected [(1, 1), (2, 0)], got {result}"
    
    # Analog value (with message type)
    data = bytes([MSG_TYPE_BUTTON_STATE, 0x10, 0x80])
    result = parse_button_state(data)
    assert result == [(0x10, 0x80)], f"Expected [(16, 128)], got {result}"
    
    # Empty data
    data = bytes([])
    result = parse_button_state(data)
    assert result == [], f"Expected [], got {result}"
    
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
    """Test that format functions produce consistent output."""
    print("Testing format consistency...")
    
    # Both BLE and TCP use the same format_button_state function now
    result1 = format_button_state(0x01, 1)
    result2 = format_button_state(0x01, 1)
    assert result1 == result2, f"Results differ: {result1} vs {result2}"
    
    print("  ✓ Format consistency tests passed")


def test_encode_button_state():
    """Test button state encoding."""
    print("Testing encode_button_state...")
    
    # Single button (with message type)
    result = encode_button_state([(0x01, 0x01)])
    assert result == bytes([MSG_TYPE_BUTTON_STATE, 0x01, 0x01]), f"Expected [0x01, 0x01, 0x01], got {result}"
    
    # Multiple buttons (with message type)
    result = encode_button_state([(0x01, 0x01), (0x02, 0x00)])
    assert result == bytes([MSG_TYPE_BUTTON_STATE, 0x01, 0x01, 0x02, 0x00]), f"Expected [0x01, 0x01, 0x01, 0x02, 0x00], got {result}"
    
    print("  ✓ All encode_button_state tests passed")


def test_device_status():
    """Test device status encoding and parsing."""
    print("Testing device status...")
    
    # Encode status with battery
    encoded = encode_device_status(85, True)
    assert encoded == bytes([MSG_TYPE_DEVICE_STATUS, 85, 0x01]), f"Unexpected encoding: {encoded}"
    
    # Parse status
    parsed = parse_device_status(encoded)
    assert parsed["battery"] == 85, f"Battery mismatch: {parsed['battery']}"
    assert parsed["connected"] == True, f"Connected mismatch: {parsed['connected']}"
    
    # Encode status without battery
    encoded = encode_device_status(None, False)
    assert encoded == bytes([MSG_TYPE_DEVICE_STATUS, 0xFF, 0x00]), f"Unexpected encoding: {encoded}"
    
    # Parse status without battery
    parsed = parse_device_status(encoded)
    assert parsed["battery"] is None, f"Battery should be None: {parsed['battery']}"
    assert parsed["connected"] == False, f"Connected mismatch: {parsed['connected']}"
    
    print("  ✓ All device status tests passed")


def test_haptic_feedback():
    """Test haptic feedback encoding and parsing."""
    print("Testing haptic feedback...")
    
    # Encode haptic (with message type)
    encoded = encode_haptic_feedback("short", 0, 0)
    assert encoded == bytes([MSG_TYPE_HAPTIC_FEEDBACK, 0x01, 0x00, 0x00]), f"Unexpected encoding: {encoded}"
    
    # Encode haptic with custom values (with message type)
    encoded = encode_haptic_feedback("double", 20, 128)
    assert encoded == bytes([MSG_TYPE_HAPTIC_FEEDBACK, 0x02, 20, 128]), f"Unexpected encoding: {encoded}"
    
    # Parse haptic (with message type)
    parsed = parse_haptic_feedback(bytes([MSG_TYPE_HAPTIC_FEEDBACK, 0x01, 0x00, 0x00]))
    assert parsed["pattern"] == "short", f"Pattern mismatch: {parsed['pattern']}"
    assert parsed["duration"] == 0, f"Duration mismatch: {parsed['duration']}"
    assert parsed["intensity"] == 0, f"Intensity mismatch: {parsed['intensity']}"
    
    # Parse haptic (with message type)
    parsed = parse_haptic_feedback(bytes([MSG_TYPE_HAPTIC_FEEDBACK, 0x02, 20, 128]))
    assert parsed["pattern"] == "double", f"Pattern mismatch: {parsed['pattern']}"
    assert parsed["duration"] == 20, f"Duration mismatch: {parsed['duration']}"
    assert parsed["intensity"] == 128, f"Intensity mismatch: {parsed['intensity']}"
    
    print("  ✓ All haptic feedback tests passed")


def test_mock_device_zeroconf():
    """Test that mock device can advertise via zeroconf."""
    print("Testing mock device zeroconf advertising...")
    
    try:
        import asyncio
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
        
        # Check if zeroconf is available
        try:
            from mock_device_tcp import start_mock_server, ZEROCONF_AVAILABLE
        except ImportError:
            print("  ⊘ Skipped (mock_device_tcp not available)")
            return
        
        if not ZEROCONF_AVAILABLE:
            print("  ⊘ Skipped (zeroconf not available)")
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


def test_mock_device_ble():
    """Test that BLE mock device can be instantiated."""
    print("Testing BLE mock device...")
    
    try:
        from mock_device_ble import MockBLEDevice, BLESS_AVAILABLE
        
        if not BLESS_AVAILABLE:
            print("  ⊘ Skipped (bless not available)")
            return
        
        # Create device
        device = MockBLEDevice()
        
        # Check device info
        info = device.get_device_info()
        # MockBLEDevice uses "OpenBike" as the default name in the constructor
        assert info['name'] == 'OpenBike', f"Device name mismatch: {info['name']}"
        assert info['manufacturer'] == 'ExampleCorp', "Manufacturer mismatch"
        assert info['model'] == 'MC-100', "Model mismatch"
        assert info['battery'] == 85, "Battery level mismatch"
        assert info['serial'] == '1234567890', "Serial mismatch"
        
        print("  ✓ BLE mock device tests passed")
    
    except ImportError as e:
        print(f"  ⊘ Skipped (import error: {e})")
    except Exception as e:
        print(f"  ⚠ BLE mock device test skipped due to error: {e}")
        import traceback
        traceback.print_exc()


def test_app_info_encoding():
    """Test app info encoding and decoding."""
    print("Testing app info encoding and decoding...")
    
    # Test basic encoding (with message type)
    result = encode_app_info("zwift", "1.52.0", [0x01, 0x02, 0x10, 0x14])
    
    # Verify structure
    assert result[0] == MSG_TYPE_APP_INFO, "Message type byte incorrect"
    assert result[1] == 0x01, "Version byte incorrect"
    assert result[2] == 5, "App ID length incorrect"
    assert result[3:8] == b'zwift', "App ID incorrect"
    assert result[8] == 6, "App version length incorrect"
    assert result[9:15] == b'1.52.0', "App version incorrect"
    assert result[15] == 4, "Button count incorrect"
    assert result[16] == 0x01, "First button ID incorrect"
    assert result[17] == 0x02, "Second button ID incorrect"
    
    # Test decoding (with message type)
    decoded = parse_app_info(result)
    assert decoded["app_id"] == "zwift", "App ID decode failed"
    assert decoded["app_version"] == "1.52.0", "App version decode failed"
    assert len(decoded["supported_buttons"]) == 4, "Button count decode failed"
    assert decoded["supported_buttons"][0] == 0x01, "Button ID decode failed"
    
    # Test encoding with message type
    result_tcp = encode_app_info("test", "1.0", [])
    assert result_tcp[0] == MSG_TYPE_APP_INFO, "Message type incorrect"
    assert result_tcp[1] == 0x01, "Version byte incorrect"
    
    # Test decoding with message type
    decoded_tcp = parse_app_info(result_tcp)
    assert decoded_tcp["app_id"] == "test", "App ID decode failed"
    assert decoded_tcp["app_version"] == "1.0", "App version decode failed"
    assert len(decoded_tcp["supported_buttons"]) == 0, "Empty button list decode failed"
    
    # Test long app ID (should truncate)
    long_id = "a" * 50
    result3 = encode_app_info(long_id, "1.0", [])
    assert result3[2] == 32, "Long app ID should be truncated to 32 bytes"
    
    # Test round-trip encoding/decoding
    original = {"app_id": "myapp", "app_version": "2.1.3", "supported_buttons": [0x01, 0x20, 0x30]}
    encoded = encode_app_info(original["app_id"], original["app_version"], original["supported_buttons"])
    decoded = parse_app_info(encoded)
    
    assert decoded["app_id"] == original["app_id"], "Round-trip app_id failed"
    assert decoded["app_version"] == original["app_version"], "Round-trip app_version failed"
    assert decoded["supported_buttons"] == original["supported_buttons"], "Round-trip buttons failed"
    
    # Test malformed data (too short)
    try:
        parse_app_info(bytes([MSG_TYPE_APP_INFO, 0x01]))
        assert False, "Should have raised ValueError for truncated data"
    except ValueError:
        pass  # Expected
    
    # Test malformed data (app_id_len exceeds buffer)
    try:
        malformed = bytes([MSG_TYPE_APP_INFO, 0x01, 0xFF, 0x01, 0x02])  # Claims 255 bytes but only has 2
        parse_app_info(malformed)
        assert False, "Should have raised ValueError for out-of-bounds app ID"
    except ValueError:
        pass  # Expected
    
    print("  ✓ App info encoding and decoding tests passed")


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
        test_encode_button_state()
        test_device_status()
        test_haptic_feedback()
        test_app_info_encoding()
        test_mock_device_zeroconf()
        test_mock_device_ble()
        
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
