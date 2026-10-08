# Virtual Shifting Extension

## Overview

Virtual shifting lets a rider change gears on a smart trainer that has no physical
drivetrain changes, by letting the trainer simulate a selected gear ratio. The
OpenBikeControl button protocol already carries the rider's *intent* to shift
(`0x01` Shift Up, `0x02` Shift Down, `0x03`–`0x05` direct gear selection). This
extension adds the second half: a way for the trainer app to tell the smart
trainer which gear ratio to simulate, and for the trainer to report which gear it
is actually in.

The extension is **optional** and **transport-independent**. It uses the same
message-type-prefixed binary format as the rest of the protocol and works over
both [BLE](BLE.md) and [mDNS/TCP](MDNS.md).

### Why the trainer needs the gear ratio

With virtual shifting, the trainer's flywheel speed no longer equals the bike's
speed in the app. The trainer has to derive the simulated bike speed from
cadence and the selected gear ratio, and set its resistance so that pedalling
feels like riding that gear at the simulated grade. That calculation is only
realistic when it happens inside the trainer's control loop, which is why the
gear ratio is sent to the trainer rather than being converted into a resistance
value by the app.

### Relationship to FTMS

This extension deliberately does **not** duplicate anything that the Bluetooth
SIG Fitness Machine Service (FTMS) already provides. A trainer implementing
virtual shifting is expected to keep using FTMS for:

- Grade, wind speed, rolling resistance and wind resistance coefficient
  (*Set Indoor Bike Simulation Parameters*)
- Wheel circumference (*Set Wheel Circumference*)
- Target power / ERG mode (*Set Target Power*)
- Power, cadence and speed reporting (*Indoor Bike Data*)
- Spin-down / calibration

What FTMS lacks, and what this extension adds, is:

- The **simulated gear ratio** the trainer should apply
- **Rider mass** and **bike mass**, needed for a realistic acceleration feel
- Feedback on the **gear actually in use**, including front/rear indices for
  trainers that model a multi-chainring drivetrain themselves
- The app's **simulated speed**, so the trainer can align its inertia and
  gravity simulation with what the rider sees on screen

---

## Roles

| Role        | Sends                              | Receives                           |
|-------------|------------------------------------|------------------------------------|
| Trainer app | Virtual Shifting Control (`0x05`), Ride State (`0x07`) | Virtual Shifting State (`0x06`)    |
| Trainer     | Virtual Shifting State (`0x06`)    | Virtual Shifting Control (`0x05`), Ride State (`0x07`) |

"Trainer app" means whichever application is driving the trainer. This can be
the training software itself, or a bridge app that sits between a controller and
the training software.

A trainer can also be a controller. A smart bike with built-in shifters sends
Button State messages (`0x01`) as a controller *and* exchanges virtual shifting
messages as a trainer, over the same service.

### Who owns the gear table

There are two valid models, and a trainer reports which one it is using in the
State message:

1. **App-owned gearing (default).** The app keeps the list of gears (for example
   a 2×12 drivetrain, or a linear 24-step table), turns Shift Up / Shift Down
   button presses into a gear ratio, and sends that ratio to the trainer. The
   trainer only needs to simulate one number. This keeps gearing consistent
   across apps and keeps trainer firmware simple.

2. **Trainer-owned gearing.** The trainer keeps its own gear table and its own
   shifters (typical for smart bikes). It applies gear changes locally and reports
   the current gear and ratio to the app for display. The app does not send gear
   ratios in this mode; it still sends grade and other simulation parameters via
   FTMS.

Apps MUST support model 1. Trainers MAY implement either or both.

---

## Byte order

All multi-byte fields in this extension are **little-endian**, matching FTMS, so
that trainer firmware can share the same helpers for both services.

---

## Virtual Shifting Control (App to Trainer)

**Message Type:** `0x05`

Sent by the app whenever the simulated gear changes, when rider or bike mass
changes, and when virtual shifting is enabled or disabled.

**Data Format:**

