// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "OpenBikeControlSwift",
    platforms: [.macOS(.v13), .iOS(.v16), .tvOS(.v16), .watchOS(.v9)],
    products: [
        // The pure codec: UUIDs, button IDs, parsing and encoding. No CoreBluetooth,
        // so it drops into any Apple-platform app unchanged.
        .library(name: "OpenBikeControl", targets: ["OpenBikeControl"]),
    ],
    targets: [
        .target(name: "OpenBikeControl"),
        // A command-line trainer app: scans, connects, declares itself, prints buttons and gear.
        .executableTarget(name: "obc-trainer-app", dependencies: ["OpenBikeControl"], path: "Sources/TrainerApp"),
        // A fake device for testing the app without hardware (macOS acts as the BLE peripheral).
        .executableTarget(name: "obc-mock-device", dependencies: ["OpenBikeControl"], path: "Sources/MockDevice"),
        .testTarget(name: "OpenBikeControlTests", dependencies: ["OpenBikeControl"]),
    ]
)
