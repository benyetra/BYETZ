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
                            Button("Rescan") {
                                Task { await viewModel.triggerRescan() }
                            }
                            .buttonStyle(.bordered)
                            .tint(.orange)
                        }
                        .padding()
                        .background(Color.gray.opacity(0.15))
                        .cornerRadius(12)
                        .padding(.horizontal)

                        // Libraries
                        ForEach(viewModel.status?.libraries ?? []) { library in
                            LibraryRow(library: library) { enabled in
                                Task { await viewModel.toggleLibrary(id: library.id, enabled: enabled) }
                            }
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

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: library.libraryType == "movie" ? "film" : "tv")
                    .foregroundColor(.orange)

                VStack(alignment: .leading) {
                    Text(library.libraryTitle)
                        .foregroundColor(.white)
                        .font(.headline)
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

            ProgressView(value: library.processingPercentage, total: 100)
                .tint(.orange)
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}