```
[Message_Type] [Version] [Mode] [Gear_Ratio_L] [Gear_Ratio_H] [Rider_Mass_L] [Rider_Mass_H] [Bike_Mass_L] [Bike_Mass_H] [Gear_Index] [Gear_Count]
```

Total length: 11 bytes.

- **Message_Type** (1 byte): Always `0x05`
- **Version** (1 byte): Format version, currently `0x01`
- **Mode** (1 byte):
  - `0x00` = Virtual shifting off. The trainer behaves as a plain FTMS trainer
    and ignores the remaining fields.
  - `0x01` = Virtual shifting on, app-owned gearing. The trainer simulates
    `Gear_Ratio`.
  - `0x02-0xFF` = Reserved; trainers MUST treat these as `0x00`
- **Gear_Ratio** (2 bytes, uint16, little-endian): Simulated gear ratio
  (chainring teeth ÷ cassette teeth) multiplied by 1000.
  - `0` = Unchanged / not specified
  - Example: 50/14 = 3.571 → `3571` = `[0xF3, 0x0D]`
  - Example: 34/32 = 1.063 → `1063` = `[0x27, 0x04]`
- **Rider_Mass** (2 bytes, uint16, little-endian): Rider mass in 0.1 kg.
  - `0` = Unknown / keep the trainer's current value
  - Example: 75.0 kg → `750` = `[0xEE, 0x02]`
- **Bike_Mass** (2 bytes, uint16, little-endian): Bike mass in 0.1 kg.
  - `0` = Unknown / keep the trainer's current value
  - Example: 8.5 kg → `85` = `[0x55, 0x00]`
- **Gear_Index** (1 byte): 1-based position of the current gear in the app's
  gear table, for trainers that have a display. `0` = Not specified.
- **Gear_Count** (1 byte): Number of gears in the app's gear table. `0` = Not
  specified.

**Example Messages:**

```
// Enable virtual shifting, ratio 2.667 (40/15), rider 75.0 kg, bike 8.5 kg, gear 12 of 24
[0x05, 0x01, 0x01, 0x6B, 0x0A, 0xEE, 0x02, 0x55, 0x00, 0x0C, 0x18]

// Shift to ratio 3.000 (45/15), masses unchanged, gear 14 of 24
[0x05, 0x01, 0x01, 0xB8, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x0E, 0x18]

// Disable virtual shifting
[0x05, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
```

**App Behaviour:**

- Apps MUST send this message on every gear change. Do not rate-limit shifts; a
  rider may shift several times per second.
- Apps SHOULD send the current state once after connecting, before the first
  shift, so the trainer starts from a known gear.
- Apps SHOULD send an update when rider or bike mass changes.
- Apps MAY resend the current state periodically (for example every 10 s) as a
  safeguard against a missed message. Trainers MUST treat an unchanged message
  as a no-op.
- While the app has an FTMS target power active (ERG mode), it SHOULD send
  `Mode = 0x00` or stop sending Control messages; the trainer ignores the gear
  ratio in ERG mode anyway (see below).

**Trainer Behaviour:**

- The trainer MUST keep the last received values until a new Control message
  arrives or the connection is closed.
- On disconnect the trainer MUST revert to `Mode = 0x00`.
- If a requested ratio is outside the range the trainer can simulate, the
  trainer MUST clamp it to the nearest supported ratio and report the applied
  ratio with the *Clamped* flag in the State message.
- While an FTMS target power is active, the trainer SHOULD ignore the gear
  ratio and set the *ERG override* flag in the State message.
- A trainer using trainer-owned gearing MAY ignore `Gear_Ratio`, `Gear_Index`
  and `Gear_Count`, but SHOULD still honour `Mode` and the mass fields.
- Trainers MUST NOT reply to a Control message directly. All feedback goes
  through the State message, which is sent on change regardless of what caused
  the change.

---

## Virtual Shifting State (Trainer to App)

**Message Type:** `0x06`

Sent by the trainer whenever its virtual shifting state changes, and once after
a connection is established so the app can detect support.

