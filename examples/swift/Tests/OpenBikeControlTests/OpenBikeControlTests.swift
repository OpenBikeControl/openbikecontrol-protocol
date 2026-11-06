//
//  OpenBikeControlTests.swift
//
//  The codec against the spec's own examples, plus vectors produced by the project's
//  Python reference implementation (examples/python/protocol_parser.py): device → app
//  messages built by its encoder with its parser's reading of each pair, and app → device
//  messages that must be byte-identical to what it encodes. If these pass, the only thing
//  left to check on hardware is what the device chooses to send.
//

import XCTest
@testable import OpenBikeControl

final class OpenBikeControlTests: XCTestCase {

    private func data(_ hex: String) -> Data {
        Data(stride(from: 0, to: hex.count, by: 2).map { i -> UInt8 in
            let a = hex.index(hex.startIndex, offsetBy: i)
            return UInt8(hex[a..<hex.index(a, offsetBy: 2)], radix: 16)!
        })
    }

    private func hex(_ data: Data) -> String {
        data.map { String(format: "%02x", $0) }.joined()
    }

    // MARK: Button State

    func testSpecExampleParses() {
        // BLE.md / PROTOCOL.md example: Shift Up, Increase Difficulty and Select pressed together.
        let events = OpenBikeControl.parseButtonState(data("01010130011401"))
        XCTAssertEqual(events?.map(\.button), [.shiftUp, .increaseDifficulty, .select])
        XCTAssertEqual(events?.allSatisfy(\.isPress), true)
    }

    func testReleasesRejectsAndDanglingBytes() {
        XCTAssertEqual(OpenBikeControl.parseButtonState(data("013500"))?.first?.isRelease, true)
        XCTAssertNil(OpenBikeControl.parseButtonState(data("03010500")), "a haptic-typed message is not button state")
        XCTAssertNil(OpenBikeControl.parseButtonState(data("0000")), "zero bytes are not button state")
        XCTAssertNil(OpenBikeControl.parseButtonState(Data()))
        XCTAssertEqual(OpenBikeControl.parseButtonState(data("01")), [], "an empty button-state message is legal")
        XCTAssertEqual(OpenBikeControl.parseButtonState(data("0135")), [], "a dangling ID with no value is ignored")
        XCTAssertEqual(OpenBikeControl.parseButtonState(data("01030504")), [.init(id: 0x03, value: 0x05)],
                       "the complete pair before a dangling byte survives")
    }

    func testCustomIDsAreKept() {
        let e = OpenBikeControl.parseButtonState(data("018501"))!.first!
        XCTAssertNil(e.button)
        XCTAssertTrue(e.isPress)
        XCTAssertEqual(e.description, "Button 0x85: pressed")
    }

    // MARK: Gear values

    func testGearValueDecoding() {
        XCTAssertEqual(OpenBikeControl.gearPosition(from: 0x02), 1)
        XCTAssertEqual(OpenBikeControl.gearPosition(from: 0x0D), 12)
        XCTAssertEqual(OpenBikeControl.gearPosition(from: 0xFF), 254)
        XCTAssertNil(OpenBikeControl.gearPosition(from: 0x00))
        XCTAssertNil(OpenBikeControl.gearPosition(from: 0x01), "0x01 is a reserved no-op for gear IDs")
    }

    func testGearDisplay() {
        var gear = OpenBikeControl.Gear()
        XCTAssertNil(gear.displayText)
        // A 2× bike reports chainring 2, cog 7 and a flattened index in one message.
        XCTAssertTrue(gear.apply(OpenBikeControl.parseButtonState(data("01040305080312"))!))
        XCTAssertEqual(gear, OpenBikeControl.Gear(flat: 17, front: 2, rear: 7))
        XCTAssertEqual(gear.displayText, "2·7")
        // A no-change message (0x00 values) leaves the gear alone.
        XCTAssertFalse(gear.apply(OpenBikeControl.parseButtonState(data("0104000500"))!))
        XCTAssertEqual(gear.displayText, "2·7")
        // 1×: only the cassette reports; flat index is the fallback.
        XCTAssertEqual(OpenBikeControl.Gear(rear: 11).displayText, "11")
        XCTAssertEqual(OpenBikeControl.Gear(flat: 5).displayText, "5")
        // Analog gear IDs never count as a press; a Lap press does.
        XCTAssertFalse(OpenBikeControl.Event(id: 0x03, value: 0x01).isPress)
        XCTAssertTrue(OpenBikeControl.Event(id: 0x35, value: 0x01).isPress)
    }

    // MARK: App Information

