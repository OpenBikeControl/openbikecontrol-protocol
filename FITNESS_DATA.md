# Fitness Data and Sensor Bridging Extension

This optional extension lets a bridge collect measurements from a smart trainer
and independent BLE, ANT+, or other sensors, then expose them through one
OpenBikeControl session. Applications consume the same messages regardless of
the upstream sensor transport.

## Scope and coexistence

The extension is for measurements. Trainer control remains the responsibility
of the Trainer Profile. A bridge MAY expose controller input, trainer data, and
sensor data on the same BLE characteristic or TCP connection. Implementations
MUST treat each source independently and MUST NOT merge two sources into one
value without marking the result as derived.

Trainer measurements have one home per session. When the Trainer Profile is
active, the bridge MUST report the trainer's power, cadence, and speed through
Trainer Data and MUST NOT repeat them here. Source type `0x01` (trainer) is for
bridges that relay a trainer's measurements without implementing the Trainer
Profile, for example a read-only relay to a computer without Bluetooth.

### Relation to standard-profile bridging

A bridge can already re-expose sensors as one standard trainer device, picking
one source per signal (for example over FTMS or Direct Connect). This extension
does not replace that. It is for applications that want what such a bridge
hides:

- which source produced each value, and whether it is stale or derived;
- several sources for the same measurement at once, leaving the choice to the
  application;
- sensor data on the OpenBikeControl connection the application already uses
  for controller input, without adding an FTMS or Direct Connect stack.

Measurements are typed values, never raw BLE or ANT+ payloads, so applications
do not need to know the upstream sensor protocol. New measurements are added by
assigning new IDs.

The initial measurement IDs are:

| ID | Measurement | Unit and encoding |
| --- | --- | --- |
| `0x01` | Power | unsigned 16-bit watts |
| `0x02` | Cadence | unsigned 16-bit 0.01 RPM |
| `0x03` | Speed | unsigned 16-bit 0.01 km/h |
| `0x04` | Heart rate | unsigned 8-bit BPM |

All multi-byte integers are little-endian, matching the Trainer Profile and
FTMS. Reserved measurement IDs MUST be
ignored by receivers.

## Message types

The messages below use the existing message-type prefix and are valid over BLE
and TCP. TCP messages are still wrapped in the version 2 length prefix.

Message types `0x0B` and `0x0C` are reserved by the Trainer Profile for
calibration. This extension therefore uses `0x0D`–`0x0F`.

### Capability advertisement (`0x0D`)

```
[0x0D, Version, Source_Count, Source...]
Source = [Source_ID, Source_Type, Measurement_Count, Measurement_ID...]
```

`Version` is `0x01`. `Source_ID` is unique for the lifetime of the session.
`Source_Type` is `0x01` trainer, `0x02` heart-rate sensor, `0x03` power meter,
`0x04` cadence sensor, `0x05` speed sensor, or `0x06` other. A source MAY
advertise more than one measurement. A count of zero means no sources are
available.

### Source lifecycle (`0x0E`)

```
[0x0E, Source_ID, State]
```

`State` is `0x01` connected, `0x02` disconnected, or `0x03` temporarily
unavailable. A disconnected source MUST stop producing measurements. A bridge
MUST send a lifecycle message when a source changes state.

### Measurement (`0x0F`)

```
[0x0F, Source_ID, Measurement_ID, Flags, Sequence, Value...]
```

`Sequence` wraps at 255 and is scoped to the source. `Flags` is `0x01` valid,
`0x02` stale, or `0x04` derived; flags MAY be combined. A stale value MUST NOT
be presented as current data. The value width is determined by the measurement
ID table. A bridge SHOULD send measurements at the source's natural rate and
MUST NOT invent a zero when a source becomes unavailable.

Applications choose among multiple sources reporting the same measurement. The
protocol does not define source precedence. A receiver MUST ignore a
measurement whose source is unknown or whose payload is truncated.

## Discovery

Network bridges advertise `_openbikecontrol._tcp.local.` as usual. They SHOULD
include `fitness-data=1` in the mDNS TXT records. The complete source inventory
is sent with `0x0D` after the connection is established; TXT records are only a
filter for discovery and are not a substitute for capability negotiation.

BLE implementations MAY expose the extension through the existing OpenBikeControl
service. A bridge that supports the extension MUST include `fitness-data=1` in
its advertised capability metadata and send the same messages on the notifying
characteristic.

## Privacy and identifiers

Source IDs are session-scoped by default. Implementations SHOULD avoid exposing
BLE addresses or serial numbers unless the user has explicitly enabled device
identification. Manufacturer and model metadata may be provided through the
existing device metadata mechanisms.
