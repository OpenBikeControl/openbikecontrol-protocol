# Trainer Profile

> **Status: Draft.** This document is a proposal and may change before it is final.

## Overview

The core OpenBikeControl protocol describes input devices (controllers) talking
to apps. The [Virtual Shifting Extension](VIRTUAL_SHIFTING.md) adds the first
app-to-trainer messages. This document completes that direction: it defines an
**OpenBikeControl Trainer Service** through which an app can control a smart
trainer or smart bike and receive its data over BLE and over the network, with a
single, explicit rule for who is allowed to control the trainer.

The Trainer Profile is **optional**. Controllers do not implement it. Trainers
and smart bikes implement it next to, not instead of, the Bluetooth SIG Fitness
Machine Service (FTMS).

### Why a trainer profile

Apps can already control a trainer over BLE with FTMS, and the Virtual Shifting
Extension fills FTMS's biggest gap. Three things remain that neither covers:

1. **Network control.** FTMS only exists over BLE. Trainers that connect over
   Wi-Fi today use vendor-specific tunnels. The Trainer Profile uses the same
   messages over BLE and TCP, so a trainer on the network is controlled exactly
   like one over BLE.
2. **Control ownership across protocols.** FTMS has a control slot, but it only
   knows about FTMS clients. A trainer that also accepts OpenBikeControl writes
   needs one rule covering both, otherwise two apps can fight over the trainer.
3. **One place for capability discovery.** Apps need to know up front whether a
   trainer supports simulation, target power, virtual shifting, app-provided
   speed, and so on. The Trainer Status message carries this for all
   OpenBikeControl trainer features.

### Design rules

The Trainer Profile follows the rest of the protocol:

- Fixed-length messages with a message type prefix, identical over BLE and TCP
- Writes are one-way; the trainer never answers a write directly
- The trainer reports its **state** whenever it changes, and once after connect
- Multi-byte fields are little-endian, matching FTMS
- Everything is optional except Trainer Status, which announces what else is there

### Relationship to FTMS

