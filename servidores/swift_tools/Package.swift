// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "SwiftTools",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "SwiftTools", targets: ["SwiftTools"]) 
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-nio.git", from: "2.61.0"),
        .package(url: "https://github.com/krzyzanowskim/CryptoSwift.git", from: "1.8.0")
    ],
    targets: [
        .executableTarget(
            name: "SwiftTools",
            dependencies: [
                .product(name: "NIO", package: "swift-nio"),
                .product(name: "NIOHTTP1", package: "swift-nio"),
                .product(name: "CryptoSwift", package: "CryptoSwift")
            ]
        )
    ]
)
