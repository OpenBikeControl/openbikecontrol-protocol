//
//  obc-trainer-app — a command-line "trainer app" that talks OpenBikeControl over BLE.
//
//  What it shows:
//    1. Discovery: scan for the OpenBikeControl service UUID.
//    2. Connection: connect, discover the service and its three characteristics.
//    3. App Information: declare who we are and which actions we handle, right after connecting.
//    4. Button State: read the current value, subscribe to notifications, decode every pair.
//    5. Gear display: keep the reported gear (front·rear or flat) up to date.
//    6. Haptic Feedback: send a short pulse when the rider presses Lap, or from the keyboard.
//
//  Run:  swift run obc-trainer-app            (macOS asks to allow Bluetooth for your terminal once)
//        swift run obc-trainer-app "SB200"    (optional: only connect to a device whose name contains this)
//  Keys: h = short haptic   s = success haptic   e = stop haptic   q = quit
//
//  Test without hardware: run `swift run obc-mock-device` in another terminal first.
//
//  Integration note for a real trainer app: a smart bike such as the Stages SB200
//  exposes this service on the SAME peripheral as its FTMS trainer service. In that
//  case you do not scan for it or open a second connection — you discover the
//  OpenBikeControl service on the trainer you are already connected to, and only
//  subscribe when it is present. Trainer control (FTMS / proprietary) is unchanged.
//

#if canImport(CoreBluetooth)
import Foundation
import CoreBluetooth
import OpenBikeControl

final class TrainerApp: NSObject, CBCentralManagerDelegate, CBPeripheralDelegate {

    // The actions this app handles. The device uses this list to choose its button
    // mapping. We leave gearing to the bike and display what it reports, so the
    // gear-set IDs are declared and Shift Up / Shift Down are not. An app that
    // implements virtual shifting itself would declare .shiftUp and .shiftDown too.
    static let declaredButtons: [OpenBikeControl.Button] = [
        .gearSet, .chainringSet, .cassetteSet,
        .pause, .resume, .lap, .skipInterval, .previousInterval,
        .increaseDifficulty, .decreaseDifficulty,
    ]

    let serviceUUID        = CBUUID(string: OpenBikeControl.serviceUUIDString)
    let buttonStateUUID    = CBUUID(string: OpenBikeControl.buttonStateUUIDString)
    let hapticUUID         = CBUUID(string: OpenBikeControl.hapticFeedbackUUIDString)
    let appInformationUUID = CBUUID(string: OpenBikeControl.appInformationUUIDString)

    let nameFilter: String?
    var central: CBCentralManager!
    var peripheral: CBPeripheral?
    var hapticCharacteristic: CBCharacteristic?
    var gear = OpenBikeControl.Gear()

    init(nameFilter: String?) {
        self.nameFilter = nameFilter
        super.init()
        central = CBCentralManager(delegate: self, queue: nil)
    }

