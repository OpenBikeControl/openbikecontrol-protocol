//
//  OpenBikeControl.swift
//
//  The OpenBikeControl message codec in Swift: service and characteristic UUIDs,
//  the standard button IDs, Button State parsing, and App Information / Haptic
//  Feedback encoding. Pure Foundation — no CoreBluetooth — so the same file works
//  on iOS, macOS, tvOS and watchOS, and is unit-tested against the spec's own
//  examples plus vectors produced by the project's Python reference implementation
//  (examples/python/protocol_parser.py).
//
//  Spec: PROTOCOL.md (button IDs, analog values) and BLE.md (characteristics,
//  message formats). The BLE and TCP/mDNS transports share this byte format,
//  including the leading message-type byte.
//
//  Released under the MIT License, like the protocol itself.
//

import Foundation

public enum OpenBikeControl {

    // MARK: - BLE identifiers (BLE.md)

    public static let serviceUUIDString        = "D273F680-D548-419D-B9D1-FA0472345229"
    public static let buttonStateUUIDString    = "D273F681-D548-419D-B9D1-FA0472345229"   // read, notify — device → app
    public static let hapticFeedbackUUIDString = "D273F682-D548-419D-B9D1-FA0472345229"   // write — app → device
    public static let appInformationUUIDString = "D273F683-D548-419D-B9D1-FA0472345229"   // write — app → device

    // MARK: - Message types (first byte of every message)

    public static let buttonStateType: UInt8    = 0x01
    public static let deviceStatusType: UInt8   = 0x02   // TCP/mDNS transport only
    public static let hapticFeedbackType: UInt8 = 0x03
    public static let appInformationType: UInt8 = 0x04

    // MARK: - Button IDs (PROTOCOL.md § Button Mapping)

    public enum Button: UInt8, CaseIterable {
        // Gear shifting (0x01–0x0F)
        case shiftUp = 0x01, shiftDown = 0x02
        case gearSet = 0x03, chainringSet = 0x04, cassetteSet = 0x05
        // Navigation (0x10–0x1F)
        case up = 0x10, down = 0x11, left = 0x12, right = 0x13
        case select = 0x14, back = 0x15, menu = 0x16, home = 0x17
        case steerLeft = 0x18, steerRight = 0x19, brake = 0x1A, steeringAngle = 0x1B
        // Social / emotes (0x20–0x2F)
        case emote = 0x20, pushToTalk = 0x21, screenshot = 0x24
        // Training controls (0x30–0x3F)
        case increaseDifficulty = 0x30, decreaseDifficulty = 0x31
        case skipInterval = 0x32, pause = 0x33, resume = 0x34, lap = 0x35
        case previousInterval = 0x36, uTurn = 0x37, changeMode = 0x38
        case takeABreak = 0x39, joinRider = 0x3A, changeRoute = 0x3B, cruiseControl = 0x3C
        // View controls (0x40–0x4F)
        case cameraView = 0x40, hudToggle = 0x44, mapToggle = 0x45, spectate = 0x46
        // Power-ups (0x50–0x5F)
        case powerUp1 = 0x50, powerUp2 = 0x51, powerUp3 = 0x52

        /// IDs whose value byte is a quantity (gear index, percentage, angle, watts),
        /// not a pressed/released flag.
        public var isAnalog: Bool {
            switch self {
            case .gearSet, .chainringSet, .cassetteSet, .brake, .steeringAngle, .emote, .cruiseControl, .cameraView:
                return true
            default:
                return false
            }
        }

        /// The three direct gear-selection IDs, whose value is a 1-based position offset by +1.
        public var isGearPosition: Bool {
            self == .gearSet || self == .chainringSet || self == .cassetteSet
        }

        /// Human-readable name, matching the spec's tables.
        public var name: String {
            switch self {
            case .shiftUp: return "Shift Up"
            case .shiftDown: return "Shift Down"
            case .gearSet: return "Gear Set"
            case .chainringSet: return "Chainring Set"
            case .cassetteSet: return "Cassette Set"
            case .up: return "Up"
            case .down: return "Down"
            case .left: return "Left/Look Left"
            case .right: return "Right/Look Right"
            case .select: return "Select/Confirm"
            case .back: return "Back/Cancel"
            case .menu: return "Menu"
            case .home: return "Home"
            case .steerLeft: return "Steer Left"
            case .steerRight: return "Steer Right"
            case .brake: return "Brake"
            case .steeringAngle: return "Steering Angle"
            case .emote: return "Emote"
            case .pushToTalk: return "Push to Talk"
            case .screenshot: return "Screenshot"
            case .increaseDifficulty: return "Increase Difficulty"
            case .decreaseDifficulty: return "Decrease Difficulty"
            case .skipInterval: return "Skip Interval"
            case .pause: return "Pause"
            case .resume: return "Resume"
            case .lap: return "Lap"
            case .previousInterval: return "Previous Interval"
            case .uTurn: return "U-Turn"
            case .changeMode: return "Change Mode"
            case .takeABreak: return "Take a Break"
            case .joinRider: return "Join Rider"
            case .changeRoute: return "Change Route"
            case .cruiseControl: return "Cruise Control"
            case .cameraView: return "Camera View"
            case .hudToggle: return "HUD Toggle"
            case .mapToggle: return "Map Toggle"
            case .spectate: return "Spectate"
            case .powerUp1: return "Power-up 1"
            case .powerUp2: return "Power-up 2"
            case .powerUp3: return "Power-up 3"
            }
        }
    }

