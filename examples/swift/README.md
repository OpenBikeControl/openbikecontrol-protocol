# OpenBikeControl Swift Example

A Swift Package showing how an Apple-platform trainer app (iOS, macOS, tvOS, watchOS) receives OpenBikeControl input over Bluetooth Low Energy. It was extracted from [TrainerKit](https://trainerkitapp.com), where the codec runs unchanged on iPhone, Mac and Apple TV.

## What's here

| Target | What it is |
|---|---|
| `OpenBikeControl` (library) | The codec: UUIDs, standard button IDs, Button State parsing, gear decoding, App Information and Haptic Feedback encoding/decoding. Foundation only, so it drops into any app. |
| `obc-trainer-app` (executable, macOS) | A command-line trainer app: scans for the service, connects, declares itself, subscribes to Button State, prints every button and the reported gear, sends haptic feedback. |
| `obc-mock-device` (executable, macOS) | A fake device: advertises the service, reports a 2×12 drivetrain's gear, sends button presses from the keyboard, decodes what the app writes. |
| `OpenBikeControlTests` | The codec against the spec's examples and against vectors from the Python reference implementation in `../python/protocol_parser.py`, in both directions. |

## Requirements

- Swift 5.9 or later (Xcode 15+). The library builds on any platform Foundation supports.
- The two executables use CoreBluetooth and run on macOS 13+. The first run asks to allow Bluetooth for your terminal.

## Quick start

```bash
cd examples/swift
swift test                      # codec tests, no hardware needed

# Without a device: fake one in a second terminal
swift run obc-mock-device
swift run obc-trainer-app

# With a device
swift run obc-trainer-app            # connects to the first OpenBikeControl device found
swift run obc-trainer-app "SB200"    # or only to one whose name contains this
```

In the mock, `u`/`d` change the rear cog, `f` toggles the chainring, and `l p r s b + -` press Lap, Pause, Resume, Skip Interval, Previous Interval and Increase/Decrease Difficulty. The app prints each notification decoded and the current gear, and sends a short haptic pulse back when Lap is pressed; `h`, `s` and `e` send haptics from the keyboard.

## Using the codec in your app

```swift
import OpenBikeControl

// Discovery and connection: CoreBluetooth, filtered on the service UUID.
let service = CBUUID(string: OpenBikeControl.serviceUUIDString)

// Right after connecting, tell the device who you are and which actions you handle.
let info = OpenBikeControl.AppInformation(appID: "my-app", appVersion: "1.0.0",
                                          buttons: [.gearSet, .chainringSet, .cassetteSet,
                                                    .pause, .resume, .lap, .increaseDifficulty, .decreaseDifficulty])
peripheral.writeValue(info.encoded, for: appInformationCharacteristic, type: .withResponse)

// Every Button State notification is a list of ID/value pairs.
var gear = OpenBikeControl.Gear()
if let events = OpenBikeControl.parseButtonState(data) {
    for e in events where e.isPress {
        switch e.button {
        case .lap:   markLap()
        case .pause: pauseWorkout()
        default:     break
        }
    }
    if gear.apply(events) { show(gear.displayText) }   // "2·7", "11", or a flat index
}

// Tactile confirmation.
peripheral.writeValue(OpenBikeControl.hapticFeedback(pattern: .short), for: hapticCharacteristic, type: .withoutResponse)
```

## Notes from a real integration

**A smart bike exposes this beside its trainer services.** The Stages SB200 advertises OpenBikeControl on the same peripheral as FTMS. A trainer app does not scan for it separately or open a second connection: after connecting to the trainer, discover the OpenBikeControl service on that peripheral and subscribe only when it is present. Trainer control is unchanged.

**Declare what you handle.** The button list in App Information tells the device which actions your app understands, so it can pick sensible button mappings. It is not a claim of control. An app that leaves gearing to the bike and displays the gear the bike reports declares the gear-set IDs (0x03–0x05) and the ride controls it performs, and not Shift Up / Shift Down (0x01/0x02). An app that implements virtual shifting itself declares those too.

**Gear values are positions, not percentages.** Gear Set, Chainring Set and Cassette Set carry a 1-based position offset by one: 0x02 is gear 1. 0x00 means released or no change and 0x01 is a reserved no-op, so `gearPosition(from:)` returns nil for both. A front/rear bike usually sends chainring, cassette and a flattened index in one notification; `Gear` keeps all three and `displayText` prefers front·rear.

**Read, then subscribe.** Button State is readable, and a bike's current gear is in that first read. Subscribing alone would leave the display empty until the first shift.

**Reset on disconnect.** Everything learned from the device, the gear included, is forgotten when the connection drops, so a stale gear is never shown against a new session.

**Robust parsing.** An empty `[0x01]` message is legal and yields nothing. A trailing byte with no value is ignored and the complete pairs before it are kept, as the Python reference parser does. Messages whose first byte is not 0x01 return nil. Analog IDs (gear, brake, steering angle, cruise control, emote, camera view) never count as a press; `Event.description` spells out what their value means.

**Permissions.** On iOS/tvOS add `NSBluetoothAlwaysUsageDescription` to Info.plist. On macOS the sandbox needs the Bluetooth entitlement; a command-line tool prompts on first use.

## Tests

```bash
swift test
```

The reference vectors were produced from `../python/protocol_parser.py` (commit 20c063d): its encoder built each device → app message and its parser's reading of every pair (gear number, pressed/released, display text) is asserted here; the App Information and Haptic bytes this codec produces are compared byte for byte with what its encoder produces and are accepted by its parser.

## License

MIT, like the protocol.
