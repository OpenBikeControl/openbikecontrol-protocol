# OpenBikeControl Protocol Specification

## Overview

OpenBikeControl is an open protocol for wireless input devices to control cycling trainer applications. It enables standardized communication between BLE controllers, apps, and the training app itself.

### Motivation

Many cycling trainer apps support various actions that traditionally require:
- On-screen button clicks
- Keyboard input
- Proprietary BLE controllers

OpenBikeControl provides a unified, open protocol that:
- **Easy to implement** - Simple data format with minimal overhead
- **Open standard** - No licensing fees or proprietary restrictions
- **Dual connectivity** - Supports both BLE and network-based connections
- **Already partially adopted** - Similar technology as the existing "Direct Connect" implementations
- **Apple-friendly** - Does not rely on manufacturer data fields that cannot be emulated on iOS

### Supported Actions

OpenBikeControl enables the following trainer app actions:
- **Virtual gear shifting** - Up/down shifting for smart trainer devices
- **Navigation** - Menu navigation, route selection, steering controls
- **UI controls** - Select, back, confirm buttons
- **Social features** - Emotes (wave, thumbs up, ride on, etc.)
- **Training controls** - ERG mode adjustments, workout skips
- **Custom actions** - App-specific features

## Protocol Architecture

OpenBikeControl uses two transport mechanisms:

1. **[BLE (Bluetooth Low Energy)](BLE.md)** - For direct device-to-app connections, or as a fallback for apps if mDNS is not possible
2. **[mDNS (Multicast DNS)](MDNS.md)** - For network-based connections ("Direct Connect")

Both transports use the identical binary message format (including the message type prefix byte), ensuring consistency across connection types.

### Quick Reference

**BLE Protocol:**
- Service UUID: `d273f680-d548-419d-b9d1-fa0472345229`
- Button State Characteristic (Read/Notify): `d273f681-d548-419d-b9d1-fa0472345229`
- Haptic Feedback Characteristic (Write): `d273f682-d548-419d-b9d1-fa0472345229`
- App Information Characteristic (Write): `d273f683-d548-419d-b9d1-fa0472345229`
- Message types: `0x01` (button state), `0x03` (haptic feedback), `0x04` (app info)
- See [BLE.md](BLE.md) for complete specification

**mDNS Protocol:**
- Service Type: `_openbikecontrol._tcp.local.`
- TCP endpoint: `<device-ip>:<port>`
- Binary data format (identical to BLE)
- Message types: `0x01` (button state), `0x02` (device status), `0x03` (haptic feedback), `0x04` (app info)
- See [MDNS.md](MDNS.md) for complete specification

---

## Button Mapping

### Standard Button IDs

OpenBikeControl defines standard button IDs for common actions. Device manufacturers should map their physical buttons to these standard IDs.

#### Gear Shifting (0x01-0x0F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x01` | Shift Up | Increase virtual gear |
| `0x02` | Shift Down | Decrease virtual gear |
| `0x03` | Gear Set | Direct gear selection (use analog value) |

#### Navigation (0x10-0x1F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x10` | Up | Navigate up in menus |
| `0x11` | Down | Navigate down in menus |
| `0x12` | Left | Navigate left / Look left |
| `0x13` | Right | Navigate right / Look right |
| `0x14` | Select/Confirm | Confirm selection |
| `0x15` | Back/Cancel | Go back / Cancel |
| `0x16` | Menu | Open menu |
| `0x17` | Home | Return to home screen |
| `0x18` | Steer Left | Steer left in-game |
| `0x19` | Steer Right | Steer right in-game |

#### Social/Emotes (0x20-0x2F)

| Button ID | Action | Description |
|-----------|--------|-------------|
| `0x20` | Emote | Send social emote (use analog value to specify emote type) |

**Emote Analog Values:**
- `0x00` = No emote / Released
- `0x01` = Pressed (cycle through emotes)
- `0x02` = Wave
- `0x03` = Thumbs Up
- `0x04` = Hammer Time
- `0x05` = Bell
- `0x06` = Screenshot
- `0x07-0x1F` = Reserved for additional emotes

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
| `0x40` | Camera View | Select camera view (use analog value to specify view) |
| `0x44` | HUD Toggle | Show/hide HUD |
| `0x45` | Map Toggle | Show/hide map |

