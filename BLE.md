# BLE Protocol Specification

## Overview

The Bluetooth Low Energy (BLE) implementation provides direct device-to-app connections for OpenBikeControl devices.

---

## Service UUID

**Primary Service UUID:** `d273f680-d548-419d-b9d1-fa0472345229`

This service UUID is used for OpenBikeControl device advertisement and discovery.

---

## Characteristics

### 1. Button State Characteristic (READ/NOTIFY)

**UUID:** `d273f681-d548-419d-b9d1-fa0472345229`

**Properties:** Read, Notify

**Description:** Reports the state of all buttons on the controller.

**Data Format:**

The characteristic value consists of button state pairs:

```
[Button_ID_1] [State_1] [Button_ID_2] [State_2] ... [Button_ID_N] [State_N]
```

- **Button_ID** (1 byte): Identifier for the button (see [Button Mapping](PROTOCOL.md#button-mapping) section)
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

---

### 2. Haptic Feedback Characteristic (WRITE)

**UUID:** `d273f682-d548-419d-b9d1-fa0472345229`

**Properties:** Write, Write Without Response

**Description:** Receives haptic feedback commands from the app to provide tactile feedback on the device.

**Data Format:**

The characteristic value consists of three bytes defining the haptic feedback pattern:

```
[Pattern] [Duration] [Intensity]
```

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
  - `0x00` = No vibration (off)
  - `0x01-0x7F` = Low to medium intensity
  - `0x80-0xFF` = Medium to maximum intensity
  - `0x00` = Use default intensity for pattern

**Example Commands:**

```
// Single short vibration with default settings
[0x01, 0x00, 0x00]

// Double pulse, 200ms duration, medium intensity (128)
[0x02, 0x14, 0x80]

// Success pattern with maximum intensity
[0x05, 0x00, 0xFF]

// Stop all haptic feedback
[0x00, 0x00, 0x00]
```

**Write Behavior:**

- Apps can send haptic feedback commands at any time
- Commands are executed immediately upon receipt
- If a new command is received while haptic feedback is active, the current pattern is interrupted and the new pattern starts immediately
- Devices should acknowledge commands if "Write" property is used, but may use "Write Without Response" for lower latency
- If the device does not support haptic feedback, it should accept the writes but perform no action

**Use Cases:**

- Confirmation feedback when button press is registered
- Success/error feedback for virtual gear changes
- Navigation feedback (e.g., reaching menu boundaries)
- Power-up activation confirmation
- Training milestone celebrations

---

## Standard BLE Services

OpenBikeControl devices MUST implement the following standard BLE services:

### Device Information Service (0x180A)

Required characteristics:
- **Manufacturer Name String** (0x2A29) - Device manufacturer
- **Model Number String** (0x2A24) - Device model
- **Serial Number String** (0x2A25) - Unique device serial
- **Hardware Revision String** (0x2A27) - Hardware version
- **Firmware Revision String** (0x2A26) - Firmware version
- **Software Revision String** (0x2A28) - Optional software version

### Battery Service (0x180F)

Required for battery-powered devices:
- **Battery Level** (0x2A19) - Current battery percentage (0-100)

---

## Advertisement Requirements

**CRITICAL:** OpenBikeControl devices MUST NOT rely on manufacturer-specific data in BLE advertisements. This restriction ensures compatibility with Apple iOS devices, which do not allow apps to emulate manufacturer data.

**Advertisement Data:**

- **Service UUIDs**: Must advertise the primary service UUID `d273f680-d548-419d-b9d1-fa0472345229`
- **Flags**: General discoverable mode, BR/EDR not supported

**Example Advertisement:**
```
Flags: 0x06 (LE General Discoverable, BR/EDR not supported)
Complete List of 128-bit Service UUIDs: d273f680-d548-419d-b9d1-fa0472345229
```

---

## Connection Parameters

Recommended BLE connection parameters for optimal performance:

- **Connection Interval**: 7.5-15ms (for low latency)
- **Slave Latency**: 0 (for immediate response)
- **Supervision Timeout**: 4 seconds
- **MTU Size**: 23 bytes minimum, 247 bytes preferred

---

## Implementation Guidelines

### For App Developers

1. **Device Discovery:**
   - Scan for devices advertising service UUID `d273f680-d548-419d-b9d1-fa0472345229`
   - Filter by device name or manufacturer if needed

2. **Connection:**
   - Connect and discover the OpenBikeControl service
   - Discover Button State characteristic (`d273f681-d548-419d-b9d1-fa0472345229`)
   - Discover Haptic Feedback characteristic (`d273f682-d548-419d-b9d1-fa0472345229`)
   - Subscribe to Button State notifications for real-time button updates

3. **Button Handling:**
   - Map button IDs to app-specific actions (see [Button Mapping](PROTOCOL.md#button-mapping))
   - Parse notification data to extract button state changes
   - Handle multiple simultaneous button presses

4. **Haptic Feedback:**
   - Send haptic commands to provide tactile feedback
   - Use appropriate patterns for different actions (success, error, confirmation)
   - Consider user preferences for haptic intensity

### For Device Manufacturers

1. **Hardware:**
   - Use reliable button switches for digital inputs
   - Consider hall-effect sensors for analog inputs
   - Include vibration motor for haptic feedback (optional but recommended)
   - Include battery monitoring circuitry for battery level reporting

2. **Firmware:**
   - Implement efficient button debouncing (10-50ms)
   - Only send notifications on state changes
   - Batch multiple button changes in one notification
   - Implement haptic feedback patterns if hardware supports it
   - Handle gracefully if haptic commands are received but hardware doesn't support it

3. **Power Management:**
   - Implement BLE sleep modes when inactive
   - Wake on button press
   - Report accurate battery levels
   - Consider power consumption of haptic motor

4. **Testing:**
   - Verify range and reliability
   - Test haptic feedback patterns and intensities
   - Ensure no interference with other BLE devices (trainers, heart rate monitors)
   - Validate notification timing and latency

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [mDNS Protocol Specification](MDNS.md)
- [Button Mapping](PROTOCOL.md#button-mapping)
- [Certification Program](CERTIFICATION.md)
