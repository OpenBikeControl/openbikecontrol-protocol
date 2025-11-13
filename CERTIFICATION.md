# SwiftControl Device Certification

## Overview

The SwiftControl Certification Program ensures that BLE controllers meet quality standards and work seamlessly with participating cycling trainer applications. Certification is voluntary but highly recommended for manufacturers who want their devices officially recognized and supported.

## Benefits of Certification

### For Manufacturers

- **Official Device Listing** - Your device listed in the SwiftControl certified devices directory
- **Compatibility Badge** - Use the "SwiftControl Certified" badge in marketing materials
- **Button Mapping Repository** - Device-specific button mappings included in the official repository
- **Technical Support** - Access to implementation guides and technical assistance
- **App Integration** - Participating apps include your device's button mappings by default
- **Community Trust** - Certification signals quality and standards compliance to users
- **Marketing Visibility** - Featured on the SwiftControl website and partner communications

### For App Developers

- **Pre-configured Mappings** - Access to certified device button definitions
- **Quality Assurance** - Confidence that devices meet minimum standards
- **Reduced Support Burden** - Fewer compatibility issues with certified devices
- **Easy Integration** - Reference implementations and tested configurations

### For Users

- **Guaranteed Compatibility** - Certified devices work with all participating apps
- **Quality Standards** - Devices meet minimum performance and reliability criteria
- **Easy Setup** - Pre-configured button mappings work out of the box
- **Ongoing Support** - Certified manufacturers commit to firmware updates and support

## Certification Requirements

### Technical Requirements

Devices must meet the following technical standards:

#### 1. Protocol Compliance

- ✅ Implement SwiftControl BLE service UUID (`0xFE50`)
- ✅ Implement Button State characteristic (`0xFE51`) with correct data format
- ✅ Implement standard BLE Device Information Service (`0x180A`)
- ✅ Implement Battery Service (`0x180F`) for battery-powered devices
- ✅ Do NOT use manufacturer-specific advertisement data (Apple compatibility requirement)
- ✅ Send notifications only on button state changes (not continuous polling)

#### 2. Performance Standards

- ✅ Button response latency < 50ms (press to notification)
- ✅ BLE connection range ≥ 10 meters in open space
- ✅ Battery life ≥ 40 hours typical use (if battery-powered)
- ✅ Reliable debouncing (no spurious button presses)
- ✅ Support connection intervals down to 7.5ms

#### 3. Quality Standards

- ✅ Hardware: Durable construction suitable for cycling environment
- ✅ Buttons: Minimum 100,000 press lifecycle
- ✅ Water resistance: IPX4 minimum (splash resistant)
- ✅ Firmware: Support OTA updates (recommended) or documented update procedure
- ✅ Documentation: User manual and setup guide in English

#### 4. Compatibility Testing

Devices must be tested with at least two of the following apps:
- Zwift
- MyWhoosh
- Rouvy
- RGT Cycling
- TrainerRoad (if applicable)
- Other participating SwiftControl apps

### Documentation Requirements

Manufacturers must provide:

1. **Device Specification Sheet**
   - Hardware specifications
   - Button layout and physical description
   - Battery specifications (if applicable)
   - Dimensions and weight
   - Operating temperature range

2. **Button Mapping Definition**
   - Complete mapping of physical buttons to SwiftControl button IDs
   - Description of analog inputs (if applicable)
   - Default button assignments

3. **User Documentation**
   - Setup instructions
   - Pairing guide
   - Battery replacement procedure (if applicable)
   - Troubleshooting guide
   - Warranty information

4. **Developer Documentation**
   - BLE characteristics documentation
   - Sample connection code (optional but recommended)
   - Known limitations or quirks

## Certification Process

### Step 1: Pre-Certification

1. **Review Protocol Specification**
   - Read [PROTOCOL.md](PROTOCOL.md) thoroughly
   - Ensure your device design complies with all requirements