**Camera View Analog Values:**
- `0x00` = No change / Released
- `0x01` = Pressed (cycle through camera views)
- `0x02` = Camera 1
- `0x03` = Camera 2
- `0x04` = Camera 3
- `0x05` = Camera 4
- `0x06` = Camera 5
- `0x07` = Camera 6
- `0x08` = Camera 7
- `0x09` = Camera 8
- `0x0A` = Camera 9
- `0x0B-0x1F` = Reserved for additional camera views

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

### Multiple Actions Per Button

Hardware or software (such as BikeControl) can send **multiple actions per button press** to maximize flexibility and compatibility across different trainer apps. This allows a single physical button to trigger multiple related actions simultaneously, with the app deciding which action to respond to based on its capabilities.

**Example Use Case:**

A "Plus" button on a controller could send three different actions at once:
- `0x01` (Shift Up) - For apps that support virtual gear shifting
- `0x30` (ERG Up) - For apps that support ERG mode power adjustment
- `0x14` (Select/Confirm) - For apps that use it for menu navigation

**Implementation:**

When a button is pressed, send a single button state message containing all relevant action IDs:
```
[0x01, 0x01, 0x01, 0x30, 0x01, 0x14, 0x01]
```

This means: Shift Up pressed (0x01, 0x01), ERG Up pressed (0x30, 0x01), and Select pressed (0x14, 0x01).

**Benefits:**
- **Compatibility**: Works with any app that supports at least one of the actions
- **Flexibility**: Easy to remap hardware buttons through software configuration
- **Discovery**: Apps communicate supported actions via the App Information Characteristic, allowing devices to optimize button mappings
- **User Experience**: Physical buttons can have consistent behavior across different apps

**Guidelines for Device Manufacturers:**
- Group related actions that make sense together (e.g., shift up, increase resistance, navigate up)
- Allow users to customize which actions are sent per button
- Use the App Information Characteristic to understand which actions the app supports
- Consider providing visual feedback on the device about which actions are active

**Guidelines for App Developers:**
- Process only the button IDs your app supports, ignoring others
- Send the App Information Characteristic after connecting to inform devices of supported actions
- Handle multiple simultaneous button presses gracefully

---

## Implementation Guidelines

### For App Developers

1. **BLE Implementation:**
   - Scan for devices advertising service UUID `d273f680-d548-419d-b9d1-fa0472345229`
   - Connect and discover the Button State characteristic (`d273f681-d548-419d-b9d1-fa0472345229`)
   - Discover the Haptic Feedback characteristic (`d273f682-d548-419d-b9d1-fa0472345229`)
   - Subscribe to notifications for real-time button updates
   - Send haptic feedback commands for tactile feedback
   - Map button IDs to app-specific actions
   - See [BLE.md](BLE.md) for detailed BLE implementation

2. **mDNS Implementation:**
   - Use Bonjour/Zeroconf libraries to discover `_openbikecontrol._tcp.local.` services
   - Connect via TCP for real-time updates
   - Parse TXT records to get device information and service UUIDs
   - Use same binary format as BLE for button states and commands
   - See [MDNS.md](MDNS.md) for detailed mDNS implementation

3. **Button Mapping:**
   - Provide user configuration for custom button mappings
   - Use standard button IDs as defaults
   - Allow users to override mappings for their workflow

4. **Multi-Device Support:**
   - Support connecting multiple OpenBikeControl devices simultaneously
   - Allow users to assign devices to specific action categories

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
   - Support both BLE and mDNS for maximum compatibility
   - Use same binary data format for both BLE and TCP
   - Implement haptic feedback if hardware supports it

3. **Power Management:**
   - Implement BLE sleep modes when inactive
   - Wake on button press
   - Report accurate battery levels

4. **Testing:**
   - Verify range and reliability
   - Ensure no interference with other BLE devices (trainers, heart rate monitors)

---

## Certification Program

To ensure quality and compatibility, OpenBikeControl offers a voluntary certification program for device manufacturers. See [CERTIFICATION.md](CERTIFICATION.md) for details.

Certified devices receive:
- **Official listing** in the OpenBikeControl device directory
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

The OpenBikeControl Protocol specification is released under the [MIT License](LICENSE), allowing free implementation in both commercial and open-source projects.

---

## Contact & Contributions

For questions, suggestions, or contributions, please refer to the repository documentation.

The protocol is designed to evolve with community feedback while maintaining backward compatibility.
