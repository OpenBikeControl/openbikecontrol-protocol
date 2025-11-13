# SwiftControl Protocol

An open and open-source protocol for wireless input controllers to interact with cycling trainer applications via mDNS or Bluetooth.

## Overview

SwiftControl enables standardized communication between BLE/network controllers and trainer apps. The protocol supports:

- **Virtual gear shifting** for smart trainer devices
- **On-screen navigation** (menus, route selection, steering)
- **Social features** (emotes, reactions)
- **Training controls** (ERG adjustments, workout navigation)
- **Custom actions** specific to each app

## Why SwiftControl?

- ✅ **Open Standard** - No licensing fees or proprietary restrictions
- ✅ **Easy to Implement** - Simple data format for both apps and devices
- ✅ **Dual Connectivity** - Works via BLE or network (mDNS/Direct Connect)
- ✅ **Apple Compatible** - No reliance on manufacturer data fields
- ✅ **Already Adopted** - Compatible with existing "Direct Connect" implementations

## Documentation

- **[Protocol Specification](PROTOCOL.md)** - Complete technical specification for BLE and mDNS protocols
- **[Certification Program](CERTIFICATION.md)** - Device manufacturer certification process and benefits

## Quick Start

### For App Developers

1. Review the [Protocol Specification](PROTOCOL.md)
2. Implement BLE service discovery for UUID `d273f680-d548-419d-b9d1-fa0472345229`
3. Subscribe to button state notifications (characteristic `d273f681-d548-419d-b9d1-fa0472345229`)
4. Map button IDs to your app's actions
5. (Optional) Implement mDNS discovery for network-based devices

### For Device Manufacturers

1. Review the [Protocol Specification](PROTOCOL.md)
2. Implement the SwiftControl BLE service and characteristics
3. Map your physical buttons to standard button IDs
4. Test with major trainer apps
5. (Optional) Apply for [certification](CERTIFICATION.md)

## Supported Actions

| Category | Examples |
|----------|----------|
| **Gear Shifting** | Shift up/down, direct gear selection |
| **Navigation** | D-pad, menu controls, steering |
| **Social** | Wave, thumbs up, ride on, emotes |
| **Training** | ERG +/-, skip interval, pause/resume |
| **View** | Camera angle, HUD toggle, map |
| **Power-ups** | Activate power-ups (game-specific) |

See [Button Mapping](PROTOCOL.md#button-mapping) for complete list.

## Protocol Architecture

### BLE Protocol
- Service UUID: `d273f680-d548-419d-b9d1-fa0472345229`
- Button State Characteristic: `d273f681-d548-419d-b9d1-fa0472345229` (Read, Notify)
- Data Format: `[Button_ID] [State]` pairs
- Notifications sent only on state changes

### mDNS Protocol
- Service Type: `_swiftcontrol._tcp.local.`
- HTTP/WebSocket endpoints for button state
- Compatible with "Direct Connect" implementations

## Certification

SwiftControl offers a [voluntary certification program](CERTIFICATION.md) for device manufacturers:

- Official device listing
- Compatibility badge for marketing
- Button mappings included in apps
- Technical support and testing

**Certification is currently free** for all manufacturers.

## Contributing

Contributions are welcome! Please:

- Open issues for suggestions or questions
- Submit PRs for protocol improvements
- Share feedback from implementations
- Help test with different apps and devices

## License

The SwiftControl Protocol is released under the [MIT License](LICENSE), allowing free implementation in commercial and open-source projects.

## Contact

- **Issues**: [GitHub Issues](https://github.com/jonasbark/swiftcontrol-protocol/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/jonasbark/swiftcontrol-protocol/pulls)

---

Made with ❤️ by the cycling and open-source community