    func testAppInformationEncoding() {
        let bytes = [UInt8](OpenBikeControl.appInformation(appID: "my-app", appVersion: "2.0", buttons: [.lap, .pause]))
        XCTAssertEqual(Array(bytes.prefix(2)), [0x04, 0x01])
        XCTAssertEqual(bytes[2], 6)
        XCTAssertEqual(String(bytes: bytes[3..<9], encoding: .utf8), "my-app")
        XCTAssertEqual(bytes[9], 3)
        XCTAssertEqual(String(bytes: bytes[10..<13], encoding: .utf8), "2.0")
        XCTAssertEqual(bytes[13], 2)
        XCTAssertEqual(Array(bytes[14...]), [0x35, 0x33])
        // Strings are capped at 32 bytes, as the spec allows.
        let long = OpenBikeControl.appInformation(appID: String(repeating: "x", count: 40), appVersion: "1", buttons: [])
        XCTAssertEqual([UInt8](long)[2], 32)
    }

    func testAppInformationSpecExample() {
        // BLE.md: "zwift", "1.52.0", buttons [0x01, 0x02, 0x10, 0x14]
        let info = OpenBikeControl.AppInformation(appID: "zwift", appVersion: "1.52.0", buttons: [.shiftUp, .shiftDown, .up, .select])
        XCTAssertEqual(hex(info.encoded), "0401057a7769667406312e35322e300401021014")
        XCTAssertEqual(OpenBikeControl.AppInformation.parse(info.encoded), info)
    }

    func testAppInformationParseRejectsMalformed() {
        XCTAssertNil(OpenBikeControl.AppInformation.parse(data("0301")))
        XCTAssertNil(OpenBikeControl.AppInformation.parse(data("0402050000000000")), "unknown version")
        XCTAssertNil(OpenBikeControl.AppInformation.parse(data("0401057a7769")), "app ID runs past the end")
        XCTAssertNil(OpenBikeControl.AppInformation.parse(data("0401057a776966740101")), "no button count")
        XCTAssertNil(OpenBikeControl.AppInformation.parse(data("0401057a7769667401310201")), "fewer IDs than declared")
        let empty = OpenBikeControl.AppInformation.parse(data("0401000000"))
        XCTAssertEqual(empty, OpenBikeControl.AppInformation(appID: "", appVersion: "", buttonIDs: []))
    }

    // MARK: Haptic Feedback

