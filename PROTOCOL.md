# SwiftControl Protocol Specification

## Overview

SwiftControl is an open protocol for wireless input devices to control cycling trainer applications. It enables standardized communication between BLE controllers and training apps like MyWhoosh, Rouvy, Zwift, and others.

### Motivation

Many cycling trainer apps support various actions that traditionally require:
- On-screen button clicks
- Keyboard input
- Proprietary BLE controllers

SwiftControl provides a unified, open protocol that:
- **Easy to implement** - Simple data format with minimal overhead
- **Open standard** - No licensing fees or proprietary restrictions
- **Dual connectivity** - Supports both BLE and network-based connections
- **Already partially adopted** - Compatible with existing "Direct Connect" implementations
- **Apple-friendly** - Does not rely on manufacturer data fields that cannot be emulated on iOS

### Supported Actions

SwiftControl enables the following trainer app actions:
- **Virtual gear shifting** - Up/down shifting for smart trainer devices
- **Navigation** - Menu navigation, route selection, steering controls
- **UI controls** - Select, back, confirm buttons
- **Social features** - Emotes (wave, thumbs up, ride on, etc.)
- **Training controls** - ERG mode adjustments, workout skips
- **Custom actions** - App-specific features

## Protocol Architecture

SwiftControl uses two transport mechanisms:

1. **BLE (Bluetooth Low Energy)** - For direct device-to-app connections
2. **mDNS (Multicast DNS)** - For network-based connections ("Direct Connect")

Both transports use the same logical data format, ensuring consistency across connection types.

---

## BLE Protocol Specification

### Service UUID

**Primary Service UUID:** `0000FE50-0000-1000-8000-00805F9B34FB`

This service UUID is used for SwiftControl device advertisement and discovery.

### Characteristics

#### 1. Button State Characteristic

**UUID:** `0000FE51-0000-1000-8000-00805F9B34FB`

**Properties:** Read, Notify

**Description:** Reports the state of all buttons on the controller.

**Data Format:**

The characteristic value consists of button state pairs:

```
[Button_ID_1] [State_1] [Button_ID_2] [State_2] ... [Button_ID_N] [State_N]
```

- **Button_ID** (1 byte): Identifier for the button (see Button Mapping section)
- **State** (1 byte): Current state of the button
  - `0x00` = Released/Off
  - `0x01` = Pressed/On
  - `0x02-0xFF` = Analog value (for analog inputs like triggers or joysticks, where 0x02 = minimum, 0xFF = maximum)

**Notification Behavior:**

- Notifications MUST be sent only when a button state changes
- Include all changed buttons in a single notification to minimize BLE traffic
- If multiple buttons change simultaneously, combine them in one notification
- Maximum recommended payload: 20 bytes (10 button state pairs)

**Example Notifications:**

```
// Single button press (button 0x01 pressed)
[0x01, 0x01]

// Multiple buttons (button 0x01 pressed, button 0x02 released)
[0x01, 0x01, 0x02, 0x00]

// Analog input (button 0x10 at 50% = 0x80)
[0x10, 0x80]
```

### Standard BLE Services

SwiftControl devices MUST implement the following standard BLE services:

#### Device Information Service (0x180A)

Required characteristics:
- **Manufacturer Name String** (0x2A29) - Device manufacturer
- **Model Number String** (0x2A24) - Device model
- **Serial Number String** (0x2A25) - Unique device serial
- **Hardware Revision String** (0x2A27) - Hardware version
- **Firmware Revision String** (0x2A26) - Firmware version
- **Software Revision String** (0x2A28) - Optional software version

#### Battery Service (0x180F)

Required for battery-powered devices:
- **Battery Level** (0x2A19) - Current battery percentage (0-100)

### Advertisement Requirements

**CRITICAL:** SwiftControl devices MUST NOT rely on manufacturer-specific data in BLE advertisements. This restriction ensures compatibility with Apple iOS devices, which do not allow apps to emulate manufacturer data.

**Advertisement Data:**

- **Service UUIDs**: Must advertise the primary service UUID `0xFE50`
- **Flags**: General discoverable mode, BR/EDR not supported

