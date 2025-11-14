# OpenBikeControl Examples

This directory contains example implementations demonstrating how to integrate OpenBikeControl support into trainer applications.

## Available Examples

### Python Examples

**Location:** [`python/`](python/)

Python example implementations for trainer applications showing:
- **BLE Trainer App**: Connect to OpenBikeControl devices via Bluetooth Low Energy
- **mDNS Trainer App**: Connect to devices via network using mDNS/Zeroconf
- **Mock Device**: Simulate a device for testing without hardware
- **Unit Tests**: Verify core functionality

See the [Python Examples README](python/README.md) for detailed usage instructions.

**Key Features:**
- Cross-platform support (Linux, macOS, Windows)
- Complete button mapping for all OpenBikeControl actions
- Haptic feedback support
- Real-time button state monitoring
- Comprehensive documentation

**Quick Start:**
```bash
cd python
pip install -r requirements.txt
python ble_trainer_app.py    # For BLE devices
python mdns_trainer_app.py   # For network devices
```

## Contributing Examples

We welcome example implementations in other languages and frameworks! If you've implemented OpenBikeControl support in your application, consider contributing an example to help other developers.

**Suggested languages/frameworks:**
- JavaScript/TypeScript (Node.js, Electron)
- Swift (iOS, macOS)
- Kotlin/Java (Android)
- C++ (Qt, native apps)
- C# (.NET, Unity)

**What makes a good example:**
- Clear, well-commented code
- Demonstrates both BLE and/or mDNS protocols
- Includes basic documentation
- Shows device discovery and connection
- Demonstrates button state handling
- Easy to run with minimal setup

## See Also

- [Protocol Specification](../PROTOCOL.md) - Complete technical specification
- [BLE Protocol](../BLE.md) - Bluetooth Low Energy implementation details
- [mDNS Protocol](../MDNS.md) - Network-based connectivity specification
- [Certification Program](../CERTIFICATION.md) - Device manufacturer certification

## License

All examples are released under the MIT License, same as the OpenBikeControl Protocol.
