// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "BYETZ",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "BYETZ", targets: ["BYETZ"]),
    ],
    targets: [
        .target(
            name: "BYETZ",
            path: "."
        ),
    ]
)
