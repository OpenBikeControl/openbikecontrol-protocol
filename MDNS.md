# mDNS Protocol Specification

## Overview

The mDNS (Multicast DNS) implementation provides network-based connectivity for OpenBikeControl devices, similar to the "Direct Connect" protocol. This allows devices to communicate with apps over WiFi/Ethernet networks using TCP sockets.

## Example Implementation
Sometimes it's easier to understand the protocol by looking at a concrete example:
- [Example Implementation for trainer app](https://github.com/OpenBikeControl/openbikecontrol-protocol/tree/main/examples/python/mdns_trainer_app.py)
- [Example Implementation for button controller](https://github.com/OpenBikeControl/openbikecontrol-protocol/tree/main/examples/python/mock_device.py)

---

## Service Discovery

**Service Type:** `_openbikecontrol._tcp.local.`

**Service Name Format:** `<Device Name>._openbikecontrol._tcp.local.`

**TXT Record Fields:**

The TXT record fields mirror BLE advertisement data:

- `version=1` - Protocol version
- `id=<unique-id>` - Unique device identifier (MAC address or serial)
- `name=<device-name>` - Human-readable device name
- `service-uuids=<uuid-list>` - Comma-separated list of service UUIDs, showcasing the hardwares' capabilities
- `manufacturer=<name>` - Device manufacturer
- `model=<model>` - Device model

**Example:**
```
Service: OpenBikeControl Remote._openbikecontrol._tcp.local.
Port: 8080
TXT:
  version=1
  id=aabbccddeeff
  name=OpenBikeControl Remote
  service-uuids=d273f680-d548-419d-b9d1-fa0472345229
  manufacturer=ExampleCorp
  model=SC-100
```

---

## TCP Protocol

Once discovered via mDNS/Bonjour, apps connect to the device using TCP sockets for real-time communication.

**Connection:**
- Apps initiate TCP connection to `<device-ip>:<port>` after discovering the device via mDNS
- Connection should be maintained for the duration of the session
- Reconnection should be automatic if connection is lost

---

## Data Format

All messages use the same binary format as the BLE protocol for consistency and efficiency.

### Button State Message (Device to App)

**Message Type:** `0x01`

Sent when one or more button states change.

**Data Format:**

```
[Message_Type] [Button_ID_1] [State_1] [Button_ID_2] [State_2] ... [Button_ID_N] [State_N]
```

- **Message_Type** (1 byte): Always `0x01` for button state messages
- **Button_ID** (1 byte): Identifier for the button (see [Button Mapping](PROTOCOL.md#button-mapping))
- **State** (1 byte): Current state of the button
  - `0x00` = Released/Off
  - `0x01` = Pressed/On
  - `0x02-0xFF` = Analog value (for analog inputs like triggers or joysticks, where 0x02 = minimum, 0xFF = maximum)

**Example Messages:**

```
// Single button press (button 0x01 pressed)
[0x01, 0x01, 0x01]

// Multiple buttons (button 0x01 pressed, button 0x02 released)
[0x01, 0x01, 0x01, 0x02, 0x00]

// Analog input (button 0x10 at 50% = 0x80)
[0x01, 0x10, 0x80]
```

---

### Device Status Message (Device to App)

**Message Type:** `0x02`

Sent periodically or on status changes.

**Data Format:**

```
[Message_Type] [Battery] [Connected]
```

- **Message_Type** (1 byte): Always `0x02` for device status messages
- **Battery** (1 byte): Battery level percentage (0-100), or `0xFF` if not applicable
- **Connected** (1 byte): Device connection state
  - `0x00` = Not connected/ready
  - `0x01` = Connected and ready for input

**Example Message:**

```
// Device with 85% battery, connected
[0x02, 0x55, 0x01]

// Device without battery monitoring, connected
[0x02, 0xFF, 0x01]
```

---

### Haptic Feedback Command (App to Device)

**Message Type:** `0x03`

Sent by the app to trigger haptic feedback on the device.

**Data Format:**

```
[Message_Type] [Pattern] [Duration] [Intensity]
```

- **Message_Type** (1 byte): Always `0x03` for haptic feedback commands
- **Pattern** (1 byte): Type of haptic feedback pattern
  - `0x00` = No haptic (stop)
  - `0x01` = Single short vibration
  - `0x02` = Double pulse
  - `0x03` = Triple pulse
  - `0x04` = Long vibration
  - `0x05` = Success pattern (crescendo)
  - `0x06` = Warning pattern (two short pulses)
  - `0x07` = Error pattern (three short pulses)
  - `0x08-0xFF` = Reserved for future patterns

- **Duration** (1 byte): Duration of the haptic feedback in units of 10ms
  - `0x00` = Use default duration for pattern
  - `0x01-0xFF` = Duration in 10ms units (e.g., `0x0A` = 100ms, `0x64` = 1000ms)
  - Maximum recommended duration: `0x64` (1000ms)

- **Intensity** (1 byte): Vibration intensity level
  - `0x00` = Use default intensity for pattern
  - `0x01-0x7F` = Low to medium intensity
  - `0x80-0xFF` = Medium to maximum intensity

**Example Commands:**

```
// Single short vibration with default settings
[0x03, 0x01, 0x00, 0x00]

// Double pulse, 200ms duration, medium intensity (128)
[0x03, 0x02, 0x14, 0x80]

// Success pattern with maximum intensity
[0x03, 0x05, 0x00, 0xFF]

// Stop all haptic feedback
[0x03, 0x00, 0x00, 0x00]
```

---

### App Information (App to Device)

**Message Type:** `0x04`

Sent by the app to inform the device about the app's identity and capabilities. This allows devices to provide better user feedback, customize button mappings, or enable app-specific features.

**Data Format:**

```
[Message_Type] [Version] [App_ID_Length] [App_ID...] [App_Version_Length] [App_Version...] [Button_Count] [Button_IDs...]
```

- **Message_Type** (1 byte): Always `0x04` for app information messages
- **Version** (1 byte): Format version, currently `0x01`
- **App_ID_Length** (1 byte): Length of the App ID string (0-32 characters)
- **App_ID** (variable): UTF-8 encoded app identifier string
  - Should be lowercase, alphanumeric with optional hyphens/underscores
  - Examples: `"zwift"`, `"trainerroad"`, `"rouvy"`, `"my-custom-app"`
- **App_Version_Length** (1 byte): Length of the App Version string (0-32 characters)
- **App_Version** (variable): UTF-8 encoded app version string
  - Recommended to follow semantic versioning format
  - Examples: `"1.52.0"`, `"2.0.1-beta"`
- **Button_Count** (1 byte): Number of supported button IDs (0-255)
  - `0` indicates the app supports all button types
- **Button_IDs** (variable): Array of button ID bytes
  - Each byte represents a supported button ID from [Button Mapping](PROTOCOL.md#button-mapping)
  - Devices can use this to provide visual feedback or customize layouts

**Example Data:**

```
// App: "zwift", Version: "1.52.0", Buttons: [0x01, 0x02, 0x10, 0x14]
[0x04, 0x01, 0x05, 'z', 'w', 'i', 'f', 't', 0x06, '1', '.', '5', '2', '.', '0', 0x04, 0x01, 0x02, 0x10, 0x14]
```

**Usage:**
- Apps SHOULD send this message immediately after establishing the TCP connection
- Apps MAY send updated information if capabilities change during the session
- Devices SHOULD handle the absence of this message gracefully (assume all buttons supported)
- The app information is cleared when the TCP connection is closed

**Note:** This message is **optional** for apps to implement, but the information is important for devices to provide the best user experience (e.g., highlighting supported buttons, customizing layouts for specific apps).

---

## Implementation Guidelines

### For App Developers

1. **Service Discovery:**
   - Use Bonjour/Zeroconf libraries to discover `_openbikecontrol._tcp.local.` services
   - Parse TXT records to get device information
   - Extract IP address and port for TCP connection

2. **TCP Connection:**
   - Connect to `<device-ip>:<port>` using a standard TCP socket
   - Implement automatic reconnection on connection loss
   - Handle binary message parsing and routing

3. **Message Handling:**
   - Read messages byte by byte from the TCP stream
   - First byte indicates the message type
   - Parse remaining bytes according to message type format
   - Button state messages (0x01) have variable length depending on number of buttons
   - Status messages (0x02) are always 3 bytes
   - Haptic feedback commands (0x03) are always 4 bytes
   - App info messages (0x04) have variable length

4. **Button Handling:**
   - Listen for button state messages (type 0x01)
   - Map button IDs to app-specific actions (see [Button Mapping](PROTOCOL.md#button-mapping))
   - Handle multiple simultaneous button presses

5. **Haptic Feedback:**
   - Send haptic feedback messages (type 0x03) to provide tactile feedback
   - Use appropriate patterns for different actions
   - Duration is in 10ms units, intensity from 0-255

6. **Status Monitoring:**
   - Monitor device status messages (type 0x02) for battery level
   - Handle disconnection gracefully
   - Display connection status to user

### For Device Manufacturers

1. **Network Setup:**
   - Implement WiFi connectivity (Station mode or AP mode)
   - Advertise mDNS service on network
   - Implement TCP server

2. **Service Advertisement:**
   - Advertise `_openbikecontrol._tcp.local.` service
   - Include all required TXT record fields
   - Update TXT records if device information changes

3. **TCP Server:**
   - Listen on configured port for incoming TCP connections
   - Support multiple simultaneous connections
   - Send button state messages as binary data
   - Handle haptic feedback and app info commands from apps

4. **Message Handling:**
   - Send button state messages (type 0x01) only on state changes
   - Send periodic device status updates (type 0x02) every 30-60 seconds
   - Process haptic feedback commands (type 0x03) immediately
   - Process app info messages (type 0x04) for device customization
   - Use the same binary format as BLE for consistency

5. **Power Management:**
   - Consider WiFi power consumption
   - Implement sleep modes when inactive
   - Wake on button press or network activity

---

## Comparison with BLE

| Feature | BLE | mDNS/TCP |
|---------|-----|----------|
| **Range** | 10-30m | WiFi network range |
| **Latency** | 7-15ms | 20-50ms |
| **Setup** | Pairing required | Network connection required |
| **Battery** | Low power | Higher power (WiFi) |
| **Compatibility** | Direct device support | Works through proxies/bridges |
| **Multi-device** | Limited | Easy multiple connections |
| **Data Format** | Binary (byte array) | Binary (byte array) - **same format as BLE** |

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [BLE Protocol Specification](BLE.md)
- [Button Mapping](PROTOCOL.md#button-mapping)
- [Certification Program](CERTIFICATION.md)
