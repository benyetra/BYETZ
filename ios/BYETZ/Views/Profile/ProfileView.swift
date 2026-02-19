import SwiftUI

struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()

    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 24) {
                        // Avatar and username
                        VStack(spacing: 12) {
                            Circle()
                                .fill(Color.orange.opacity(0.3))
                                .frame(width: 80, height: 80)
                                .overlay(
                                    Image(systemName: "person.fill")
                                        .font(.title)
                                        .foregroundColor(.orange)
                                )

                            Text(viewModel.profile?.plexUsername ?? "User")
                                .font(.title3.bold())
                                .foregroundColor(.white)
                        }
                        .padding(.top)

                        // Stats
                        HStack(spacing: 32) {
                            StatItem(value: viewModel.profile?.totalClipsWatched ?? 0, label: "Watched")
                            StatItem(value: viewModel.profile?.totalLikes ?? 0, label: "Likes")
                            StatItem(value: viewModel.profile?.totalSaves ?? 0, label: "Saved")
                        }

                        // Saved clips grid
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Saved Clips")
                                .font(.headline)
                                .foregroundColor(.white)
                                .padding(.horizontal)

                            if viewModel.savedClips.isEmpty {
                                Text("No saved clips yet")
                                    .foregroundColor(.gray)
                                    .padding()
                            } else {
                                LazyVGrid(columns: [GridItem(.adaptive(minimum: 160))], spacing: 8) {
                                    ForEach(viewModel.savedClips) { clip in
                                        SavedClipCard(clip: clip)
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
        .task {
            await viewModel.loadProfile()
        }
    }
}

struct StatItem: View {
    let value: Int
    let label: String

    var body: some View {
        VStack(spacing: 4) {
            Text("\(value)")
                .font(.title2.bold())
                .foregroundColor(.orange)
            Text(label)
                .font(.caption)
                .foregroundColor(.gray)
        }
    }
}

struct SavedClipCard: View {
    let clip: Clip

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.2))
                .aspectRatio(16/9, contentMode: .fit)
                .overlay(
                    Image(systemName: "play.fill")
                        .foregroundColor(.white.opacity(0.7))
                )

            Text(clip.title)
                .font(.caption)
                .foregroundColor(.white)
                .lineLimit(1)

            Text("\(clip.durationMs / 1000)s")
                .font(.caption2)
                .foregroundColor(.gray)
        }
    }
}