**Example Advertisement:**
```
Flags: 0x06 (LE General Discoverable, BR/EDR not supported)
Complete List of 16-bit Service UUIDs: 0xFE50
```

### Connection Parameters

Recommended BLE connection parameters for optimal performance:

- **Connection Interval**: 7.5-15ms (for low latency)
- **Slave Latency**: 0 (for immediate response)
- **Supervision Timeout**: 4 seconds
- **MTU Size**: 23 bytes minimum, 247 bytes preferred

---

## Button Mapping

### Standard Button IDs

SwiftControl defines standard button IDs for common actions. Device manufacturers should map their physical buttons to these standard IDs.

#### Gear Shifting (0x01-0x0F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x01` | Shift Up | Increase virtual gear |
| `0x02` | Shift Down | Decrease virtual gear |
| `0x03` | Gear Set | Direct gear selection (use analog value) |

#### Navigation (0x10-0x1F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x10` | Up | Navigate up / Steer left |
| `0x11` | Down | Navigate down / Steer right |
| `0x12` | Left | Navigate left / Look left |
| `0x13` | Right | Navigate right / Look right |
| `0x14` | Select/Confirm | Confirm selection |
| `0x15` | Back/Cancel | Go back / Cancel |
| `0x16` | Menu | Open menu |
| `0x17` | Home | Return to home screen |

#### Social/Emotes (0x20-0x2F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x20` | Wave | Wave to other riders |
| `0x21` | Thumbs Up | Give thumbs up |
| `0x22` | Ride On | Zwift "Ride On" or equivalent |
| `0x23` | Hammer Time | Activate power-up |
| `0x24` | Bell | Ring bell |
| `0x25` | Screenshot | Take screenshot |

#### Training Controls (0x30-0x3F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x30` | ERG Up | Increase ERG mode power |
| `0x31` | ERG Down | Decrease ERG mode power |
| `0x32` | Skip Interval | Skip to next workout interval |
| `0x33` | Pause | Pause workout |
| `0x34` | Resume | Resume workout |
| `0x35` | Lap | Mark lap |

#### View Controls (0x40-0x4F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x40` | Camera Angle | Cycle camera view |
| `0x41` | Camera 1 | Switch to camera 1 |
| `0x42` | Camera 2 | Switch to camera 2 |
| `0x43` | Camera 3 | Switch to camera 3 |
| `0x44` | HUD Toggle | Show/hide HUD |
| `0x45` | Map Toggle | Show/hide map |

#### Power-ups (0x50-0x5F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x50` | Power-up 1 | Activate power-up slot 1 |
| `0x51` | Power-up 2 | Activate power-up slot 2 |
| `0x52` | Power-up 3 | Activate power-up slot 3 |

#### Custom/Reserved (0x60-0xFF)

| Range | Purpose |
|-------|---------|
| `0x60-0x7F` | Reserved for future standard actions |
| `0x80-0x9F` | App-specific custom actions |
| `0xA0-0xFF` | Manufacturer-specific custom actions |

### Multi-Button Combinations

Apps may implement multi-button combinations by detecting multiple simultaneous button presses. For example:
- Shift Up + Shift Down simultaneously = Reset gear to neutral
- Menu + Select = Quick settings

---

## mDNS Protocol Specification

The mDNS implementation provides network-based connectivity, similar to the "Direct Connect" protocol.

### Service Discovery

**Service Type:** `_swiftcontrol._tcp.local.`

**Service Name Format:** `<Device Name>._swiftcontrol._tcp.local.`

**TXT Record Fields:**

- `version=1` - Protocol version
- `id=<unique-id>` - Unique device identifier
- `name=<device-name>` - Human-readable device name
- `buttons=<count>` - Number of available buttons
- `analog=<true/false>` - Supports analog inputs
- `manufacturer=<name>` - Device manufacturer
- `model=<model>` - Device model

**Example:**
```
Service: SwiftControl Remote._swiftcontrol._tcp.local.
Port: 8080
TXT:
  version=1
  id=aabbccddeeff
  name=SwiftControl Remote
  buttons=8
  analog=true
  manufacturer=ExampleCorp
  model=SC-100
```

### HTTP/WebSocket Protocol

Once discovered, apps connect to the device using HTTP or WebSocket.

