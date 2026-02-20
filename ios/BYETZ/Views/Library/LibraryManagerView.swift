import SwiftUI

struct LibraryManagerView: View {
    @StateObject private var viewModel = LibraryViewModel()

    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 20) {
                        // Server status
                        HStack {
                            Circle()
                                .fill(viewModel.status?.serverReachable == true ? Color.green : Color.red)
                                .frame(width: 10, height: 10)
                            Text(viewModel.status?.serverName ?? "No Server")
                                .foregroundColor(.white)
                            Spacer()
                        }
                        .padding()
                        .background(Color.gray.opacity(0.15))
                        .cornerRadius(12)
                        .padding(.horizontal)

                        if !viewModel.hasLibraries {
                            // No libraries discovered yet
                            VStack(spacing: 16) {
                                Image(systemName: "magnifyingglass")
                                    .font(.system(size: 40))
                                    .foregroundColor(.gray)
                                Text("No libraries found")
                                    .font(.title3)
                                    .foregroundColor(.gray)
                                Text("Discover your Plex libraries to get started")
                                    .font(.caption)
                                    .foregroundColor(.gray.opacity(0.7))

                                Button(action: {
                                    Task { await viewModel.discoverLibraries() }
                                }) {
                                    HStack {
                                        if viewModel.isDiscovering {
                                            ProgressView()
                                                .tint(.black)
                                        } else {
                                            Image(systemName: "antenna.radiowaves.left.and.right")
                                        }
                                        Text(viewModel.isDiscovering ? "Discovering..." : "Discover Libraries")
                                    }
                                    .fontWeight(.semibold)
                                    .padding(.horizontal, 24)
                                    .padding(.vertical, 12)
                                    .background(Color.orange)
                                    .foregroundColor(.black)
                                    .cornerRadius(12)
                                }
                                .disabled(viewModel.isDiscovering)
                            }
                            .padding(.top, 40)
                        } else {
                            // Libraries list with toggles
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Select Libraries")
                                    .font(.headline)
                                    .foregroundColor(.white)
                                Text("Disable 4K/UHD libraries to avoid duplicate processing")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal)

                            ForEach(viewModel.status?.libraries ?? []) { library in
                                LibraryRow(library: library) { enabled in
                                    Task { await viewModel.toggleLibrary(id: library.id, enabled: enabled) }
                                }
                            }

                            // Action buttons
                            VStack(spacing: 12) {
                                Button(action: {
                                    Task { await viewModel.processLibraries() }
                                }) {
                                    HStack {
                                        if viewModel.isProcessing {
                                            ProgressView()
                                                .tint(.black)
                                        } else {
                                            Image(systemName: "play.fill")
                                        }
                                        Text(viewModel.isProcessing ? "Processing..." : "Start Processing (\(viewModel.enabledCount) libraries)")
                                    }
                                    .fontWeight(.semibold)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 14)
                                    .background(viewModel.enabledCount > 0 ? Color.orange : Color.gray)
                                    .foregroundColor(.black)
                                    .cornerRadius(12)
                                }
                                .disabled(viewModel.enabledCount == 0 || viewModel.isProcessing)

                                Button(action: {
                                    Task { await viewModel.discoverLibraries() }
                                }) {
                                    HStack {
                                        Image(systemName: "arrow.triangle.2.circlepath")
                                        Text("Re-discover Libraries")
                                    }
                                    .font(.subheadline)
                                    .foregroundColor(.orange)
                                }
                            }
                            .padding(.horizontal)
                            .padding(.top, 8)
                        }
                    }
                    .padding(.top)
                }
            }
            .navigationTitle("Library")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
        .task {
            await viewModel.loadStatus()
        }
    }
}

struct LibraryRow: View {
    let library: LibraryDetail
    let onToggle: (Bool) -> Void

    private var is4K: Bool {
        let upper = library.libraryTitle.uppercased()
        return upper.contains("4K") || upper.contains("UHD") || upper.contains("2160")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: library.libraryType == "movie" ? "film" : "tv")
                    .foregroundColor(.orange)

                VStack(alignment: .leading) {
                    HStack(spacing: 6) {
                        Text(library.libraryTitle)
                            .foregroundColor(.white)
                            .font(.headline)
                        if is4K {
                            Text("4K")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.6))
                                .foregroundColor(.white)
                                .cornerRadius(4)
                        }
                    }
                    Text("\(library.processedItems)/\(library.totalItems) processed")
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                Spacer()

                Toggle("", isOn: Binding(
                    get: { library.enabled },
                    set: { onToggle($0) }
                ))
                .tint(.orange)
            }

            if library.totalItems > 0 {
                ProgressView(value: library.processingPercentage, total: 100)
                    .tint(.orange)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}
