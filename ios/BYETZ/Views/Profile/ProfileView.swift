import SwiftUI
import AVKit

struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()
    @State private var selectedClip: Clip?

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
                                            .onTapGesture {
                                                selectedClip = clip
                                            }
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
            .fullScreenCover(item: $selectedClip) { clip in
                ClipPlayerView(clip: clip)
            }
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
            ZStack {
                // Thumbnail
                if let url = thumbnailURL {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .success(let image):
                            image
                                .resizable()
                                .aspectRatio(16/9, contentMode: .fill)
                        case .failure:
                            thumbnailPlaceholder
                        default:
                            thumbnailPlaceholder
                                .overlay(ProgressView().tint(.white))
                        }
                    }
                    .frame(height: 90)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    thumbnailPlaceholder
                }

                // Play icon overlay
                Image(systemName: "play.circle.fill")
                    .font(.title)
                    .foregroundColor(.white.opacity(0.85))
                    .shadow(color: .black.opacity(0.5), radius: 4)
            }

            Text(clip.title)
                .font(.caption)
                .foregroundColor(.white)
                .lineLimit(1)

            Text("\(clip.durationMs / 1000)s")
                .font(.caption2)
                .foregroundColor(.gray)
        }
    }

    private var thumbnailURL: URL? {
        guard let token = KeychainService.shared.getToken() else { return nil }
        let base = "http://192.168.1.9:8101"
        return URL(string: "\(base)/clips/\(clip.id.uuidString)/thumbnail?token=\(token)")
    }

    private var thumbnailPlaceholder: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(Color.gray.opacity(0.2))
            .aspectRatio(16/9, contentMode: .fit)
    }
}

/// Full-screen player for a single clip from the profile
struct ClipPlayerView: View {
    let clip: Clip
    @Environment(\.dismiss) private var dismiss
    @State private var isPlaying = true

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VideoPlayerView(clip: clip, isPlaying: isPlaying)
                .ignoresSafeArea()
                .onTapGesture {
                    isPlaying.toggle()
                }

            // Close button
            VStack {
                HStack {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title)
                            .foregroundColor(.white.opacity(0.8))
                            .shadow(color: .black.opacity(0.5), radius: 4)
                    }
                    .padding(.leading, 16)
                    .padding(.top, 8)
                    Spacer()
                }
                Spacer()
            }

            // Clip info at bottom
            VStack {
                Spacer()
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(clip.title)
                            .font(.headline)
                            .foregroundColor(.white)
                        if let se = clip.seasonEpisode {
                            Text(se)
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.8))
                        }
                    }
                    Spacer()
                }
                .padding()
                .background(
                    LinearGradient(
                        colors: [.clear, .black.opacity(0.7)],
                        startPoint: .top, endPoint: .bottom
                    )
                )
            }
            .allowsHitTesting(false)
        }
    }
}
