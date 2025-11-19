# mDNS Protocol Specification

## Overview

The mDNS (Multicast DNS) implementation provides network-based connectivity for OpenBikeControl devices, similar to the "Direct Connect" protocol. This allows devices to communicate with apps over WiFi/Ethernet networks.

## Example Implementation
Sometimes it's easier to understand the protocol by looking at a concrete example:
- [Example Implementation for trainer app](examples/python/mdns_trainer_app.py)
- [Example Implementation for button controller](examples/python/mock_device.py)

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

## WebSocket Protocol

Once discovered via mDNS/Bonjour, apps connect to the device using WebSocket for real-time communication.

**Endpoint:** `ws://<device-ip>:<port>/api/ws`

**Connection:**
- Apps initiate WebSocket connection after discovering the device via mDNS
- Connection should be maintained for the duration of the session
- Reconnection should be automatic if connection is lost

---

## Message Format

All messages use JSON format for easy parsing and extensibility.

### Button State Change (Device to App)

Sent when one or more button states change.

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

**Fields:**
- `type`: Always `"button_state"`
- `timestamp`: Unix timestamp in milliseconds
- `buttons`: Array of button state changes
  - `id`: Button ID (see [Button Mapping](PROTOCOL.md#button-mapping))
  - `state`: Button state (0 = released, 1 = pressed, 2-255 = analog value)

---

### Device Status Update (Device to App)

Sent periodically or on status changes.

```json
{
  "type": "device_status",
  "timestamp": 1699887600000,
  "battery": 85,
  "connected": true
}
```

**Fields:**
- `type`: Always `"device_status"`
- `timestamp`: Unix timestamp in milliseconds
- `battery`: Battery level percentage (0-100), or `null` if not applicable
- `connected`: Boolean indicating if device is ready for input

---

### Haptic Feedback Command (App to Device)

Sent by the app to trigger haptic feedback on the device.

```json
{
  "type": "haptic_feedback",
  "pattern": "vibrate",
  "duration": 100,
  "intensity": 128
}
```

**Fields:**
- `type`: Always `"haptic_feedback"`
- `pattern`: Haptic feedback pattern (string)
  - `"none"` - No haptic (stop)
  - `"short"` - Single short vibration
  - `"double"` - Double pulse
  - `"triple"` - Triple pulse
  - `"long"` - Long vibration
  - `"success"` - Success pattern (crescendo)
  - `"warning"` - Warning pattern (two short pulses)
  - `"error"` - Error pattern (three short pulses)
- `duration`: Duration in milliseconds (0 = use default for pattern)
- `intensity`: Vibration intensity (0-255, where 0 = off, 255 = maximum, 0 = use default)

---

### Haptic Feedback Response (Device to App)

Sent by the device after processing a haptic feedback command.

```json
{
  "type": "haptic_feedback_response",
  "timestamp": 1699887600000,
  "success": true
}
```

**Fields:**
- `type`: Always `"haptic_feedback_response"`
- `timestamp`: Unix timestamp in milliseconds
- `success`: Boolean indicating if haptic feedback was executed successfully

---

## Implementation Guidelines

### For App Developers

1. **Service Discovery:**
   - Use Bonjour/Zeroconf libraries to discover `_openbikecontrol._tcp.local.` services
   - Parse TXT records to get device information
   - Extract IP address and port for WebSocket connection

2. **WebSocket Connection:**
   - Connect to `ws://<device-ip>:<port>/api/ws`
   - Implement automatic reconnection on connection loss
   - Handle JSON message parsing and routing

3. **Button Handling:**
   - Listen for `button_state` messages
   - Map button IDs to app-specific actions (see [Button Mapping](PROTOCOL.md#button-mapping))
   - Handle multiple simultaneous button presses

4. **Haptic Feedback:**
   - Send `haptic_feedback` messages to provide tactile feedback
   - Use appropriate patterns for different actions
   - Wait for `haptic_feedback_response` if confirmation is needed

5. **Status Monitoring:**
   - Monitor `device_status` messages for battery level
   - Handle disconnection gracefully
   - Display connection status to user

### For Device Manufacturers

1. **Network Setup:**
   - Implement WiFi connectivity (Station mode or AP mode)
   - Advertise mDNS service on network
   - Implement HTTP/WebSocket server

2. **Service Advertisement:**
   - Advertise `_openbikecontrol._tcp.local.` service
   - Include all required TXT record fields
   - Update TXT records if device information changes

3. **WebSocket Server:**
   - Implement WebSocket endpoint at `/api/ws`
   - Support multiple simultaneous connections
   - Send button state changes as JSON messages
   - Handle haptic feedback commands from app

4. **Message Handling:**
   - Send `button_state` messages only on state changes
   - Send periodic `device_status` updates (every 30-60 seconds)
   - Process `haptic_feedback` commands and respond with `haptic_feedback_response`
   - Include accurate timestamps in all messages

5. **Power Management:**
   - Consider WiFi power consumption
   - Implement sleep modes when inactive
   - Wake on button press or network activity

---

## Comparison with BLE

| Feature | BLE | mDNS/WebSocket |
|---------|-----|----------------|
| **Range** | 10-30m | WiFi network range |
| **Latency** | 7-15ms | 20-50ms |
| **Setup** | Pairing required | Network connection required |
| **Battery** | Low power | Higher power (WiFi) |
| **Compatibility** | Direct device support | Works through proxies/bridges |
| **Multi-device** | Limited | Easy multiple connections |

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [BLE Protocol Specification](BLE.md)
- [Button Mapping](PROTOCOL.md#button-mapping)
- [Certification Program](CERTIFICATION.md)
