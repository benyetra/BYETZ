import UIKit

class HapticManager {
    static let shared = HapticManager()

    private let impactLight = UIImpactFeedbackGenerator(style: .light)
    private let impactMedium = UIImpactFeedbackGenerator(style: .medium)
    private let notificationGenerator = UINotificationFeedbackGenerator()

    func like() {
        impactMedium.impactOccurred()
    }

    func dislike() {
        impactLight.impactOccurred()
    }

    func save() {
        notificationGenerator.notificationOccurred(.success)
    }

    func tap() {
        impactLight.impactOccurred()
    }
}