    /// One ID/value pair from a Button State message.
    public struct Event: Equatable {
        public let id: UInt8
        public let value: UInt8

        public init(id: UInt8, value: UInt8) {
            self.id = id
            self.value = value
        }

        /// The standard button this ID maps to, or nil for custom / manufacturer IDs (0x60–0xFF).
        public var button: Button? { Button(rawValue: id) }

        /// Digital press (value 0x01). Analog IDs never "press" — their 0x01 has its own meaning.
        public var isPress: Bool { value == 0x01 && !(button?.isAnalog ?? false) }
        public var isRelease: Bool { value == 0x00 }

        /// The spec's reading of this pair, for logs: "Lap: pressed", "Cassette Set: gear 7",
        /// "Brake: 100%", "Cruise Control: target 200 W".
        public var description: String {
            let name = button?.name ?? String(format: "Button 0x%02X", id)
            guard let b = button else {
                return "\(name): \(value == 0 ? "released" : value == 1 ? "pressed" : "value \(value)")"
            }
            switch b {
            case .gearSet, .chainringSet, .cassetteSet:
                if value == 0 { return "\(name): released" }
                if value == 1 { return "\(name): no-op (reserved)" }
                return "\(name): gear \(value - 1)"
            case .brake:
                // value − 1 = percent (two levers can reach 200%); 0x01 is full on a single lever.
                if value == 0 { return "\(name): released" }
                if value == 1 { return "\(name): 100%" }
                return "\(name): \(min(Int(value) - 1, 200))%"
            case .steeringAngle:
                if value == 0 { return "\(name): unavailable" }
                if value == 1 || value == 0xFF { return "\(name): no-op (reserved)" }
                let degrees = Double(Int(value) - 0x80) * 0.5
                if degrees == 0 { return "\(name): center" }
                return String(format: "%@: %@ %.1f°", name, degrees > 0 ? "right" : "left", abs(degrees))
            case .cruiseControl:
                if value == 0 { return "\(name): released" }
                if value == 1 { return "\(name): engage at current power" }
                if value < 0x0A { return "\(name): no-op (reserved)" }
                return "\(name): target \(Int(value) * 5) W"
            case .emote, .cameraView:
                if value == 0 { return "\(name): released" }
                if value == 1 { return "\(name): pressed (cycle)" }
                return "\(name): value \(value)"
            default:
                if value == 0 { return "\(name): released" }
                if value == 1 { return "\(name): pressed" }
                return "\(name): analog \(value)"
            }
        }
    }

    // MARK: - Button State (notify): [0x01] [ID] [value] [ID] [value] …

    /// Parse a Button State message into its ID/value pairs. Returns nil when the
    /// first byte is not the Button State type (0x01). A dangling trailing byte
    /// with no value is ignored, as the Python reference parser ignores it — the
    /// complete pairs before it are still real. An empty message `[0x01]` is legal
    /// and yields no events.
    public static func parseButtonState(_ data: Data) -> [Event]? {
        let bytes = [UInt8](data)
        guard let first = bytes.first, first == buttonStateType else { return nil }
        var events: [Event] = []
        var it = bytes.dropFirst().makeIterator()
        while let id = it.next(), let value = it.next() {
            events.append(Event(id: id, value: value))
        }
        return events
    }

    // MARK: - Gear values (PROTOCOL.md § Gear Selection Analog Values)

    /// Gear Set / Chainring Set / Cassette Set carry a 1-based position offset by +1:
    /// 0x02 is gear 1, 0x03 is gear 2 … up to 254 positions. 0x00 means released /
    /// no change and 0x01 is a reserved no-op. Returns the 1-based gear, or nil.
    public static func gearPosition(from value: UInt8) -> Int? {
        guard value >= 0x02 else { return nil }
        return Int(value) - 1
    }

    /// The gear a device reports, kept up to date from Button State events.
    /// A bike with real shifters (the Stages SB200, for example) reports its own
    /// gear this way so the app can display it.
    public struct Gear: Equatable {
        public var flat: Int?    // sequential index, 1-based (Gear Set, 0x03)
        public var front: Int?   // chainring, 1-based (Chainring Set, 0x04)
        public var rear: Int?    // cassette cog, 1-based (Cassette Set, 0x05)

        public init(flat: Int? = nil, front: Int? = nil, rear: Int? = nil) {
            self.flat = flat
            self.front = front
            self.rear = rear
        }

        /// "2·7" for a front/rear drivetrain, "7" for a 1x one, the flat index as a
        /// fallback, nil when nothing is known yet.
        public var displayText: String? {
            if let f = front, let r = rear { return "\(f)·\(r)" }
            if let r = rear { return "\(r)" }
            if let g = flat { return "\(g)" }
            return nil
        }

