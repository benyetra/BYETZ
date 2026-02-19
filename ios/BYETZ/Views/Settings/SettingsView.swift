import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = SettingsViewModel()

    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()

                Form {
                    Section("Plex Connection") {
                        HStack {
                            Text("Server")
                            Spacer()
                            Text("Connected")
                                .foregroundColor(.green)
                        }
                    }

                    Section("Clip Preferences") {
                        Toggle("Subtitle Overlay", isOn: $viewModel.subtitleOverlay)

                        Picker("Video Quality", selection: $viewModel.clipQuality) {
                            Text("1080p").tag("1080p")
                            Text("720p").tag("720p")
                        }
                    }

                    Section("Notifications") {
                        Toggle("Enable Notifications", isOn: $viewModel.notificationsEnabled)
                    }

                    Section {
                        Button("Sign Out", role: .destructive) {
                            authManager.logout()
                        }
                    }
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
        .task {
            await viewModel.loadSettings()
        }
    }
}
