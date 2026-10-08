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

- `version=1` - Highest protocol version the device supports (`1` or `2`). Devices advertising `version=2` support [framed TCP messages](#message-framing-version-2) and MUST still accept version 1 apps
- `id=<unique-id>` - Unique device identifier (MAC address or serial)
- `name=<device-name>` - Human-readable device name
- `service-uuids=<uuid-list>` - Comma-separated list of service UUIDs, showcasing the hardwares' capabilities. Controllers list `d273f680-d548-419d-b9d1-fa0472345229`; smart trainers list the Trainer Service `d273f690-d548-419d-b9d1-fa0472345229` (see [TRAINER.md](TRAINER.md)); smart bikes list both
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

In version 1, messages are written to the TCP stream back to back without a length,
so a receiver cannot reliably tell where one message ends and the next begins when
TCP delivers several writes in one read. Version 2 adds a length prefix; see
[Message Framing (Version 2)](#message-framing-version-2).

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

### Virtual Shifting Control (App to Trainer)

**Message Type:** `0x05`

Optional, for smart trainers and smart bikes. Sent by the app to set the simulated gear
ratio, rider mass and bike mass.

**Data Format:**

```
[0x05] [Version] [Mode] [Gear_Ratio_L] [Gear_Ratio_H] [Rider_Mass_L] [Rider_Mass_H] [Bike_Mass_L] [Bike_Mass_H] [Gear_Index] [Gear_Count]
```

Fixed length of 11 bytes. Field definitions, examples and behaviour are specified in
[VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md#virtual-shifting-control-app-to-trainer).

---

### Virtual Shifting State (Trainer to App)

**Message Type:** `0x06`

Optional, for smart trainers and smart bikes. Sent by the trainer once right after the TCP
connection is accepted (so the app can detect support) and whenever its state changes.

**Data Format:**

```
[0x06] [Version] [Flags] [Gear_Ratio_L] [Gear_Ratio_H] [Gear_Index] [Gear_Count] [Front_Index] [Front_Count] [Rear_Index] [Rear_Count]
```

Fixed length of 11 bytes. Field definitions, examples and behaviour are specified in
[VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md#virtual-shifting-state-trainer-to-app).

---

### Ride State (App to Trainer)

**Message Type:** `0x07`

Optional, for smart trainers and smart bikes. Sent by the app at 1–4 Hz with the
simulated bike speed so the trainer can align its inertia and gravity simulation with the
on-screen speed.

**Data Format:**

```
[0x07] [Version] [Speed_L] [Speed_H] [Reserved]
```

Fixed length of 5 bytes. Field definitions, examples and behaviour are specified in
[VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md#ride-state-app-to-trainer).

---

### Trainer Control (App to Trainer)

**Message Type:** `0x08`

Optional, for smart trainers and smart bikes. Sets mode (idle, simulation, target
power, target resistance) and the simulation or target values.

**Data Format:**

```
[0x08] [Version] [Mode] [Target_Power_L] [Target_Power_H] [Target_Resistance_L] [Target_Resistance_H] [Grade_L] [Grade_H] [Wind_L] [Wind_H] [CRR_L] [CRR_H] [CW_L] [CW_H] [Wheel_Circ_L] [Wheel_Circ_H]
```

Fixed length of 17 bytes. Field definitions, examples and behaviour are specified in
[TRAINER.md](TRAINER.md#trainer-control-app-to-trainer).

---

### Trainer Data (Trainer to App)

**Message Type:** `0x09`

Optional, for smart trainers and smart bikes. Power, cadence, speed, applied resistance
and grade, sent at 1–4 Hz to every connected client.

**Data Format:**

```
[0x09] [Version] [Flags] [Power_L] [Power_H] [Cadence_L] [Cadence_H] [Speed_L] [Speed_H] [Resistance_L] [Resistance_H] [Grade_L] [Grade_H]
```

Fixed length of 13 bytes. Field definitions, examples and behaviour are specified in
[TRAINER.md](TRAINER.md#trainer-data-trainer-to-app).

---

### Trainer Status (Trainer to App)

**Message Type:** `0x0A`

Mandatory for smart trainers and smart bikes. Capabilities, limits, control ownership
and active mode. Sent right after the connection is established (after version
negotiation, if any) and whenever any field changes. Because the `Control` field is
per client, the trainer sends it to every connected client when ownership changes.

**Data Format:**

```
[0x0A] [Version] [Control] [Mode] [Capabilities_L] [Capabilities_H] [Max_Power_L] [Max_Power_H] [Max_Resistance_L] [Max_Resistance_H] [Max_Grade_L] [Max_Grade_H] [Min_Grade_L] [Min_Grade_H] [Calibration]
```

Fixed length of 15 bytes. Field definitions, examples and behaviour are specified in
[TRAINER.md](TRAINER.md#trainer-status-trainer-to-app).

---

## Message Framing (Version 2)

> **Status: Draft.** This section is a proposal and may change before version 2 is final.

### Why

TCP is a byte stream, not a message stream. Two messages written separately can
arrive in a single read, and one message can be split across two reads. Version 1
has no length field, so a receiver that treats each read as one message will
misparse merged messages:

```
Written:  [0x01, 0x1B, 0x85]  [0x01, 0x1B, 0x86]
Read as:  [0x01, 0x1B, 0x85, 0x01, 0x1B, 0x86]
Parsed:   0x1B = 0x85, 0x01 (Shift Up) = 0x1B, 0x86 = <dangling>
```

The middle pair is read as a Shift Up press. This rarely happens with occasional
button presses, but becomes common with continuously streamed values such as the
Steering Angle (`0x1B`).

### Frame Format

In version 2, every TCP message in both directions is prefixed with its length:

```
[Length_Hi] [Length_Lo] [Message_Type] [Payload...]
```

- **Length** (2 bytes, big-endian): number of bytes that follow, i.e. Message_Type + Payload. MUST be at least 1 and at most 512.
- **Message_Type** and **Payload**: unchanged from version 1.

Example: a button state message `[0x01, 0x1B, 0x94]` is sent as
`[0x00, 0x03, 0x01, 0x1B, 0x94]`.

Receivers MUST buffer incoming bytes and only process a message once all `Length`
bytes have arrived. Receivers MUST skip (but still consume) messages with an unknown
Message_Type. A receiver that reads a Length of 0 or above 512 MUST close the
connection.

Framing applies to TCP only. BLE is unchanged: each notification or write is already
exactly one message.

### Negotiation

Framing is opt-in per connection, so version 1 apps keep working with version 2 devices.

**Protocol Version Message (Message Type `0xF0`), App to Device and Device to App:**

```
[0x00, 0x02, 0xF0, Version]
```

Always sent framed. `Version` is the requested (app) or accepted (device) protocol
version, currently `0x02`.

1. A version 2 app connecting to a device that advertises `version=2` MUST send the
   Protocol Version message `[0x00, 0x02, 0xF0, 0x02]` as the first bytes on the connection.
2. A version 2 device MUST NOT send anything on a new connection until it has received
   the first bytes from the app, or until 500 ms have passed without the app sending
   anything (button changes in this window MAY be queued).
3. If the first byte received is `0x00`, the device reads the Protocol Version message,
   replies with `[0x00, 0x02, 0xF0, 0x02]`, and uses framing for the rest of the
   connection in both directions.
4. Otherwise (the app sent a version 1 message first, or nothing within 500 ms) the
   device uses version 1 framing for the rest of the connection.
5. The app MUST NOT send any further messages until it has received the device's
   Protocol Version reply. If no reply arrives within 2 seconds, the app SHOULD close
   the connection and reconnect using version 1.

The first byte of a framed message is `0x00` for all valid lengths up to 255 and at
most `0x02` above that. `0x00` is never a valid version 1 Message_Type, so the device
can tell the two apart from the first byte alone. Version 1 devices ignore the
unknown leading bytes.

### Version 1 Mitigations

Until both sides support version 2:

- Devices SHOULD disable Nagle's algorithm (`TCP_NODELAY`) and write each message
  with a single call, which makes merged reads less likely but does not prevent them.
- Devices SHOULD NOT stream values faster than needed (see the update rate for
  Steering Angle).

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
   - For version 2 connections, read the 2-byte length first and buffer until the full message has arrived (see [Message Framing](#message-framing-version-2))
   - First byte indicates the message type
   - Parse remaining bytes according to message type format
   - Button state messages (0x01) have variable length depending on number of buttons
   - Status messages (0x02) are always 3 bytes
   - Haptic feedback commands (0x03) are always 4 bytes
   - App info messages (0x04) have variable length
   - Virtual shifting messages (0x05, 0x06) are always 11 bytes
   - Ride state messages (0x07) are always 5 bytes
   - Trainer control (0x08), data (0x09) and status (0x0A) are 17, 13 and 15 bytes

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
   - Smart trainers: process Virtual Shifting Control (type 0x05) and send Virtual Shifting State (type 0x06) on connect and on change
   - Smart trainers: optionally use Ride State (type 0x07) as the speed reference for inertia and gravity simulation
   - Smart trainers: send Trainer Status (type 0x0A) on connect and on change, stream Trainer Data (type 0x09), and accept Trainer Control (type 0x08) from the owning client only (see [TRAINER.md](TRAINER.md#control-ownership))
   - Use the same binary format as BLE for consistency

5. **Power Management:**
   - Consider WiFi power consumption
   - Implement sleep modes when inactive
   - Wake on button press or network activity

---

## Comparison with BLE

| Feature           | BLE                   | mDNS/TCP                                     |
|-------------------|-----------------------|----------------------------------------------|
| **Range**         | 10-30m                | WiFi network range                           |
| **Latency**       | 7-15ms                | 20-50ms                                      |
| **Setup**         | Pairing required      | Network connection required                  |
| **Battery**       | Low power             | Higher power (WiFi)                          |
| **Compatibility** | Direct device support | Works through proxies/bridges                |
| **Multi-device**  | Limited               | Easy multiple connections                    |
| **Data Format**   | Binary (byte array)   | Binary (byte array) - **same format as BLE** |

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [BLE Protocol Specification](BLE.md)
- [Virtual Shifting Extension](VIRTUAL_SHIFTING.md)
- [Trainer Profile](TRAINER.md)
- [Button Mapping](PROTOCOL.md#button-mapping)
- [Certification Program](CERTIFICATION.md)