A trainer that implements the Trainer Profile SHOULD still implement FTMS, so
apps that have not adopted OpenBikeControl keep working over BLE. The two share
one control slot (see [Control Ownership](#control-ownership)). FTMS data
characteristics stay readable by every client regardless of who owns control.

Apps on BLE MAY use either FTMS or the Trainer Profile for simulation and target
power. They MUST NOT use both on the same connection at the same time.

---

## Message Summary

| Type   | Name                     | Direction        | Length | Defined in                |
|--------|--------------------------|------------------|--------|---------------------------|
| `0x05` | Virtual Shifting Control | app → trainer    | 11     | [VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md) |
| `0x06` | Virtual Shifting State   | trainer → app    | 11     | [VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md) |
| `0x07` | Ride State               | app → trainer    | 5      | [VIRTUAL_SHIFTING.md](VIRTUAL_SHIFTING.md) |
| `0x08` | Trainer Control          | app → trainer    | 17     | this document             |
| `0x09` | Trainer Data             | trainer → app    | 13     | this document             |
| `0x0A` | Trainer Status           | trainer → app    | 15     | this document             |
| `0x0B` | Calibration Control      | app → trainer    | —      | reserved                  |
| `0x0C` | Calibration State        | trainer → app    | —      | reserved                  |

Message types `0x05`–`0x07` are defined by the Virtual Shifting Extension and
are part of the Trainer Service. A trainer MAY implement only those three plus
Trainer Status; the Virtual Shifting Extension does not require the rest of this
profile.

---

## Control Ownership

Exactly one client controls a trainer at a time. This covers Trainer Control,
Virtual Shifting Control and Ride State together, and it covers FTMS too.

**Acquiring control:**

- The first client that writes Trainer Control or Virtual Shifting Control with
  a non-idle `Mode` becomes the **owner**. There is no separate request message.
- While an owner exists, control writes from any other client MUST be ignored.
  The trainer MUST NOT change its behaviour because of them.
- Ride State messages from a non-owner MUST be ignored.

**Releasing control:**

- The owner writes Trainer Control with `Mode = 0x00` (idle) **and** Virtual
  Shifting Control with `Mode = 0x00`, or simply disconnects.
- The trainer MUST release ownership if no message at all has been received from
  the owner for 30 seconds. Owners SHOULD send at least one message every
  10 seconds; an app that streams Ride State satisfies this automatically.

**Reporting:**

- Trainer Status carries a `Control` field telling each client whether it is the
  owner, whether another OpenBikeControl client is, or whether an FTMS client is.
  The trainer sends it to every connected client whenever ownership changes.
- Apps MUST show the rider when they are not the owner. "Connected, but another
  app is controlling the trainer" is the message that prevents the most support
  tickets.

**Interaction with FTMS:**

- While an OpenBikeControl owner exists, the trainer MUST reject FTMS *Request
  Control* with *Control Not Permitted* and ignore FTMS control point writes.
- While an FTMS client holds control, the trainer MUST ignore OpenBikeControl
  control writes and report `Control = 0x03` in Trainer Status.
- FTMS data (Indoor Bike Data) and OpenBikeControl Trainer Data remain available
  to all clients at all times.

**Transport notes:**

- Over BLE most trainers accept a single central, so ownership is usually
  implicit. The rule still applies to trainers that accept multiple centrals.
- Over TCP multiple apps commonly connect at once (for example a trainer app on
  a PC and a bridge app on a phone). The rule is what makes that safe.

---

## Trainer Control (App to Trainer)

**Message Type:** `0x08`

Sets the trainer's operating mode and the simulation or target values. Replaces
the FTMS control point *Set Indoor Bike Simulation Parameters*, *Set Target
Power*, *Set Target Resistance Level* and *Set Wheel Circumference*. Sent on
change; apps MAY repeat it.

**Data Format:**

```
[Message_Type] [Version] [Mode] [Target_Power_L] [Target_Power_H] [Target_Resistance_L] [Target_Resistance_H] [Grade_L] [Grade_H] [Wind_L] [Wind_H] [CRR_L] [CRR_H] [CW_L] [CW_H] [Wheel_Circ_L] [Wheel_Circ_H]
```

Total length: 17 bytes.

- **Message_Type** (1 byte): Always `0x08`
- **Version** (1 byte): Format version, currently `0x01`
- **Mode** (1 byte):
  - `0x00` = Idle. Releases control (see above). The trainer applies no
    resistance beyond its mechanical minimum.
  - `0x01` = Simulation. Resistance follows `Grade`, `Wind`, `CRR`, `CW`, the
    virtual gear ratio if active, and the trainer's speed model.
  - `0x02` = Target power (ERG). Resistance follows `Target_Power`.
  - `0x03` = Target resistance. Resistance is fixed at `Target_Resistance`.
  - `0x04-0xFF` = Reserved; trainers MUST treat these as `0x00`
- **Target_Power** (2 bytes, uint16): Watts. `0xFFFF` = Unchanged.
- **Target_Resistance** (2 bytes, uint16): Resistance level in 0.1 %.
  `0xFFFF` = Unchanged.
- **Grade** (2 bytes, int16): Simulated grade in 0.01 %. `0x7FFF` = Unchanged.
  - Example: 4.50 % → `450` = `[0xC2, 0x01]`; −3.00 % → `−300` = `[0xD4, 0xFE]`
- **Wind** (2 bytes, int16): Simulated wind speed in 0.001 m/s, positive for a
  headwind. `0x7FFF` = Unchanged.
- **CRR** (2 bytes, uint16): Rolling resistance coefficient in 0.0001.
  `0xFFFF` = Unchanged.
  - Example: 0.0040 → `40` = `[0x28, 0x00]`
- **CW** (2 bytes, uint16): Wind resistance coefficient in 0.01 kg/m.
  `0xFFFF` = Unchanged.
  - Example: 0.51 kg/m → `51` = `[0x33, 0x00]`
- **Wheel_Circ** (2 bytes, uint16): Wheel circumference in mm. `0xFFFF` = Unchanged.
  - Example: 2105 mm → `[0x39, 0x08]`

Values the trainer does not support are ignored; the capability bits in Trainer
Status tell the app in advance which ones will be honoured. "Unchanged" keeps the
trainer's current value, so an app can update a single field without resending
the rest.

**Example Messages:**

```
// Simulation mode, grade 4.50 %, no wind, CRR 0.0040, CW 0.51, wheel 2105 mm
[0x08, 0x01, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xC2, 0x01, 0x00, 0x00, 0x28, 0x00, 0x33, 0x00, 0x39, 0x08]

// Grade update only, −3.00 %
[0x08, 0x01, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xD4, 0xFE, 0xFF, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

// ERG mode, 250 W
[0x08, 0x01, 0x02, 0xFA, 0x00, 0xFF, 0xFF, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

// Release control
[0x08, 0x01, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
```

**App Behaviour:**

- Apps SHOULD send grade updates at 1–2 Hz in simulation mode, as they do with
  FTMS, and immediately on mode changes.
- Apps SHOULD send `Mode = 0x00` before disconnecting.

**Trainer Behaviour:**

- Trainers MUST keep the last values until a new message arrives or ownership
  is released.
- On release or disconnect, trainers MUST return to `Mode = 0x00`.
- Trainers MUST NOT reply to this message. The applied values show up in
  Trainer Data and the active mode in Trainer Status.

---

## Trainer Data (Trainer to App)

**Message Type:** `0x09`

Periodic measurements from the trainer. Equivalent to FTMS *Indoor Bike Data*
and sent to every connected client, not only the owner.

**Data Format:**

```
[Message_Type] [Version] [Flags] [Power_L] [Power_H] [Cadence_L] [Cadence_H] [Speed_L] [Speed_H] [Resistance_L] [Resistance_H] [Grade_L] [Grade_H]
```

Total length: 13 bytes.

- **Message_Type** (1 byte): Always `0x09`
- **Version** (1 byte): Format version, currently `0x01`
- **Flags** (1 byte): Bit field marking which fields are valid
  - Bit 0 (`0x01`) = `Power` valid
  - Bit 1 (`0x02`) = `Cadence` valid
  - Bit 2 (`0x04`) = `Speed` valid
  - Bit 3 (`0x08`) = `Resistance` valid
  - Bit 4 (`0x10`) = `Grade` valid
  - Bit 5 (`0x20`) = `Speed` is the simulated bike speed (virtual gearing or
    app-provided speed in use) rather than the measured flywheel speed
  - Bits 6–7 = Reserved, MUST be `0`
- **Power** (2 bytes, uint16): Watts
- **Cadence** (2 bytes, uint16): 0.5 rpm, matching FTMS
- **Speed** (2 bytes, uint16): 0.01 km/h, matching FTMS
- **Resistance** (2 bytes, uint16): Applied resistance level in 0.1 %
- **Grade** (2 bytes, int16): Applied grade in 0.01 %

**Example Message:**

```
// 220 W, 90 rpm, 32.50 km/h, 12.5 % resistance, 4.50 % grade, all valid
[0x09, 0x01, 0x1F, 0xDC, 0x00, 0xB4, 0x00, 0xB2, 0x0C, 0x7D, 0x00, 0xC2, 0x01]
```

**Trainer Behaviour:**

- Trainers SHOULD send Trainer Data at 1–4 Hz while a client is subscribed
  (BLE) or connected (TCP).
- Fields marked invalid MUST be sent as `0`.

---

## Trainer Status (Trainer to App)

**Message Type:** `0x0A`

Capabilities, limits, control ownership and current mode. Replaces FTMS *Fitness
Machine Feature*, *Supported Power/Resistance Range* and the control-related
parts of *Fitness Machine Status*. **Mandatory** for every trainer implementing
the Trainer Service; this is how apps discover everything else.

**Data Format:**

```
[Message_Type] [Version] [Control] [Mode] [Capabilities_L] [Capabilities_H] [Max_Power_L] [Max_Power_H] [Max_Resistance_L] [Max_Resistance_H] [Max_Grade_L] [Max_Grade_H] [Min_Grade_L] [Min_Grade_H] [Calibration]
```

Total length: 15 bytes.

- **Message_Type** (1 byte): Always `0x0A`
- **Version** (1 byte): Format version, currently `0x01`
- **Control** (1 byte): Ownership as seen by the receiving client
  - `0x00` = Nobody controls the trainer
  - `0x01` = The receiving client is the owner
  - `0x02` = Another OpenBikeControl client is the owner
  - `0x03` = An FTMS client holds control
- **Mode** (1 byte): Currently active mode, same values as Trainer Control
- **Capabilities** (2 bytes, uint16): Bit field
  - Bit 0 (`0x0001`) = Simulation mode
  - Bit 1 (`0x0002`) = Target power mode
  - Bit 2 (`0x0004`) = Target resistance mode
  - Bit 3 (`0x0008`) = Virtual shifting (`0x05`/`0x06`)
  - Bit 4 (`0x0010`) = Uses app-provided speed (`0x07`)
  - Bit 5 (`0x0020`) = Trainer-owned gearing (has its own gear table)
  - Bit 6 (`0x0040`) = Wheel circumference
  - Bit 7 (`0x0080`) = Spin-down calibration
  - Bit 8 (`0x0100`) = Reports power
  - Bit 9 (`0x0200`) = Reports cadence
  - Bit 10 (`0x0400`) = Reports speed
  - Bit 11 (`0x0800`) = Has incline hardware (physical tilt)
  - Bits 12–15 = Reserved, MUST be `0`
- **Max_Power** (2 bytes, uint16): Highest target power accepted, in W.
  `0` = Not applicable.
- **Max_Resistance** (2 bytes, uint16): Highest resistance level, in 0.1 %.
  `0` = Not applicable.
- **Max_Grade** (2 bytes, int16): Steepest positive grade simulated, in 0.01 %.
- **Min_Grade** (2 bytes, int16): Steepest negative grade simulated, in 0.01 %.
  Trainers that cannot simulate descents report `0`.
- **Calibration** (1 byte):
  - `0x00` = Not supported / unknown
  - `0x01` = Calibrated
  - `0x02` = Calibration recommended
  - `0x03` = Calibration in progress
  - `0x04` = Last calibration failed

**Example Messages:**

```
// Direct-drive trainer: sim, ERG, resistance, virtual shifting, app speed, wheel
// circumference, spin-down, power/cadence/speed; 2000 W, 100 %, +20 % / -10 %;
// this client owns control, simulation active, calibrated
[0x0A, 0x01, 0x01, 0x01, 0xDF, 0x07, 0xD0, 0x07, 0xE8, 0x03, 0xD0, 0x07, 0x18, 0xFC, 0x01]

// Same trainer, but another OpenBikeControl client owns it and runs ERG
[0x0A, 0x01, 0x02, 0x02, 0xDF, 0x07, 0xD0, 0x07, 0xE8, 0x03, 0xD0, 0x07, 0x18, 0xFC, 0x01]

// Smart bike with its own gear table, no app speed, no wheel circumference;
// nobody in control, idle
[0x0A, 0x01, 0x00, 0x00, 0x2F, 0x07, 0xD0, 0x07, 0xE8, 0x03, 0xD0, 0x07, 0x18, 0xFC, 0x01]
```

**Trainer Behaviour:**

- Trainers MUST send Trainer Status once when a client subscribes (BLE) or
  right after the connection is established (TCP, after version negotiation if
  any), and again whenever any field changes.
- When ownership changes, Trainer Status MUST be sent to every connected client,
  because the `Control` value differs per client.

---

## Calibration (Reserved)

Message types `0x0B` (Calibration Control, app to trainer) and `0x0C`
(Calibration State, trainer to app) are reserved for a spin-down procedure and
will be specified separately. Until then, trainers report calibration state in
Trainer Status and perform calibration through FTMS or their vendor app.

---

## Transport Mapping

### BLE: Trainer Service

**Service UUID:** `d273f690-d548-419d-b9d1-fa0472345229`

| Characteristic           | UUID                                   | Properties                    | Message | Required |
|--------------------------|----------------------------------------|-------------------------------|---------|----------|
| Virtual Shifting Control | `d273f691-d548-419d-b9d1-fa0472345229` | Write, Write Without Response | `0x05`  | if capability bit 3 |
| Virtual Shifting State   | `d273f692-d548-419d-b9d1-fa0472345229` | Read, Notify                  | `0x06`  | if capability bit 3 |
| Ride State               | `d273f693-d548-419d-b9d1-fa0472345229` | Write Without Response        | `0x07`  | if capability bit 4 |
| Trainer Control          | `d273f694-d548-419d-b9d1-fa0472345229` | Write, Write Without Response | `0x08`  | if capability bits 0–2 |
| Trainer Data             | `d273f695-d548-419d-b9d1-fa0472345229` | Read, Notify                  | `0x09`  | if capability bits 8–10 |
| Trainer Status           | `d273f696-d548-419d-b9d1-fa0472345229` | Read, Notify                  | `0x0A`  | yes |

The Trainer Service is separate from the controller service
(`d273f680-…`). A smart bike with shifters and buttons exposes both; a
direct-drive trainer exposes only the Trainer Service; a handlebar remote only
the controller service. The Button State characteristic on the controller
service is unchanged by this profile.

**Advertisement:** Trainers advertise the Trainer Service UUID. A device that
offers both services cannot fit two 128-bit UUIDs into one advertising packet;
such devices SHOULD put the controller service UUID in the advertising packet
and the Trainer Service UUID in the scan response. Apps MUST discover services
after connecting rather than relying on the advertisement alone.

### mDNS / TCP

The Trainer Service UUID is listed in the `service-uuids` TXT record field, which
is how apps discover trainers on the network. All trainer messages share the TCP
connection with the controller messages. Trainers SHOULD support
[version 2 framing](MDNS.md#message-framing-version-2), since Trainer Data and
Ride State are continuous streams and version 1 cannot delimit merged messages.

---

## See Also

- [Main Protocol Documentation](PROTOCOL.md)
- [Virtual Shifting Extension](VIRTUAL_SHIFTING.md)
- [BLE Protocol Specification](BLE.md)
- [mDNS Protocol Specification](MDNS.md)