**Data Format:**

```
[Message_Type] [Version] [Flags] [Gear_Ratio_L] [Gear_Ratio_H] [Gear_Index] [Gear_Count] [Front_Index] [Front_Count] [Rear_Index] [Rear_Count]
```

Total length: 11 bytes.

- **Message_Type** (1 byte): Always `0x06`
- **Version** (1 byte): Format version, currently `0x01`
- **Flags** (1 byte): Bit field
  - Bit 0 (`0x01`) = *Active*: virtual shifting is currently being simulated
  - Bit 1 (`0x02`) = *Clamped*: the last requested ratio was outside the
    supported range and the nearest supported ratio is in use
  - Bit 2 (`0x04`) = *Trainer-owned gearing*: the trainer keeps its own gear
    table; the app should display the reported gear and not send ratios
  - Bit 3 (`0x08`) = *ERG override*: a target power is active and the gear
    ratio is ignored until it is cleared
  - Bit 4 (`0x10`) = *Uses app speed*: the trainer is currently using the
    speed from Ride State messages as its inertia and gravity reference
  - Bits 5–7 = Reserved, MUST be `0`
- **Gear_Ratio** (2 bytes, uint16, little-endian): Ratio currently simulated,
  multiplied by 1000. `0` = Not simulating / unknown.
- **Gear_Index** (1 byte): 1-based current gear in a flat gear table.
  `0` = Not applicable.
- **Gear_Count** (1 byte): Number of gears in the flat table. `0` = Not applicable.
- **Front_Index** (1 byte): 1-based current chainring (trainer-owned gearing).
  `0` = Not applicable.
- **Front_Count** (1 byte): Number of chainrings. `0` = Not applicable.
- **Rear_Index** (1 byte): 1-based current cassette sprocket (trainer-owned
  gearing). `0` = Not applicable.
- **Rear_Count** (1 byte): Number of cassette sprockets. `0` = Not applicable.

With app-owned gearing the trainer echoes `Gear_Index` and `Gear_Count` from the
last Control message. With trainer-owned gearing the trainer fills in the
front/rear fields and SHOULD also provide a flattened `Gear_Index`/`Gear_Count`
for apps that only display a single gear number.

**Example Messages:**

```
// Capability announcement after connect: supported, not active yet
[0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

// Active, app-owned, ratio 3.000, gear 14 of 24
[0x06, 0x01, 0x01, 0xB8, 0x0B, 0x0E, 0x18, 0x00, 0x00, 0x00, 0x00]

// Active, requested ratio was clamped to 5.500
[0x06, 0x01, 0x03, 0x7C, 0x15, 0x18, 0x18, 0x00, 0x00, 0x00, 0x00]

// Smart bike with its own 2x12 drivetrain: big ring, 5th sprocket, ratio 3.333, flat gear 17 of 24
[0x06, 0x01, 0x05, 0x05, 0x0D, 0x11, 0x18, 0x02, 0x02, 0x05, 0x0C]

// ERG mode active, gear ratio currently ignored
[0x06, 0x01, 0x09, 0xB8, 0x0B, 0x0E, 0x18, 0x00, 0x00, 0x00, 0x00]
```

**Trainer Behaviour:**

- Trainers MUST send a State message once after the connection is established
  (BLE: when the app subscribes; TCP: right after the socket is accepted). This
  is how apps discover that the trainer supports virtual shifting.
- Trainers MUST send a State message whenever any field changes.
- Trainers MAY additionally send the State message periodically (at most once
  per second) as a keep-alive for apps.

**App Behaviour:**

- Apps SHOULD use the State message as the source of truth for what to display
  to the rider.
- If the *Trainer-owned gearing* flag is set, apps SHOULD stop sending gear
  ratios and display the reported front/rear or flat gear instead.
- If the *Clamped* flag is set, apps MAY inform the rider that the top or
  bottom of the trainer's range has been reached, for example with a haptic
  pattern on the controller.

---

## Ride State (App to Trainer)

**Message Type:** `0x07`

