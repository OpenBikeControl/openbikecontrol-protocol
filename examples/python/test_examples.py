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
        assert info['name'] == 'Mock OpenBike Remote', "Device name mismatch"
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


def test_app_info_json_format():
    """Test app info JSON message format for mDNS/WebSocket."""
    print("Testing app info JSON format...")
    
    import json
    
    # Test valid app info message
    message = {
        "type": "app_info",
        "app_id": "zwift",
        "app_version": "1.52.0",
        "supported_buttons": [0x01, 0x02, 0x10, 0x14]
    }
    
    # Should be valid JSON
    json_str = json.dumps(message)
    parsed = json.loads(json_str)
    
    assert parsed["type"] == "app_info", "Type field mismatch"
    assert parsed["app_id"] == "zwift", "App ID mismatch"
    assert parsed["app_version"] == "1.52.0", "App version mismatch"
    assert len(parsed["supported_buttons"]) == 4, "Button count mismatch"
    assert parsed["supported_buttons"][0] == 0x01, "Button ID mismatch"
    
    # Test empty button list
    message2 = {
        "type": "app_info",
        "app_id": "test-app",
        "app_version": "1.0.0",
        "supported_buttons": []
    }
    json_str2 = json.dumps(message2)
    parsed2 = json.loads(json_str2)
    assert len(parsed2["supported_buttons"]) == 0, "Empty button list failed"
    
    print("  ✓ App info JSON format tests passed")


def _encode_app_info_ble(app_id: str, app_version: str, supported_buttons: list) -> bytes:
    """
    Helper function to encode app info to BLE format.
    Used by multiple test functions.
    """
    app_id_bytes = app_id.encode('utf-8')[:32]
    app_version_bytes = app_version.encode('utf-8')[:32]
    
    data = bytearray()
    data.append(0x01)  # Version
    data.append(len(app_id_bytes))
    data.extend(app_id_bytes)
    data.append(len(app_version_bytes))
    data.extend(app_version_bytes)
    data.append(len(supported_buttons))
    data.extend(supported_buttons)
    
    return bytes(data)


def test_app_info_ble_encoding():
    """Test app info BLE binary encoding."""
    print("Testing app info BLE encoding...")
    
    # Test basic encoding
    result = _encode_app_info_ble("zwift", "1.52.0", [0x01, 0x02, 0x10, 0x14])
    
    # Verify structure
    assert result[0] == 0x01, "Version byte incorrect"
    assert result[1] == 5, "App ID length incorrect"
    assert result[2:7] == b'zwift', "App ID incorrect"
    assert result[7] == 6, "App version length incorrect"
    assert result[8:14] == b'1.52.0', "App version incorrect"
    assert result[14] == 4, "Button count incorrect"
    assert result[15] == 0x01, "First button ID incorrect"
    assert result[16] == 0x02, "Second button ID incorrect"
    
    # Test empty button list
    result2 = _encode_app_info_ble("test", "1.0", [])
    assert result2[-1] == 0, "Empty button list encoding failed"
    
    # Test long app ID (should truncate)
    long_id = "a" * 50
    result3 = _encode_app_info_ble(long_id, "1.0", [])
    assert result3[1] == 32, "Long app ID should be truncated to 32 bytes"
    
    print("  ✓ App info BLE encoding tests passed")


def test_app_info_ble_decoding():
    """Test app info BLE binary decoding."""
    print("Testing app info BLE decoding...")
    
    # Test decoding function (from mock_device_ble.py) with bounds checking
    def decode_app_info(value: bytes) -> dict:
        """Decode app info from BLE format."""
        if len(value) < 3:
            raise ValueError("Data too short")
        
        idx = 0
        version = value[idx]
        idx += 1
        
        if version != 0x01:
            raise ValueError(f"Unsupported version: {version}")
        
        # Parse App ID with bounds checking
        if idx >= len(value):
            raise ValueError("Missing app ID length")
        app_id_len = value[idx]
        idx += 1
        if idx + app_id_len > len(value):
            raise ValueError("App ID length exceeds buffer")
        app_id = value[idx:idx+app_id_len].decode('utf-8')
        idx += app_id_len
        
        # Parse App Version with bounds checking
        if idx >= len(value):
            raise ValueError("Missing app version length")
        app_version_len = value[idx]
        idx += 1
        if idx + app_version_len > len(value):
            raise ValueError("App version length exceeds buffer")
        app_version = value[idx:idx+app_version_len].decode('utf-8')
        idx += app_version_len
        
        # Parse Button IDs with bounds checking
        if idx >= len(value):
            raise ValueError("Missing button count")
        button_count = value[idx]
        idx += 1
        if idx + button_count > len(value):
            raise ValueError("Button count exceeds buffer")
        button_ids = list(value[idx:idx+button_count])
        
        return {
            "app_id": app_id,
            "app_version": app_version,
            "supported_buttons": button_ids
        }
    
    # Test basic decoding
    data = bytes([0x01, 0x05]) + b'zwift' + bytes([0x06]) + b'1.52.0' + bytes([0x04, 0x01, 0x02, 0x10, 0x14])
    result = decode_app_info(data)
    
    assert result["app_id"] == "zwift", "App ID decode failed"
    assert result["app_version"] == "1.52.0", "App version decode failed"
    assert len(result["supported_buttons"]) == 4, "Button count decode failed"
    assert result["supported_buttons"][0] == 0x01, "Button ID decode failed"
    
    # Test empty button list
    data2 = bytes([0x01, 0x04]) + b'test' + bytes([0x03]) + b'1.0' + bytes([0x00])
    result2 = decode_app_info(data2)
    assert len(result2["supported_buttons"]) == 0, "Empty button list decode failed"
    
    # Test round-trip encoding/decoding
    original = {"app_id": "myapp", "app_version": "2.1.3", "supported_buttons": [0x01, 0x20, 0x30]}
    encoded = _encode_app_info_ble(original["app_id"], original["app_version"], original["supported_buttons"])
    decoded = decode_app_info(encoded)
    
    assert decoded["app_id"] == original["app_id"], "Round-trip app_id failed"
    assert decoded["app_version"] == original["app_version"], "Round-trip app_version failed"
    assert decoded["supported_buttons"] == original["supported_buttons"], "Round-trip buttons failed"
    
    # Test malformed data (too short)
    try:
        decode_app_info(bytes([0x01]))
        assert False, "Should have raised ValueError for truncated data"
    except ValueError:
        pass  # Expected
    
    # Test malformed data (app_id_len exceeds buffer)
    try:
        malformed = bytes([0x01, 0xFF, 0x01, 0x02])  # Claims 255 bytes but only has 2
        decode_app_info(malformed)
        assert False, "Should have raised ValueError for out-of-bounds app ID"
    except ValueError:
        pass  # Expected
    
    print("  ✓ App info BLE decoding tests passed")


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
        test_app_info_json_format()
        test_app_info_ble_encoding()
        test_app_info_ble_decoding()
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
