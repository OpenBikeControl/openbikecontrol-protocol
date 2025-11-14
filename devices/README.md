# OpenBikeControl Certified Devices

This directory contains device definitions for OpenBikeControl certified controllers. Each device includes button mappings, specifications, and documentation to enable seamless integration with trainer apps.

## Directory Structure

```
devices/
├── <manufacturer>/
│   └── <model>/
│       ├── device.json          # Device definition and button mapping
│       ├── README.md             # User documentation and setup guide
│       ├── product.jpg           # Product image (optional)
│       └── button_layout.png     # Button layout diagram (optional)
```

## Device Definition Format

Each certified device must include a `device.json` file with the following structure:

```json
{
  "manufacturer": "Manufacturer Name",
  "model": "Model Number",
  "name": "Full Product Name",
  "version": "1.0",
  "certification_date": "YYYY-MM-DD",
  "status": "certified|pending|example",
  "button_mapping": [
    {
      "physical_button": "Button Label",
      "button_id": 1,
      "standard_action": "Shift Up",
      "type": "digital|analog",
      "description": "What this button does"
    }
  ],
  "specs": { /* Technical specifications */ },
  "ble_services": { /* BLE service details */ },
  "connectivity": { /* Connection capabilities */ },
  "support": { /* Support and contact info */ }
}
```

See [example-corp/sc-100/device.json](example-corp/sc-100/device.json) for a complete example.

## Certification Status

- **certified** - Fully certified and tested device
- **pending** - Certification in progress
- **example** - Example device for documentation

## Using Device Definitions

### For App Developers

Import device definitions to provide pre-configured button mappings:

```javascript
// Load device definition
const deviceDef = require('./devices/example-corp/sc-100/device.json');

// Map button IDs to app actions
deviceDef.button_mapping.forEach(btn => {
  registerButton(btn.button_id, btn.standard_action);
});
```

### For Device Manufacturers

To add your device to this directory:

1. Review the [Certification Process](../CERTIFICATION.md)
2. Create your device definition files
3. Submit a Pull Request
4. Work with the team through certification
5. Device added to certified list upon approval

## Certified Devices

### Currently Certified

*No devices currently certified - this is a new protocol!*

Be the first to certify your device and support the OpenBikeControl ecosystem.

### Example Devices

- [ExampleCorp SC-100](example-corp/sc-100/) - Reference implementation

## Button ID Reference

Quick reference for standard button IDs:

| Range | Category |
|-------|----------|
| 0x01-0x0F | Gear Shifting |
| 0x10-0x1F | Navigation |
| 0x20-0x2F | Social/Emotes |
| 0x30-0x3F | Training Controls |
| 0x40-0x4F | View Controls |
| 0x50-0x5F | Power-ups |
| 0x60-0x7F | Reserved |
| 0x80-0x9F | App-specific |
| 0xA0-0xFF | Manufacturer-specific |

See [PROTOCOL.md](../PROTOCOL.md#button-mapping) for complete button mapping details.

## Contributing

Help improve the certified devices directory:

- Submit your device for certification
- Report issues with device definitions
- Improve documentation and examples
- Test devices with different apps

## Questions?

- Open a [GitHub Issue](https://github.com/jonasbark/openbikecontrol-protocol/issues)
- Review [Certification Documentation](../CERTIFICATION.md)
- Contact: certification@swiftcontrol.app
