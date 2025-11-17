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
- **Already partially adopted** - Similar to existing "Direct Connect" implementations
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

Both transports use the same logical data format, ensuring consistency across connection types.

### Quick Reference

**BLE Protocol:**
- Service UUID: `d273f680-d548-419d-b9d1-fa0472345229`
- Button State Characteristic (Read/Notify): `d273f681-d548-419d-b9d1-fa0472345229`
- Haptic Feedback Characteristic (Write): `d273f682-d548-419d-b9d1-fa0472345229`
- See [BLE.md](BLE.md) for complete specification

**mDNS Protocol:**
- Service Type: `_openbikecontrol._tcp.local.`
- WebSocket endpoint: `ws://<device-ip>:<port>/api/ws`
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
| `0x10` | Up | Navigate up / Steer left |
| `0x11` | Down | Navigate down / Steer right |
| `0x12` | Left | Navigate left / Look left |
| `0x13` | Right | Navigate right / Look right |
| `0x14` | Select/Confirm | Confirm selection |
| `0x15` | Back/Cancel | Go back / Cancel |
| `0x16` | Menu | Open menu |
| `0x17` | Home | Return to home screen |

#### Social/Emotes (0x20-0x2F)

| Button ID | Action      | Description |
|-----------|-------------|-------------|
| `0x20`    | Wave        | Wave to other riders |
| `0x21`    | Thumbs Up   | Give thumbs up |
| `0x22`    | Hammer Time | Activate power-up |
| `0x23`    | Bell        | Ring bell |
| `0x24`    | Screenshot  | Take screenshot |

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
   - Connect via WebSocket for real-time updates
   - Parse TXT records to get device information and service UUIDs
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
