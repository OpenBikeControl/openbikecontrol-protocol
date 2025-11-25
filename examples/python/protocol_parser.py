#!/usr/bin/env python3
"""
OpenBikeControl Protocol Parser

Shared module for parsing OpenBikeControl protocol data in both BLE and TCP implementations.
This module provides common functionality for encoding and decoding messages according to
the OpenBikeControl protocol specification.
"""

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

# Message types (for TCP/mDNS protocol)
MSG_TYPE_BUTTON_STATE = 0x01
MSG_TYPE_DEVICE_STATUS = 0x02
MSG_TYPE_HAPTIC_FEEDBACK = 0x03
MSG_TYPE_APP_INFO = 0x04


def parse_button_state(data: bytes) -> list:
    """
    Parse button state data from binary format.
    
    Data format: [Message_Type, Button_ID_1, State_1, Button_ID_2, State_2, ...]
    
    Args:
        data: Raw bytes from BLE notification or TCP message
        
    Returns:
        List of tuples (button_id, state)
    """
    buttons = []
    
    if len(data) == 0:
        return buttons
    
    # Expect message type as first byte
    if data[0] != MSG_TYPE_BUTTON_STATE:
        return buttons
    
    # Parse button state pairs starting after message type
    for i in range(1, len(data), 2):
        if i + 1 < len(data):
            button_id = data[i]
            state = data[i + 1]
            buttons.append((button_id, state))
    
    return buttons


def encode_button_state(buttons: list) -> bytes:
    """
    Encode button state data to binary format.
    
    Args:
        buttons: List of tuples (button_id, state)
        
    Returns:
        Encoded bytes with message type prefix
    """
    data = bytearray()
    data.append(MSG_TYPE_BUTTON_STATE)
    
    for button_id, state in buttons:
        data.append(button_id)
        data.append(state)
    
    return bytes(data)


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


def parse_device_status(data: bytes) -> dict:
    """
    Parse device status message from binary format.
    
    Data format: [Message_Type, Battery, Connected]
    
    Args:
        data: Raw bytes from TCP message
        
    Returns:
        Dictionary with battery and connected status
    """
    if len(data) < 3:
        raise ValueError("Device status message too short")
    
    if data[0] != MSG_TYPE_DEVICE_STATUS:
        raise ValueError(f"Invalid message type: {data[0]}, expected {MSG_TYPE_DEVICE_STATUS}")
    
    battery = data[1] if data[1] != 0xFF else None
    connected = data[2] == 0x01
    
    return {
        "battery": battery,
        "connected": connected
    }


def encode_device_status(battery: int = None, connected: bool = True) -> bytes:
    """
    Encode device status message to binary format.
    
    Args:
        battery: Battery level 0-100, or None if not applicable
        connected: Connection state
        
    Returns:
        Encoded bytes
    """
    battery_byte = 0xFF if battery is None else battery
    connected_byte = 0x01 if connected else 0x00
    
    return bytes([MSG_TYPE_DEVICE_STATUS, battery_byte, connected_byte])


def encode_haptic_feedback(pattern: str = "short", duration: int = 0, 
                          intensity: int = 0) -> bytes:
    """
    Encode haptic feedback command to binary format.
    
    Args:
        pattern: Haptic pattern name (see HAPTIC_PATTERNS)
        duration: Duration in 10ms units (0 = use default)
        intensity: Intensity 0-255 (0 = use default)
        
    Returns:
        Encoded bytes with message type prefix
    """
    pattern_byte = HAPTIC_PATTERNS.get(pattern, HAPTIC_PATTERNS["short"])
    
    data = bytearray()
    data.append(MSG_TYPE_HAPTIC_FEEDBACK)
    data.extend([pattern_byte, duration, intensity])
    
    return bytes(data)


def parse_haptic_feedback(data: bytes) -> dict:
    """
    Parse haptic feedback command from binary format.
    
    Data format: [Message_Type, Pattern, Duration, Intensity]
    
    Args:
        data: Raw bytes
        
    Returns:
        Dictionary with pattern, duration, and intensity
    """
    if len(data) < 4:
        raise ValueError("Haptic feedback message too short")
    
    if data[0] != MSG_TYPE_HAPTIC_FEEDBACK:
        raise ValueError(f"Invalid message type: {data[0]}")
    
    pattern_byte = data[1]
    duration = data[2]
    intensity = data[3]
    
    # Reverse lookup pattern name
    pattern_name = "unknown"
    for name, value in HAPTIC_PATTERNS.items():
        if value == pattern_byte:
            pattern_name = name
            break
    
    return {
        "pattern": pattern_name,
        "pattern_byte": pattern_byte,
        "duration": duration,
        "intensity": intensity
    }


def encode_app_info(app_id: str = "example-app", app_version: str = "1.0.0",
                   supported_buttons: list = None) -> bytes:
    """
    Encode app information to binary format.
    
    Args:
        app_id: App identifier string
        app_version: App version string
        supported_buttons: List of supported button IDs (empty list = all buttons)
        
    Returns:
        Encoded bytes with message type prefix
    """
    if supported_buttons is None:
        supported_buttons = []
    
    app_id_bytes = app_id.encode('utf-8')[:32]  # Max 32 chars
    app_version_bytes = app_version.encode('utf-8')[:32]  # Max 32 chars
    
    data = bytearray()
    data.append(MSG_TYPE_APP_INFO)
    data.append(0x01)  # Version
    data.append(len(app_id_bytes))  # App ID length
    data.extend(app_id_bytes)  # App ID
    data.append(len(app_version_bytes))  # App Version length
    data.extend(app_version_bytes)  # App Version
    data.append(len(supported_buttons))  # Button count
    data.extend(supported_buttons)  # Button IDs
    
    return bytes(data)


def parse_app_info(data: bytes) -> dict:
    """
    Parse app information from binary format.
    
    Data format: [Message_Type, Version, App_ID_Length, App_ID..., ...]
    
    Args:
        data: Raw bytes
        
    Returns:
        Dictionary with app_id, app_version, and supported_buttons
    """
    if len(data) < 1 or data[0] != MSG_TYPE_APP_INFO:
        raise ValueError("Invalid message type")
    
    idx = 1  # Start after message type
    
    if len(data) < idx + 3:
        raise ValueError("App info message too short")
    
    version = data[idx]
    idx += 1
    
    if version != 0x01:
        raise ValueError(f"Unsupported app info version: {version}")
    
    # Parse App ID with bounds checking
    if idx >= len(data):
        raise ValueError("Missing app ID length")
    app_id_len = data[idx]
    idx += 1
    if idx + app_id_len > len(data):
        raise ValueError("App ID length exceeds buffer")
    app_id = data[idx:idx+app_id_len].decode('utf-8')
    idx += app_id_len
    
    # Parse App Version with bounds checking
    if idx >= len(data):
        raise ValueError("Missing app version length")
    app_version_len = data[idx]
    idx += 1
    if idx + app_version_len > len(data):
        raise ValueError("App version length exceeds buffer")
    app_version = data[idx:idx+app_version_len].decode('utf-8')
    idx += app_version_len
    
    # Parse Button IDs with bounds checking
    if idx >= len(data):
        raise ValueError("Missing button count")
    button_count = data[idx]
    idx += 1
    if idx + button_count > len(data):
        raise ValueError("Button count exceeds buffer")
    button_ids = list(data[idx:idx+button_count])
    
    return {
        "app_id": app_id,
        "app_version": app_version,
        "supported_buttons": button_ids
    }