Optional. Sent periodically by the app so the trainer can align its inertia and
gravity simulation with the speed the rider sees on screen. The app's speed
includes effects the trainer cannot know about, such as drafting, coasting on a
descent, braking, or the app's own mass and drag model. Without it the trainer
has to derive a speed from cadence and gear ratio alone, which can drift away
from the on-screen speed in exactly the moments where feel matters most.

**Data Format:**

```
[Message_Type] [Version] [Speed_L] [Speed_H] [Reserved]
```

Total length: 5 bytes.

- **Message_Type** (1 byte): Always `0x07`
- **Version** (1 byte): Format version, currently `0x01`
- **Speed** (2 bytes, uint16, little-endian): Simulated bike speed in 0.01 km/h,
  the same unit FTMS uses for Indoor Bike Data.
  - `0` = Stationary
  - Example: 32.50 km/h → `3250` = `[0xB2, 0x0C]`
- **Reserved** (1 byte): MUST be `0`

**Example Messages:**

```
// 32.50 km/h
[0x07, 0x01, 0xB2, 0x0C, 0x00]

// 0 km/h (rider stopped)
[0x07, 0x01, 0x00, 0x00, 0x00]
```

**App Behaviour:**

- Apps SHOULD send Ride State at 1–4 Hz while virtual shifting is on. Higher
  rates add BLE traffic without improving the simulation.
- Apps that do not model speed themselves MAY omit this message entirely.
- Apps SHOULD stop sending Ride State when they send `Mode = 0x00` in the
  Control message.

**Trainer Behaviour:**

- The speed is a *reference* for inertia and gravity simulation, not a target
  the trainer should chase. Trainers MUST NOT adjust resistance to force the
  flywheel towards this speed; doing so would oscillate whenever the stream lags.
- Trainers MAY ignore Ride State entirely and derive speed from cadence and
  gear ratio. Trainers that use it MUST set the *Uses app speed* flag in the
  State message while doing so.
- If no Ride State message arrives for 2 seconds, the trainer SHOULD fall back
  to cadence-derived speed and clear the *Uses app speed* flag.
- Trainers MUST NOT reply to a Ride State message.

---

## Transport Mapping

### BLE

Two additional characteristics on the OpenBikeControl service
`d273f680-d548-419d-b9d1-fa0472345229`:

| Characteristic           | UUID                                   | Properties                   | Message type |
|--------------------------|----------------------------------------|------------------------------|--------------|
| Virtual Shifting Control | `d273f684-d548-419d-b9d1-fa0472345229` | Write, Write Without Response | `0x05`       |
| Virtual Shifting State   | `d273f685-d548-419d-b9d1-fa0472345229` | Read, Notify                 | `0x06`       |
| Ride State               | `d273f686-d548-419d-b9d1-fa0472345229` | Write Without Response       | `0x07`       |

Apps detect support by discovering the State characteristic. See
[BLE.md](BLE.md#4-virtual-shifting-control-characteristic-write) for details.

### mDNS / TCP

Message types `0x05`, `0x06` and `0x07` are exchanged on the same TCP connection as
all other messages. All are fixed-length (11, 11 and 5 bytes). See
[MDNS.md](MDNS.md#virtual-shifting-control-app-to-trainer) for details.

---

## Interaction with Button Messages

A controller's Shift Up / Shift Down buttons continue to be delivered to the app
as Button State messages (`0x01`). The app decides what a press means (next gear
in its table, step size, limits) and sends the resulting ratio to the trainer.
This keeps the controller independent of the trainer and lets the same controller
drive any trainer that implements this extension.

A smart bike that both has shifters and simulates gears itself SHOULD still send
the Button State messages, so apps can use them for other purposes (for example
menu navigation while not riding), and SHOULD set the *Trainer-owned gearing*
flag in its State messages so the app does not also apply its own gear table.

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [BLE Protocol Specification](BLE.md)
- [mDNS Protocol Specification](MDNS.md)
- [Button Mapping](PROTOCOL.md#button-mapping)