    func testHapticEncoding() {
        XCTAssertEqual([UInt8](OpenBikeControl.hapticFeedback(pattern: .double, durationMs: 250, intensity: 0x80)), [0x03, 0x02, 25, 0x80])
        XCTAssertEqual([UInt8](OpenBikeControl.hapticFeedback(pattern: .none)), [0x03, 0x00, 0x00, 0x00])
        XCTAssertEqual([UInt8](OpenBikeControl.hapticFeedback(pattern: .error, durationMs: 9999, intensity: 255)), [0x03, 0x07, 0xFF, 0xFF], "duration clamps")
        // BLE.md example: double pulse, 200 ms, intensity 128
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .double, durationMs: 200, intensity: 128)), "03021480")
        XCTAssertEqual(OpenBikeControl.HapticFeedback.parse(data("03021480")),
                       OpenBikeControl.HapticFeedback(pattern: .double, durationMs: 200, intensity: 128))
        XCTAssertNil(OpenBikeControl.HapticFeedback.parse(data("030214")))
        XCTAssertNil(OpenBikeControl.HapticFeedback.parse(data("04021480")))
    }

    // MARK: - Cross-check against the Python reference implementation
    //
    // Generated 2026-10-14 against examples/python/protocol_parser.py at commit 20c063d.
    // `gear` is the reference's "GEAR n" reading, `pressed`/`released` whether its
    // display text ends in ": PRESSED" / ": RELEASED". Analog IDs — gear, brake,
    // steering, cruise control, emote, camera — are never "pressed" there, and the
    // same is true of `Event.isPress` here.

    func testReferenceDeviceToAppVectors() {
        struct V { let hex: String; let pairs: [(UInt8, UInt8)]; let gear: [Int?]; let pressed: [Bool]; let released: [Bool] }
        let vectors: [V] = [
            V(hex: "01010130011401", pairs: [(0x01, 1), (0x30, 1), (0x14, 1)], gear: [nil, nil, nil], pressed: [true, true, true], released: [false, false, false]),
            V(hex: "013501",         pairs: [(0x35, 1)],                        gear: [nil],           pressed: [true],  released: [false]),
            V(hex: "013500",         pairs: [(0x35, 0)],                        gear: [nil],           pressed: [false], released: [true]),
            V(hex: "01040305080312", pairs: [(0x04, 3), (0x05, 8), (0x03, 18)], gear: [2, 7, 17],      pressed: [false, false, false], released: [false, false, false]),
            V(hex: "0104000500",     pairs: [(0x04, 0), (0x05, 0)],             gear: [nil, nil],      pressed: [false, false], released: [true, true]),
            V(hex: "010302",         pairs: [(0x03, 2)],                        gear: [1],             pressed: [false], released: [false]),
            V(hex: "0103ff",         pairs: [(0x03, 255)],                      gear: [254],           pressed: [false], released: [false]),
            V(hex: "010301",         pairs: [(0x03, 1)],                        gear: [nil],           pressed: [false], released: [false]),   // reserved no-op
            V(hex: "0133013001",     pairs: [(0x33, 1), (0x30, 1)],             gear: [nil, nil],      pressed: [true, true], released: [false, false]),
            V(hex: "013601",         pairs: [(0x36, 1)],                        gear: [nil],           pressed: [true],  released: [false]),
            V(hex: "011a65",         pairs: [(0x1A, 0x65)],                     gear: [nil],           pressed: [false], released: [false]),   // brake 100%
            V(hex: "011a01",         pairs: [(0x1A, 0x01)],                     gear: [nil],           pressed: [false], released: [false]),   // brake full, single lever
            V(hex: "011b80",         pairs: [(0x1B, 0x80)],                     gear: [nil],           pressed: [false], released: [false]),   // steering centre
            V(hex: "011b94",         pairs: [(0x1B, 0x94)],                     gear: [nil],           pressed: [false], released: [false]),   // steering right 10°
            V(hex: "013c01",         pairs: [(0x3C, 0x01)],                     gear: [nil],           pressed: [false], released: [false]),   // cruise: engage at current power
            V(hex: "013c28",         pairs: [(0x3C, 0x28)],                     gear: [nil],           pressed: [false], released: [false]),   // cruise 200 W
            V(hex: "012001",         pairs: [(0x20, 0x01)],                     gear: [nil],           pressed: [false], released: [false]),   // emote cycle
            V(hex: "014001",         pairs: [(0x40, 0x01)],                     gear: [nil],           pressed: [false], released: [false]),   // camera cycle
            V(hex: "018501",         pairs: [(0x85, 0x01)],                     gear: [nil],           pressed: [true],  released: [false]),   // app-specific ID
            V(hex: "01",             pairs: [],                                 gear: [],              pressed: [], released: []),
            // Raw bytes the reference parser accepts or yields nothing for (not produced by its encoder).
            V(hex: "01030504",       pairs: [(0x03, 5)],                        gear: [4],             pressed: [false], released: [false]),   // dangling byte ignored
            V(hex: "0135",           pairs: [],                                 gear: [],              pressed: [], released: []),
        ]
        for v in vectors {
            let events = OpenBikeControl.parseButtonState(data(v.hex))
            XCTAssertEqual(events?.map { [$0.id, $0.value] }, v.pairs.map { [$0.0, $0.1] }, v.hex)
            for (i, e) in (events ?? []).enumerated() {
                let gear = (e.button?.isGearPosition ?? false) ? OpenBikeControl.gearPosition(from: e.value) : nil
                XCTAssertEqual(gear, v.gear[i], v.hex)
                XCTAssertEqual(e.isPress, v.pressed[i], v.hex)
                XCTAssertEqual(e.isRelease, v.released[i], v.hex)
            }
        }
        // Messages the reference parser yields nothing for.
        XCTAssertNil(OpenBikeControl.parseButtonState(data("0000")))
        XCTAssertNil(OpenBikeControl.parseButtonState(data("03010500")))
    }

    func testReferenceDescriptions() {
        // The reference's display text, in this codec's wording.
        let expectations: [(String, String)] = [
            ("01040305080312", "Chainring Set: gear 2"),
            ("010301", "Gear Set: no-op (reserved)"),
            ("011a65", "Brake: 100%"),
            ("011a01", "Brake: 100%"),
            ("011b80", "Steering Angle: center"),
            ("011b94", "Steering Angle: right 10.0°"),
            ("013c01", "Cruise Control: engage at current power"),
            ("013c28", "Cruise Control: target 200 W"),
            ("012001", "Emote: pressed (cycle)"),
            ("013601", "Previous Interval: pressed"),
        ]
        for (hex, text) in expectations {
            XCTAssertEqual(OpenBikeControl.parseButtonState(data(hex))?.first?.description, text, hex)
        }
    }

    func testReferenceAppToDeviceVectors() {
        // encode_app_info("swift-example", "1.0.0", [0x03,0x04,0x05,0x33,0x34,0x35,0x32,0x36,0x30,0x31])
        let info = OpenBikeControl.AppInformation(appID: "swift-example", appVersion: "1.0.0", buttons: [
            .gearSet, .chainringSet, .cassetteSet,
            .pause, .resume, .lap, .skipInterval, .previousInterval,
            .increaseDifficulty, .decreaseDifficulty,
        ])
        XCTAssertEqual(hex(info.encoded), "04010d73776966742d6578616d706c6505312e302e300a03040533343532363031")
        XCTAssertEqual(OpenBikeControl.AppInformation.parse(info.encoded), info)
        // encode_haptic_feedback(pattern, duration /10 ms, intensity)
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .short)), "03010000")
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .double, durationMs: 250, intensity: 128)), "03021980")
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .success, intensity: 255)), "030500ff")
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .error, durationMs: 2550, intensity: 255)), "0307ffff")
        XCTAssertEqual(hex(OpenBikeControl.hapticFeedback(pattern: .none)), "03000000")
    }
}
