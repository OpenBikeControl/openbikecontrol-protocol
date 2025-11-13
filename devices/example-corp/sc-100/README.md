# ExampleCorp SC-100 SwiftControl Remote Pro

![Device Status](https://img.shields.io/badge/SwiftControl-Example-blue) ![Certification](https://img.shields.io/badge/Status-Example%20Device-orange)

> **Note:** This is an example device definition for documentation purposes.

## Overview

The SC-100 SwiftControl Remote Pro is a compact wireless controller designed for cycling trainer applications. It features dual shift paddles, a 4-way joystick, action buttons, and analog triggers for precise control.

## Features

- **8 Digital Buttons** - Dual paddles, 4-way joystick, 2 action buttons
- **2 Analog Triggers** - Pressure-sensitive for ERG mode control
- **Long Battery Life** - Up to 500 hours on single CR2032 battery
- **Water Resistant** - IPX4 rated for sweat and light rain
- **Low Latency** - <20ms response time
- **Universal Compatibility** - Works with Zwift, MyWhoosh, and other SwiftControl apps

## Physical Layout

```
                    [B]
         [Left        |        Right]
         Paddle      [A]      Paddle
            |         |         |
            |    [Joystick]    |
            |    (4-way)       |
            |                  |
        [Left                Right]
        Trigger            Trigger
```

## Button Mapping

| Physical Button | Button ID | Standard Action | Type |
|----------------|-----------|-----------------|------|
| Left Paddle | 0x01 | Shift Up | Digital |
| Right Paddle | 0x02 | Shift Down | Digital |
| Joystick Up | 0x10 | Navigate Up / Steer Left | Digital |
| Joystick Down | 0x11 | Navigate Down / Steer Right | Digital |
| Joystick Left | 0x12 | Navigate Left | Digital |
| Joystick Right | 0x13 | Navigate Right | Digital |
| A Button | 0x14 | Select / Confirm | Digital |
| B Button | 0x15 | Back / Cancel | Digital |
| Left Trigger | 0x30 | ERG Down | Analog (0-255) |
| Right Trigger | 0x31 | ERG Up | Analog (0-255) |

## Setup Instructions

### Pairing with BLE

1. **Power On** - Press and hold the A button for 3 seconds
2. **Enter Pairing Mode** - LED will blink blue rapidly
3. **Open Your Trainer App** - Navigate to device settings
4. **Scan for Devices** - Look for "SwiftControl SC-100"
5. **Select and Pair** - Device will connect automatically
6. **Confirmation** - LED turns solid blue when connected

### First Time Setup

After pairing:
1. Most apps will automatically detect standard button mappings
2. You can customize button assignments in app settings
3. Test each button to ensure proper function
4. Save your configuration

## Usage

### Gear Shifting
- **Press Left Paddle** - Shift to harder gear
- **Press Right Paddle** - Shift to easier gear

### Menu Navigation
- **Move Joystick** - Navigate through menus
- **Press A Button** - Select/Confirm
- **Press B Button** - Go back/Cancel

### ERG Mode Control
- **Pull Left Trigger** - Decrease power target
- **Pull Right Trigger** - Increase power target
- **Trigger Pressure** - Controls adjustment speed

## Battery

- **Type:** CR2032 coin cell battery
- **Life:** Up to 500 hours of typical use
- **Indicator:** LED blinks red when battery is low (<10%)
- **Replacement:** 
  1. Remove back cover (twist counterclockwise)
  2. Remove old battery
  3. Insert new CR2032 (+ side up)
  4. Replace cover (twist clockwise)

## LED Indicators

| Pattern | Meaning |
|---------|---------|
| Solid Blue | Connected |
| Blinking Blue (fast) | Pairing mode |
| Blinking Blue (slow) | Searching for connection |
| Blinking Red | Low battery |
| Off | Powered off or sleep mode |

## Troubleshooting

### Device Won't Pair

1. Ensure device is powered on (LED should be blinking)
2. Check battery level - replace if low
3. Reset device: Hold A + B buttons for 10 seconds
4. Remove from app's paired devices list and re-pair
5. Ensure no other BLE devices are interfering

### Buttons Not Responding

1. Check LED - ensure device is connected
2. Verify app has SwiftControl support enabled
3. Check button mappings in app settings
4. Test buttons in app's controller test mode
5. Try re-pairing the device

### Short Battery Life

1. Ensure device enters sleep mode (LED off when idle)
2. Check for firmware updates
3. Avoid leaving in pairing mode for extended periods
4. Use high-quality CR2032 batteries

### Connection Drops

1. Keep device within 10 meters of receiver
2. Avoid obstacles between device and receiver
3. Minimize other BLE devices nearby
4. Update app and device firmware
5. Check for interference from WiFi routers

## Specifications

| Specification | Value |
|--------------|-------|
| Dimensions | 50mm × 80mm × 20mm |
| Weight | 45g (with battery) |
| Battery | CR2032 |
| Battery Life | 500 hours |
| Water Resistance | IPX4 |
| BLE Range | 15 meters |
| Latency | <20ms |
| Operating Temp | 0°C to 50°C |

## BLE Technical Details

- **Service UUID:** 0xFE50
- **Button Characteristic:** 0xFE51 (Read, Notify)
- **Device Information Service:** 0x180A (Manufacturer, Model, Serial, Firmware)
- **Battery Service:** 0x180F (Battery level 0-100%)

## Compatibility

### Tested Apps
- ✅ Zwift (iOS, Android, Windows, macOS)
- ✅ MyWhoosh (iOS, Android, Windows, macOS)
- ✅ Rouvy (iOS, Android, Windows, macOS)
- ✅ RGT Cycling (Windows, macOS)

### Platform Support
- ✅ iOS 13.0+
- ✅ Android 8.0+
- ✅ Windows 10+ (BLE adapter required)
- ✅ macOS 10.13+

## Firmware Updates

The SC-100 supports OTA (Over-The-Air) firmware updates via the companion mobile app:

1. Download "SwiftControl Config" app (iOS/Android)
2. Connect to your SC-100
3. App will notify if updates are available
4. Follow on-screen instructions
5. Device will restart with new firmware

## Support

- **Website:** https://example.com/products/sc100
- **Email:** support@example.com
- **User Manual:** https://example.com/manuals/sc100.pdf
- **Warranty:** 2 years from date of purchase

## Regulatory

- CE certified
- FCC certified
- RoHS compliant

## Package Contents

- 1× SwiftControl SC-100 Remote
- 1× CR2032 Battery (pre-installed)
- 1× Quick Start Guide
- 1× Mounting accessories
- 1× Warranty card

---

**Manufactured by ExampleCorp**  
*This is an example device for documentation purposes*
