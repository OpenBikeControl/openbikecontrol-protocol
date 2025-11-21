# BLE Protocol Specification

## Overview

The Bluetooth Low Energy (BLE) implementation provides direct device-to-app connections for OpenBikeControl devices.

---

## Example Implementation
Sometimes it's easier to understand the protocol by looking at a concrete example:
- [Example Implementation for trainer app](https://github.com/OpenBikeControl/openbikecontrol-protocol/tree/main/examples/python/ble_trainer_app.py)
- [Example Implementation for button controller](https://github.com/OpenBikeControl/openbikecontrol-protocol/tree/main/examples/python/mock_device_ble.py)

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

### 3. App Information Characteristic (WRITE)

**UUID:** `d273f683-d548-419d-b9d1-fa0472345229`

**Properties:** Write, Write Without Response

**Description:** Receives information from the app about its identity and capabilities. This allows devices to provide better user feedback, customize button mappings, or enable app-specific features.

**Data Format:**

The characteristic value uses a compact binary format for efficient transmission:

```
[Version] [App_ID_Length] [App_ID...] [App_Version_Length] [App_Version...] [Button_Count] [Button_IDs...]
```

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
[0x01, 0x05, 'z', 'w', 'i', 'f', 't', 0x06, '1', '.', '5', '2', '.', '0', 0x04, 0x01, 0x02, 0x10, 0x14]
```

**Write Behavior:**

- Apps SHOULD send this information immediately after connecting to the device
- Apps MAY send updated information if capabilities change during the session
- Commands are processed immediately upon receipt
- Devices SHOULD handle the absence of this message gracefully (assume all buttons supported)
- If a new message is received, it replaces the previous app information
- Devices should acknowledge commands if "Write" property is used, but may use "Write Without Response" for simplicity
- The written value will be emptied on every disconnect

**Note:** This characteristic is **optional** for apps to implement, but the information is important for devices to provide the best user experience (e.g., highlighting supported buttons, customizing layouts for specific apps).

**Use Cases:**

- Device displays app name/version on screen or LEDs
- Device highlights or enables only supported buttons
- Device customizes button layouts for popular apps
- Device logs connection history for diagnostics
- Device provides app-specific haptic patterns or feedback

**Maximum Payload Size:**

The maximum size of this characteristic depends on MTU, but should aim to fit within standard MTU (23 bytes data):
- Version (1) + Max App ID (1+32) + Max Version (1+32) + Button Count (1) = 68 bytes minimum
- Recommended to keep App ID + Version under 40 characters combined for compatibility
- For longer values, increase MTU negotiation or truncate gracefully

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
   - Filter by device name if needed

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
   - Optional: Consider hall-effect sensors for analog inputs
   - Optional: Include vibration motor for haptic feedback
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