2. **Self-Testing**
   - Test with BLE debugging tools (nRF Connect, LightBlue)
   - Verify all required characteristics are discoverable
   - Test button state notifications
   - Measure response latency

3. **Prepare Documentation**
   - Complete device specification sheet
   - Create button mapping definition file
   - Prepare user and developer documentation

### Step 2: Application Submission

Submit a certification request by creating a GitHub Pull Request:

1. **Fork the Repository**
   ```bash
   git clone https://github.com/jonasbark/swiftcontrol-protocol.git
   cd swiftcontrol-protocol
   git checkout -b certification/your-device-name
   ```

2. **Add Device Definition**

   Create a new file in `devices/<manufacturer>/<model>.json`:

   ```json
   {
     "manufacturer": "ExampleCorp",
     "model": "SC-100",
     "name": "SwiftControl Remote Pro",
     "version": "1.0",
     "certification_date": "2024-01-15",
     "device_info": {
       "firmware_version": "1.2.3",
       "hardware_version": "1.0",
       "serial_prefix": "SC1"
     },
     "specs": {
       "buttons": 8,
       "analog_inputs": 2,
       "battery_type": "CR2032",
       "battery_life_hours": 500,
       "water_resistance": "IPX4",
       "weight_grams": 45,
       "dimensions_mm": {
         "width": 50,
         "height": 80,
         "depth": 20
       }
     },
     "button_mapping": [
       {
         "physical_button": "Left Paddle",
         "button_id": 1,
         "standard_action": "Shift Up",
         "type": "digital"
       },
       {
         "physical_button": "Right Paddle",
         "button_id": 2,
         "standard_action": "Shift Down",
         "type": "digital"
       },
       {
         "physical_button": "Joystick Up",
         "button_id": 16,
         "standard_action": "Navigate Up",
         "type": "digital"
       },
       {
         "physical_button": "Joystick Down",
         "button_id": 17,
         "standard_action": "Navigate Down",
         "type": "digital"
       },
       {
         "physical_button": "A Button",
         "button_id": 20,
         "standard_action": "Select",
         "type": "digital"
       },
       {
         "physical_button": "B Button",
         "button_id": 21,
         "standard_action": "Back",
         "type": "digital"
       },
       {
         "physical_button": "Left Trigger",
         "button_id": 48,
         "standard_action": "ERG Down",
         "type": "analog",
         "range": "0-255"
       },
       {
         "physical_button": "Right Trigger",
         "button_id": 49,
         "standard_action": "ERG Up",
         "type": "analog",
         "range": "0-255"
       }
     ],
     "ble_services": {
       "primary_service": "0xFE50",
       "button_characteristic": "0xFE51",
       "device_information": true,
       "battery_service": true
     },
     "connectivity": {
       "ble": true,
       "mdns": false,
       "connection_range_meters": 15
     },
     "support": {
       "website": "https://example.com/sc100",
       "firmware_updates": "OTA via mobile app",
       "warranty_years": 2,
       "support_email": "support@example.com"
     },
     "certifications": {
       "ce": true,
       "fcc": true,
       "rohs": true
     }
   }
   ```

3. **Add Documentation**

   Create `devices/<manufacturer>/<model>/README.md` with:
   - Setup instructions
   - Pairing guide
   - Button layout diagram (image)
   - Troubleshooting guide

4. **Add Marketing Assets** (Optional)

   Include in `devices/<manufacturer>/<model>/`:
   - Product image (product.jpg)
   - Button layout diagram (button_layout.png)
   - Logo (logo.png)

5. **Submit Pull Request**
   ```bash
   git add devices/
   git commit -m "Add certification for ExampleCorp SC-100"
   git push origin certification/your-device-name
   ```

   Create a PR with the title: "Certification: [Manufacturer] [Model]"

### Step 3: Review Process

The SwiftControl team will review your submission:

1. **Documentation Review** (1-2 business days)
   - Verify all required documentation is complete
   - Check button mapping definitions
   - Review technical specifications

