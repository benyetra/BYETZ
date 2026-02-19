import SwiftUI

struct PlexAuthView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var plexToken = ""
    @State private var isLoading = false

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                VStack(spacing: 12) {
                    Text("BYETZ")
                        .font(.system(size: 56, weight: .bold, design: .rounded))
                        .foregroundColor(.white)

                    Text("Your Personal Clip Feed")
                        .font(.title3)
                        .foregroundColor(.gray)
                }

                VStack(spacing: 16) {
                    Text("Connect your Plex account to get started")
                        .font(.body)
                        .foregroundColor(.white.opacity(0.8))
                        .multilineTextAlignment(.center)

                    SecureField("Plex Token", text: $plexToken)
                        .textFieldStyle(.roundedBorder)
                        .padding(.horizontal, 40)

                    Button(action: authenticate) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .tint(.black)
                            }
                            Text("Connect to Plex")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.orange)
                        .foregroundColor(.black)
                        .cornerRadius(12)
                    }
                    .disabled(plexToken.isEmpty || isLoading)
                    .padding(.horizontal, 40)
                }

                if let error = authManager.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding(.horizontal)
                }

                Spacer()
                Spacer()
            }
        }
    }

    private func authenticate() {
        isLoading = true
        Task {
            await authManager.authenticateWithPlex(token: plexToken)
            isLoading = false
        }
    }
}
