# OpenBikeControl Python Trainer App Examples

This directory contains Python example implementations demonstrating how to connect to OpenBikeControl devices and receive button state data using both BLE and mDNS protocols.

## Overview

These examples show how trainer applications can integrate OpenBikeControl support to receive input from wireless controllers. The examples demonstrate:

- **BLE Trainer App** (`ble_trainer_app.py`): Connect to devices via Bluetooth Low Energy
- **mDNS Trainer App** (`mdns_trainer_app.py`): Connect to devices via network using mDNS/Zeroconf

Both examples provide:
- Device discovery
- Connection management
- Button state monitoring
- Haptic feedback support
- Clear console output showing received data

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
# For BLE support
pip install bleak>=0.21.0

# For mDNS support
pip install zeroconf>=0.131.0 websockets>=12.0
```

### Platform-Specific Requirements

#### Linux
For BLE support on Linux, you may need to install additional system packages:

```bash
# Debian/Ubuntu
sudo apt-get install bluez libbluetooth-dev

# For running without sudo (optional)
sudo setcap cap_net_raw+ep $(readlink -f $(which python3))
```

#### macOS
- BLE support works out of the box
- mDNS support works out of the box (using Apple's Bonjour)

#### Windows
- BLE support works with Windows 10 version 1709 or later
- mDNS support works out of the box

## Usage

### BLE Trainer App

Connect to an OpenBikeControl device via Bluetooth:

```bash
python ble_trainer_app.py
```

The app will:
1. Scan for OpenBikeControl BLE devices (5 seconds)
2. Display found devices
3. Connect to the device (auto-select if only one found)
4. Subscribe to button state notifications
5. Display button presses/releases in real-time
6. Send haptic feedback on button presses
7. Run until Ctrl+C is pressed

**Example Output:**
```
============================================================
OpenBikeControl BLE Trainer App Example
============================================================

🔍 Scanning for OpenBikeControl devices...
   Scan timeout: 5.0 seconds

✓ Found device: OpenBike Remote
  Address: AA:BB:CC:DD:EE:FF
  RSSI: -45 dBm

Found 1 device(s)

🔗 Connecting to OpenBike Remote...
✓ Connected to OpenBike Remote

📱 Device Information:
  Service: d273f680-d548-419d-b9d1-fa0472345229
    Characteristic: d273f681-d548-419d-b9d1-fa0472345229
      Properties: ['read', 'notify']
    Characteristic: d273f682-d548-419d-b9d1-fa0472345229
      Properties: ['write', 'write-without-response']

👂 Subscribing to button state notifications...
✓ Subscribed! Waiting for button presses...

Press Ctrl+C to stop

📍 Button State Update (received 2 bytes):
  Shift Up: PRESSED
  → Sent haptic feedback: short

📍 Button State Update (received 2 bytes):
  Shift Up: RELEASED
```

### mDNS Trainer App

Connect to an OpenBikeControl device via network:

```bash
python mdns_trainer_app.py
```

The app will:
1. Discover OpenBikeControl devices on the network (5 seconds)
2. Display found devices with details
3. Connect via WebSocket
4. Listen for button state and status messages
5. Display updates in real-time
6. Send haptic feedback on button presses
7. Run until Ctrl+C is pressed

**Example Output:**
```
============================================================
OpenBikeControl mDNS Trainer App Example
============================================================

🔍 Discovering OpenBikeControl devices...
   Discovery timeout: 5.0 seconds

✓ Found device: OpenBike Remote
  Service: OpenBike Remote._openbikecontrol._tcp.local.
  Address: 192.168.1.100:8080
  ID: aabbccddeeff
  Manufacturer: ExampleCorp
  Model: SC-100

Found 1 device(s)

🔗 Connecting to OpenBike Remote._openbikecontrol._tcp.local....
   WebSocket URL: ws://192.168.1.100:8080/api/ws

✓ Connected to OpenBike Remote

👂 Listening for messages...
Press Ctrl+C to stop

📍 Button State Update [14:30:45.123]:
  Shift Up: PRESSED
  → Sent haptic feedback: short

📍 Button State Update [14:30:45.234]:
  Shift Up: RELEASED

🔋 Device Status Update [14:30:50.001]:
  Battery: 85%
  Connected: Yes
