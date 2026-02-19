import Foundation
import SwiftUI

enum AuthState: Equatable {
    case loading
    case unauthenticated
    case needsTasteProfile
    case authenticated
}

@MainActor
class AuthManager: ObservableObject {
    @Published var authState: AuthState = .loading
    @Published var currentUserId: UUID?
    @Published var username: String = ""
    @Published var errorMessage: String?

    init() {
        checkExistingAuth()
    }

    func checkExistingAuth() {
        if let token = KeychainService.shared.getToken() {
            authState = .authenticated
        } else {
            authState = .unauthenticated
        }
    }

    func authenticateWithPlex(token: String) async {
        do {
            let response = try await APIClient.shared.authenticatePlex(token: token)
            KeychainService.shared.saveToken(response.accessToken)
            KeychainService.shared.savePlexToken(token)
            currentUserId = response.userId
            username = response.username
            authState = .needsTasteProfile
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func completeTasteProfile() {
        authState = .authenticated
    }

    func logout() {
        KeychainService.shared.clearAll()
        currentUserId = nil
        username = ""
        authState = .unauthenticated
    }
}