2. **Technical Testing** (3-5 business days)
   - Connect to device via BLE
   - Verify service and characteristic UUIDs
   - Test button state notifications
   - Measure response latency
   - Test with 2+ compatible apps

3. **Compatibility Testing** (3-5 business days)
   - Test pairing with iOS and Android devices
   - Verify button mappings work as documented
   - Test battery reporting
   - Verify range and stability

4. **Feedback and Iteration**
   - Issues or suggestions communicated via PR comments
   - Manufacturer addresses feedback
   - Re-review if necessary

### Step 4: Certification Approval

Once approved:

1. **Certification Badge**
   - Receive official "SwiftControl Certified" badge
   - Usage guidelines provided
   - Badge valid for device hardware version

2. **Device Listing**
   - Device added to official certified devices list
   - Published on SwiftControl website
   - Included in app developer documentation

3. **Repository Merge**
   - Your device definition merged to main branch
   - Available for app developers to integrate
   - Versioned and maintained

## Certification Maintenance

### Firmware Updates

- Minor firmware updates: No re-certification required
- Major protocol changes: May require re-certification
- Notify SwiftControl team of significant updates

### Recertification

Recertification required for:
- New hardware versions
- Major firmware changes affecting protocol compliance
- Changes to button mappings
- Additional features (e.g., adding analog inputs)

Recertification follows expedited process for previously certified manufacturers.

## Certification Costs

The SwiftControl Certification Program is currently **free** for all manufacturers. The program is maintained by the community and sponsored contributors.

### Future Considerations

As the program scales, nominal fees may be introduced to cover:
- Testing equipment and infrastructure
- Technical review team compensation
- Website hosting and maintenance

Any future fees will be:
- Announced with 6+ months notice
- Kept minimal to encourage broad adoption
- Waived for open-source hardware projects

## Certification Withdrawal

Certification may be withdrawn if:
- Device fails to meet standards after market release
- Manufacturer makes undocumented protocol changes
- Safety or quality issues are reported
- Manufacturer requests withdrawal

Withdrawal process:
1. Written notice provided to manufacturer
2. 30-day period to address issues
3. If unresolved, device removed from certified list
4. Public notice published

## Getting Started

Ready to certify your device?

1. ✅ Review the [Protocol Specification](PROTOCOL.md)
2. ✅ Build and test your device implementation
3. ✅ Prepare your documentation
4. ✅ Submit your certification PR
5. ✅ Work with the team through the review process

### Questions?

- Open a [GitHub Issue](https://github.com/jonasbark/swiftcontrol-protocol/issues) with the `certification` label
- Email: certification@swiftcontrol.org (if available)
- Community Discord: [Join here](https://discord.gg/swiftcontrol) (if available)

## Example Certified Devices

Once devices are certified, they will be listed here with:
- Manufacturer and model
- Certification date
- Key features
- Where to buy
- Support links

---

## Certification Badge Usage

### Certified Badge

![SwiftControl Certified](https://img.shields.io/badge/SwiftControl-Certified-brightgreen)

Manufacturers may use the certification badge on:
- Product packaging
- Marketing materials
- Website and documentation
- Retail listings

### Badge Requirements

- Only use current/valid certification badge
- Do not modify badge design
- Include badge version number (hardware version)
- Link badge to SwiftControl website when used digitally

### Badge Restrictions

Do not use badge if:
- Certification has expired or been withdrawn
- Device hardware has changed without recertification
- Using on non-certified products

---

## Contributing to Certification

The certification program improves through community input:

- **Suggest Requirements** - Propose new technical or quality standards
- **Testing Tools** - Contribute testing scripts and utilities
- **App Integration** - Help integrate certified devices into trainer apps
- **Documentation** - Improve certification guides and templates
- **Translation** - Translate certification docs to other languages

All contributions welcome via GitHub Issues and Pull Requests.

---

## License

The SwiftControl Certification Program documentation is released under the [MIT License](LICENSE).