        /// Apply one message's events; returns true when the gear changed.
        @discardableResult
        public mutating func apply(_ events: [Event]) -> Bool {
            let before = self
            for e in events {
                guard let b = e.button, let pos = gearPosition(from: e.value) else { continue }
                switch b {
                case .gearSet:      flat = pos
                case .chainringSet: front = pos
                case .cassetteSet:  rear = pos
                default: break
                }
            }
            return self != before
        }
    }

    // MARK: - App Information (write): [0x04] [ver=0x01] [len][appID] [len][appVersion] [count] [IDs…]

    /// What an app tells the device about itself right after connecting (BLE.md § 3).
    /// The button list says which actions the app understands, so the device can
    /// pick sensible button mappings and highlight what works. Declare the IDs you
    /// actually handle. An app that leaves gearing to the bike and only displays
    /// the reported gear declares 0x03–0x05 and not Shift Up / Shift Down.
    public struct AppInformation: Equatable {
        public var appID: String
        public var appVersion: String
        public var buttons: [UInt8]

        public init(appID: String, appVersion: String, buttons: [Button]) {
            self.init(appID: appID, appVersion: appVersion, buttonIDs: buttons.map(\.rawValue))
        }

        public init(appID: String, appVersion: String, buttonIDs: [UInt8]) {
            self.appID = appID
            self.appVersion = appVersion
            self.buttons = buttonIDs
        }

        /// The wire bytes. Strings are UTF-8, capped at 32 bytes as the spec allows;
        /// an empty button list means "all buttons supported".
        public var encoded: Data {
            func field(_ s: String) -> [UInt8] {
                let utf8 = Array(s.utf8.prefix(32))
                return [UInt8(utf8.count)] + utf8
            }
            var bytes: [UInt8] = [appInformationType, 0x01]
            bytes += field(appID)
            bytes += field(appVersion)
            let ids = Array(buttons.prefix(255))
            bytes.append(UInt8(ids.count))
            bytes += ids
            return Data(bytes)
        }

        /// Device-side decoding. Returns nil for a malformed message or an unknown
        /// format version.
        public static func parse(_ data: Data) -> AppInformation? {
            let b = [UInt8](data)
            guard b.count >= 5, b[0] == appInformationType, b[1] == 0x01 else { return nil }
            var i = 2
            func string() -> String? {
                guard i < b.count else { return nil }
                let n = Int(b[i]); i += 1
                guard i + n <= b.count, let s = String(bytes: b[i..<i + n], encoding: .utf8) else { return nil }
                i += n
                return s
            }
            guard let appID = string(), let appVersion = string(), i < b.count else { return nil }
            let count = Int(b[i]); i += 1
            guard i + count <= b.count else { return nil }
            return AppInformation(appID: appID, appVersion: appVersion, buttonIDs: Array(b[i..<i + count]))
        }
    }

    /// Convenience for the common case: encode in one call.
    public static func appInformation(appID: String, appVersion: String, buttons: [Button]) -> Data {
        AppInformation(appID: appID, appVersion: appVersion, buttons: buttons).encoded
    }

    // MARK: - Haptic Feedback (write): [0x03] [pattern] [duration/10 ms] [intensity]

    public enum HapticPattern: UInt8 {
        case none = 0x00, short = 0x01, double = 0x02, triple = 0x03
        case long = 0x04, success = 0x05, warning = 0x06, error = 0x07
    }

    public struct HapticFeedback: Equatable {
        public var pattern: UInt8
        /// Duration in milliseconds, rounded down to 10 ms units on the wire; 0 = pattern default.
        public var durationMs: Int
        /// 0 = pattern default, 0x01–0xFF = low to maximum.
        public var intensity: UInt8

        public init(pattern: HapticPattern, durationMs: Int = 0, intensity: UInt8 = 0) {
            self.init(patternByte: pattern.rawValue, durationMs: durationMs, intensity: intensity)
        }

        public init(patternByte: UInt8, durationMs: Int = 0, intensity: UInt8 = 0) {
            self.pattern = patternByte
            self.durationMs = durationMs
            self.intensity = intensity
        }

        public var encoded: Data {
            Data([hapticFeedbackType, pattern, UInt8(clamping: durationMs / 10), intensity])
        }

        /// Device-side decoding. Returns nil unless the message is exactly four bytes of type 0x03.
        public static func parse(_ data: Data) -> HapticFeedback? {
            let b = [UInt8](data)
            guard b.count == 4, b[0] == hapticFeedbackType else { return nil }
            return HapticFeedback(patternByte: b[1], durationMs: Int(b[2]) * 10, intensity: b[3])
        }
    }

    /// Convenience for the common case: encode in one call.
    public static func hapticFeedback(pattern: HapticPattern, durationMs: Int = 0, intensity: UInt8 = 0) -> Data {
        HapticFeedback(pattern: pattern, durationMs: durationMs, intensity: intensity).encoded
    }
}