```

## Button Mapping

Both examples support the full OpenBikeControl button mapping:

### Gear Shifting (0x01-0x0F)
- 0x01: Shift Up
- 0x02: Shift Down
- 0x03: Gear Set

### Navigation (0x10-0x1F)
- 0x10: Up/Steer Left
- 0x11: Down/Steer Right
- 0x12: Left/Look Left
- 0x13: Right/Look Right
- 0x14: Select/Confirm
- 0x15: Back/Cancel
- 0x16: Menu
- 0x17: Home

### Social/Emotes (0x20-0x2F)
- 0x20: Wave
- 0x21: Thumbs Up
- 0x22: Hammer Time
- 0x23: Bell
- 0x24: Screenshot

### Training Controls (0x30-0x3F)
- 0x30: ERG Up
- 0x31: ERG Down
- 0x32: Skip Interval
- 0x33: Pause
- 0x34: Resume
- 0x35: Lap

### View Controls (0x40-0x4F)
- 0x40: Camera Angle
- 0x41-0x43: Camera 1-3
- 0x44: HUD Toggle
- 0x45: Map Toggle

### Power-ups (0x50-0x5F)
- 0x50-0x52: Power-up 1-3

See the [Protocol Specification](../../PROTOCOL.md) for the complete button mapping.

## Haptic Feedback

Both examples support sending haptic feedback to devices:

### Available Patterns
- `short`: Single short vibration (default)
- `double`: Double pulse
- `triple`: Triple pulse
- `long`: Long vibration
- `success`: Success pattern (crescendo)
- `warning`: Warning pattern
- `error`: Error pattern

The examples automatically send a short haptic pulse when a button is pressed, providing tactile confirmation to the user.

## Architecture

### BLE Implementation
- Uses the `bleak` library for cross-platform BLE support
- Scans for devices advertising the OpenBikeControl service UUID
- Subscribes to button state characteristic notifications
- Sends haptic feedback via write characteristic
- Handles connection management and cleanup

### mDNS Implementation
- Uses `zeroconf` for mDNS/Bonjour service discovery
- Discovers devices advertising `_openbikecontrol._tcp.local.`
- Connects via WebSocket (`ws://<ip>:<port>/api/ws`)
- Handles JSON message format for button states and status
- Supports bidirectional communication for haptic feedback

## Troubleshooting

### BLE Issues

**No devices found:**
- Ensure Bluetooth is enabled on your computer
- Make sure the device is in pairing/advertising mode
- Check that the device is within Bluetooth range (~10m)
- On Linux, ensure you have proper permissions (see Linux requirements)

**Connection failed:**
- Try restarting both the device and Bluetooth on your computer
- On Linux, make sure BlueZ is running: `sudo systemctl start bluetooth`

### mDNS Issues

**No devices found:**
- Ensure both computer and device are on the same network
- Check that the device is powered on and connected to WiFi
- Verify firewall settings allow mDNS traffic (UDP port 5353)
- Some corporate networks may block mDNS

**WebSocket connection failed:**
- Verify the device's WebSocket endpoint is accessible
- Check firewall settings on both device and computer
- Ensure the device's HTTP/WebSocket server is running

### General Issues

**Import errors:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.7+)

**Permission errors (Linux):**
- BLE operations may require root or specific capabilities
- Run with sudo: `sudo python ble_trainer_app.py`
- Or set capabilities (see Linux requirements above)

## Extending the Examples

These examples can be extended to build full trainer applications:

1. **Action Mapping**: Map button IDs to specific app actions
2. **Multi-device Support**: Connect to multiple devices simultaneously
3. **Configuration**: Save/load user button mappings
4. **UI Integration**: Integrate with GUI frameworks (tkinter, PyQt, etc.)
5. **State Management**: Track device state and handle reconnections
6. **Logging**: Add detailed logging for debugging

## Contributing

These examples are part of the OpenBikeControl Protocol project. Contributions are welcome!

- Report issues on GitHub
- Submit improvements via pull requests
- Share your implementations with the community

## License

These examples are released under the MIT License, same as the OpenBikeControl Protocol.

## See Also

- [OpenBikeControl Protocol Specification](../../PROTOCOL.md)
- [BLE Protocol Details](../../BLE.md)
- [mDNS Protocol Details](../../MDNS.md)
- [Certification Program](../../CERTIFICATION.md)
