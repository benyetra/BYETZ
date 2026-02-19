import Foundation

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var profile: UserProfile?
    @Published var savedClips: [Clip] = []
    @Published var isLoading = false

    func loadProfile() async {
        isLoading = true
        do {
            async let profileRequest = APIClient.shared.getProfile()
            async let savedRequest = APIClient.shared.getSavedClips()

            profile = try await profileRequest
            savedClips = try await savedRequest
        } catch {
            print("Failed to load profile: \(error)")
        }
        isLoading = false
    }
}
