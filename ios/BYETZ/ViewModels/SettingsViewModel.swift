import Foundation
import Combine

@MainActor
class SettingsViewModel: ObservableObject {
    @Published var subtitleOverlay: Bool = false {
        didSet { saveSettingsDebounced() }
    }
    @Published var clipQuality: String = "1080p" {
        didSet { saveSettingsDebounced() }
    }
    @Published var contentMaturityFilter: String = "all"
    @Published var notificationsEnabled: Bool = true {
        didSet { saveSettingsDebounced() }
    }

    private var saveTask: Task<Void, Never>?

    func loadSettings() async {
        do {
            let settings = try await APIClient.shared.getSettings()
            subtitleOverlay = settings.subtitleOverlay
            clipQuality = settings.clipQuality
            contentMaturityFilter = settings.contentMaturityFilter
            notificationsEnabled = settings.notificationsEnabled
        } catch {
            print("Failed to load settings: \(error)")
        }
    }

    private func saveSettingsDebounced() {
        saveTask?.cancel()
        saveTask = Task {
            try? await Task.sleep(nanoseconds: 500_000_000)
            guard !Task.isCancelled else { return }

            let settings = UserSettings(
                subtitleOverlay: subtitleOverlay,
                contentMaturityFilter: contentMaturityFilter,
                clipQuality: clipQuality,
                notificationsEnabled: notificationsEnabled
            )
            do {
                _ = try await APIClient.shared.updateSettings(settings)
            } catch {
                print("Failed to save settings: \(error)")
            }
        }
    }
}