    // MARK: Discovery

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        guard central.state == .poweredOn else {
            print("Bluetooth is not available (state \(central.state.rawValue)).")
            return
        }
        scan()
    }

    func scan() {
        print("Scanning for OpenBikeControl devices…")
        central.scanForPeripherals(withServices: [serviceUUID], options: nil)
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        let name = peripheral.name ?? (advertisementData[CBAdvertisementDataLocalNameKey] as? String) ?? "(unnamed)"
        if let filter = nameFilter, !name.localizedCaseInsensitiveContains(filter) {
            print("  skipping \(name)")
            return
        }
        print("Found \(name) (RSSI \(RSSI)) — connecting")
        central.stopScan()
        self.peripheral = peripheral
        peripheral.delegate = self
        central.connect(peripheral, options: nil)
    }

    // MARK: Connection

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("Connected to \(peripheral.name ?? "device"); discovering the OpenBikeControl service")
        peripheral.discoverServices([serviceUUID])
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        print("Connection failed: \(error?.localizedDescription ?? "unknown error")")
        scan()
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        // Everything learned from the device is forgotten on disconnect — the gear
        // display must not show a stale value from the last session.
        print("Disconnected\(error.map { ": \($0.localizedDescription)" } ?? "")")
        self.peripheral = nil
        hapticCharacteristic = nil
        gear = OpenBikeControl.Gear()
        scan()
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let service = peripheral.services?.first(where: { $0.uuid == serviceUUID }) else {
            print("The device has no OpenBikeControl service.")
            return
        }
        peripheral.discoverCharacteristics([buttonStateUUID, hapticUUID, appInformationUUID], for: service)
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        for c in service.characteristics ?? [] {
            switch c.uuid {
            case appInformationUUID:
                // BLE.md: apps SHOULD send this immediately after connecting.
                let info = OpenBikeControl.AppInformation(appID: "swift-example", appVersion: "1.0.0",
                                                          buttons: Self.declaredButtons)
                let type: CBCharacteristicWriteType = c.properties.contains(.write) ? .withResponse : .withoutResponse
                peripheral.writeValue(info.encoded, for: c, type: type)
                print("Sent App Information: \(info.appID) \(info.appVersion), \(info.buttons.count) actions")
            case buttonStateUUID:
                // The characteristic is readable: the first read gives the device's current
                // state (a bike reports its gear here), then notifications carry changes.
                peripheral.readValue(for: c)
                peripheral.setNotifyValue(true, for: c)
            case hapticUUID:
                hapticCharacteristic = c
            default:
                break
            }
        }
    }

    // MARK: Button State

    func peripheral(_ peripheral: CBPeripheral, didUpdateNotificationStateFor characteristic: CBCharacteristic, error: Error?) {
        if characteristic.uuid == buttonStateUUID {
            print(error == nil ? "Subscribed to Button State. Waiting for input…" : "Subscribe failed: \(error!.localizedDescription)")
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard characteristic.uuid == buttonStateUUID, let data = characteristic.value else { return }
        let hex = data.map { String(format: "%02X", $0) }.joined(separator: " ")
        guard let events = OpenBikeControl.parseButtonState(data) else {
            print("← [\(hex)] not a Button State message")
            return
        }
        for e in events {
            print("← [\(hex)] \(e.description)")
            // Map presses to the app's actions here. We only demonstrate one:
            if e.isPress, e.button == .lap { sendHaptic(.short) }
        }
        if gear.apply(events), let text = gear.displayText {
            print("   Gear: \(text)")
        }
    }

    // MARK: Haptic Feedback

    func sendHaptic(_ pattern: OpenBikeControl.HapticPattern, durationMs: Int = 0, intensity: UInt8 = 0) {
        guard let p = peripheral, let c = hapticCharacteristic else {
            print("No haptic characteristic on this device.")
            return
        }
        let data = OpenBikeControl.hapticFeedback(pattern: pattern, durationMs: durationMs, intensity: intensity)
        let type: CBCharacteristicWriteType = c.properties.contains(.writeWithoutResponse) ? .withoutResponse : .withResponse
        p.writeValue(data, for: c, type: type)
        print("→ haptic \(pattern)")
    }

    func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error { print("Write to \(characteristic.uuid) failed: \(error.localizedDescription)") }
    }

    // MARK: Keyboard

    func readKeys() {
        DispatchQueue.global().async { [weak self] in
            while let line = readLine() {
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    switch line.trimmingCharacters(in: .whitespaces) {
                    case "h": self.sendHaptic(.short)
                    case "s": self.sendHaptic(.success, intensity: 0xFF)
                    case "e": self.sendHaptic(.none)
                    case "q": exit(0)
                    default: print("keys: h = short haptic, s = success haptic, e = stop, q = quit")
                    }
                }
            }
        }
    }
}

let app = TrainerApp(nameFilter: CommandLine.arguments.dropFirst().first)
app.readKeys()
RunLoop.main.run()

#else
print("obc-trainer-app needs CoreBluetooth (macOS). The OpenBikeControl library itself builds anywhere.")
#endif
