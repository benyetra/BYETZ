import Foundation

@MainActor
class LibraryViewModel: ObservableObject {
    @Published var status: LibraryStatus?
    @Published var isLoading = false
    @Published var isDiscovering = false
    @Published var isProcessing = false

    var hasLibraries: Bool {
        !(status?.libraries ?? []).isEmpty
    }

    var enabledCount: Int {
        (status?.libraries ?? []).filter(\.enabled).count
    }

    func loadStatus() async {
        isLoading = true
        do {
            status = try await APIClient.shared.getLibraryStatus()
        } catch {
            print("Failed to load library status: \(error)")
        }
        isLoading = false
    }

    func discoverLibraries() async {
        isDiscovering = true
        do {
            try await APIClient.shared.discoverLibraries()
            // Poll for results
            try await Task.sleep(for: .seconds(3))
            await loadStatus()
        } catch {
            print("Failed to discover libraries: \(error)")
        }
        isDiscovering = false
    }

    func processLibraries() async {
        isProcessing = true
        do {
            try await APIClient.shared.processLibraries()
        } catch {
            print("Failed to start processing: \(error)")
        }
        isProcessing = false
    }

    func triggerRescan() async {
        do {
            try await APIClient.shared.triggerRescan()
        } catch {
            print("Failed to trigger rescan: \(error)")
        }
    }

    func toggleLibrary(id: UUID, enabled: Bool) async {
        struct ToggleBody: Encodable {
            let library_id: UUID
            let enabled: Bool
        }
        do {
            let _: [String: String] = try await APIClient.shared.request(
                "/library/toggle",
                method: "PUT",
                body: ToggleBody(library_id: id, enabled: enabled)
            )
            await loadStatus()
        } catch {
            print("Failed to toggle library: \(error)")
        }
    }
}