#### HTTP Endpoint

**Endpoint:** `GET /api/buttons`

**Response Format (JSON):**

```json
{
  "version": "1.0",
  "device": {
    "id": "aabbccddeeff",
    "name": "SwiftControl Remote",
    "manufacturer": "ExampleCorp",
    "model": "SC-100",
    "firmware": "1.2.3"
  },
  "buttons": [
    {
      "id": 1,
      "name": "Shift Up",
      "state": 0
    },
    {
      "id": 2,
      "name": "Shift Down",
      "state": 0
    }
  ]
}
```

#### WebSocket Connection

**Endpoint:** `ws://<device-ip>:<port>/api/ws`

**Message Format (JSON):**

Button state change notifications:
```json
{
  "type": "button_state",
  "timestamp": 1699887600000,
  "buttons": [
    {"id": 1, "state": 1},
    {"id": 2, "state": 0}
  ]
}
```

Device status updates:
```json
{
  "type": "device_status",
  "timestamp": 1699887600000,
  "battery": 85,
  "connected": true
}
```

#### RESTful API (Optional)

For simple implementations, devices may support REST endpoints:

**GET /api/button/:id**
```json
{
  "id": 1,
  "name": "Shift Up",
  "state": 0
}
```

**POST /api/feedback** (for haptic feedback, if supported)
```json
{
  "type": "vibrate",
  "duration": 100,
  "intensity": 128
}
```

---

## Implementation Guidelines

### For App Developers

1. **BLE Implementation:**
   - Scan for devices advertising service UUID `0xFE50`
   - Connect and discover the Button State characteristic (`0xFE51`)
   - Subscribe to notifications for real-time button updates
   - Map button IDs to app-specific actions

2. **mDNS Implementation:**
   - Use Bonjour/Zeroconf libraries to discover `_swiftcontrol._tcp.local.` services
   - Connect via WebSocket for real-time updates
   - Fall back to HTTP polling if WebSocket is unavailable

3. **Button Mapping:**
   - Provide user configuration for custom button mappings
   - Use standard button IDs as defaults
   - Allow users to override mappings for their workflow

4. **Multi-Device Support:**
   - Support connecting multiple SwiftControl devices simultaneously
   - Allow users to assign devices to specific action categories

### For Device Manufacturers

1. **Hardware:**
   - Use reliable button switches for digital inputs
   - Consider hall-effect sensors for analog inputs
   - Include battery monitoring circuitry for battery level reporting

2. **Firmware:**
   - Implement efficient button debouncing (10-50ms)
   - Only send notifications on state changes
   - Batch multiple button changes in one notification
   - Support both BLE and mDNS for maximum compatibility

3. **Power Management:**
   - Implement BLE sleep modes when inactive
   - Wake on button press
   - Report accurate battery levels

4. **Testing:**
   - Test with major trainer apps (Zwift, Rouvy, MyWhoosh)
   - Verify range and reliability
   - Ensure no interference with other BLE devices (trainers, heart rate monitors)

---

## Certification Program

To ensure quality and compatibility, SwiftControl offers a voluntary certification program for device manufacturers. See [CERTIFICATION.md](CERTIFICATION.md) for details.

Certified devices receive:
- **Official listing** in the SwiftControl device directory
- **Compatibility badge** for marketing materials
- **Technical support** for implementation
- **Button mapping presets** included in participating apps

---

## Version History

- **Version 1.0** (Current)
  - Initial protocol specification
  - BLE and mDNS transport definitions
  - Standard button mappings
  - Certification program launch

---

## References

- [Bluetooth SIG - GATT Services](https://www.bluetooth.com/specifications/gatt/services/)
- [Apple Core Bluetooth Programming Guide](https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/CoreBluetooth_concepts/)
- [mDNS/Bonjour Specification (RFC 6762)](https://tools.ietf.org/html/rfc6762)

---

## License

The SwiftControl Protocol specification is released under the [MIT License](LICENSE), allowing free implementation in both commercial and open-source projects.

---

## Contact & Contributions

For questions, suggestions, or contributions, please refer to the repository documentation.

The protocol is designed to evolve with community feedback while maintaining backward compatibility.
