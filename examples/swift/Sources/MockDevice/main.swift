//
//  obc-mock-device — a fake OpenBikeControl device for testing an app without hardware.
//
//  Runs on a Mac as a Bluetooth PERIPHERAL: advertises the OpenBikeControl service,
//  answers reads of Button State with the current gear, notifies gear changes and
//  button presses typed at the keyboard, and prints every App Information and
//  Haptic Feedback write it receives, decoded.
//
//  It models a bike with its own 2×12 drivetrain: it reports Chainring Set (0x04),
//  Cassette Set (0x05) and a flattened Gear Set (0x03) in one notification, as the
//  spec suggests for front/rear devices.
//
//  Run:  swift run obc-mock-device        (quit other BLE peripherals on this Mac first)
//  Keys: u / d  rear cog up / down      f  toggle chainring
//        l lap   p pause   r resume   s skip interval   b previous interval
//        + / -  increase / decrease difficulty      q quit
//
//  This is a protocol test bench, not a trainer: it has no FTMS service and no
//  power or cadence. A real bike exposes OpenBikeControl beside its trainer services.
//

#if canImport(CoreBluetooth)
import Foundation
import CoreBluetooth
import OpenBikeControl

final class MockDevice: NSObject, CBPeripheralManagerDelegate {

    let manager: CBPeripheralManager
    let service = CBMutableService(type: CBUUID(string: OpenBikeControl.serviceUUIDString), primary: true)
    let buttonState = CBMutableCharacteristic(type: CBUUID(string: OpenBikeControl.buttonStateUUIDString),
                                              properties: [.read, .notify], value: nil, permissions: [.readable])
    let haptic = CBMutableCharacteristic(type: CBUUID(string: OpenBikeControl.hapticFeedbackUUIDString),
                                         properties: [.write, .writeWithoutResponse], value: nil, permissions: [.writeable])
    let appInformation = CBMutableCharacteristic(type: CBUUID(string: OpenBikeControl.appInformationUUIDString),
                                                 properties: [.write, .writeWithoutResponse], value: nil, permissions: [.writeable])

    var front = 2, rear = 7
    let cogs = 12

    override init() {
        manager = CBPeripheralManager(delegate: nil, queue: nil)
        super.init()
        manager.delegate = self
    }

    func peripheralManagerDidUpdateState(_ p: CBPeripheralManager) {
        guard p.state == .poweredOn else {
            print("Bluetooth is not available (state \(p.state.rawValue)).")
            return
        }
        service.characteristics = [buttonState, haptic, appInformation]
        p.add(service)
        p.startAdvertising([CBAdvertisementDataLocalNameKey: "OBC Mock",
                            CBAdvertisementDataServiceUUIDsKey: [service.uuid]])
        print("Advertising as 'OBC Mock'. Gear: \(front)·\(rear). Keys: u d f l p r s b + - q")
        readKeys()
    }

    // MARK: Device → app

    /// One Button State message carrying the whole gear picture: front, rear and a
    /// flattened index (chainrings concatenated), all as 1-based positions + 1.
    func gearMessage() -> Data {
        let flat = (front - 1) * cogs + rear
        return Data([OpenBikeControl.buttonStateType,
                     OpenBikeControl.Button.chainringSet.rawValue, UInt8(front + 1),
                     OpenBikeControl.Button.cassetteSet.rawValue, UInt8(rear + 1),
                     OpenBikeControl.Button.gearSet.rawValue, UInt8(min(flat + 1, 255))])
    }

    func sendGear() {
        manager.updateValue(gearMessage(), for: buttonState, onSubscribedCentrals: nil)
        print("→ gear \(front)·\(rear)")
    }

    /// A press is two notifications: value 0x01, then 0x00 a moment later.
    func press(_ button: OpenBikeControl.Button) {
        manager.updateValue(Data([OpenBikeControl.buttonStateType, button.rawValue, 0x01]), for: buttonState, onSubscribedCentrals: nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.08) { [self] in
            manager.updateValue(Data([OpenBikeControl.buttonStateType, button.rawValue, 0x00]), for: buttonState, onSubscribedCentrals: nil)
        }
        print("→ \(button.name) pressed")
    }

    func peripheralManager(_ p: CBPeripheralManager, central: CBCentral, didSubscribeTo c: CBCharacteristic) {
        if c.uuid == buttonState.uuid {
            print("App subscribed to Button State")
            sendGear()
        }
    }

    func peripheralManager(_ p: CBPeripheralManager, central: CBCentral, didUnsubscribeFrom c: CBCharacteristic) {
        print("App unsubscribed")
    }

    func peripheralManager(_ p: CBPeripheralManager, didReceiveRead r: CBATTRequest) {
        if r.characteristic.uuid == buttonState.uuid { r.value = gearMessage() }
        p.respond(to: r, withResult: .success)
    }

    // MARK: App → device

    func peripheralManager(_ p: CBPeripheralManager, didReceiveWrite requests: [CBATTRequest]) {
        for r in requests {
            let data = r.value ?? Data()
            let hex = data.map { String(format: "%02X", $0) }.joined(separator: " ")
            switch r.characteristic.uuid {
            case appInformation.uuid:
                if let info = OpenBikeControl.AppInformation.parse(data) {
                    let names = info.buttons.map { OpenBikeControl.Button(rawValue: $0)?.name ?? String(format: "0x%02X", $0) }
                    print("← App Information [\(hex)]")
                    print("   \(info.appID) \(info.appVersion) handles: \(names.isEmpty ? "all actions" : names.joined(separator: ", "))")
                    let shifts = info.buttons.contains(OpenBikeControl.Button.shiftUp.rawValue) || info.buttons.contains(OpenBikeControl.Button.shiftDown.rawValue)
                    print("   declares Shift Up / Shift Down: \(shifts)")
                } else {
                    print("← App Information [\(hex)] — malformed")
                }
            case haptic.uuid:
                if let h = OpenBikeControl.HapticFeedback.parse(data) {
                    let pattern = OpenBikeControl.HapticPattern(rawValue: h.pattern).map { "\($0)" } ?? String(format: "0x%02X", h.pattern)
                    print("← Haptic [\(hex)] pattern \(pattern), duration \(h.durationMs == 0 ? "default" : "\(h.durationMs) ms"), intensity \(h.intensity == 0 ? "default" : "\(h.intensity)")")
                } else {
                    print("← Haptic [\(hex)] — malformed")
                }
            default:
                print("← write [\(hex)] on \(r.characteristic.uuid)")
            }
            p.respond(to: r, withResult: .success)
        }
    }

    // MARK: Keyboard

    func readKeys() {
        DispatchQueue.global().async { [weak self] in
            while let line = readLine() {
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    switch line.trimmingCharacters(in: .whitespaces) {
                    case "u": self.rear = min(self.rear + 1, self.cogs); self.sendGear()
                    case "d": self.rear = max(self.rear - 1, 1); self.sendGear()
                    case "f": self.front = self.front == 1 ? 2 : 1; self.sendGear()
                    case "l": self.press(.lap)
                    case "p": self.press(.pause)
                    case "r": self.press(.resume)
                    case "s": self.press(.skipInterval)
                    case "b": self.press(.previousInterval)
                    case "+": self.press(.increaseDifficulty)
                    case "-": self.press(.decreaseDifficulty)
                    case "q": exit(0)
                    default: print("keys: u d f l p r s b + - q")
                    }
                }
            }
        }
    }
}

let device = MockDevice()
RunLoop.main.run()

#else
print("obc-mock-device needs CoreBluetooth (macOS). The OpenBikeControl library itself builds anywhere.")
#endif
