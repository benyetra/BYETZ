import SwiftUI
import AVKit

struct FeedView: View {
    @StateObject private var viewModel = FeedViewModel()
    @State private var showInfoPanel = false
    @State private var showOverlay = false

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.black.ignoresSafeArea()

                if viewModel.clips.isEmpty && viewModel.isLoading {
                    ProgressView()
                        .tint(.white)
                } else if let currentClip = viewModel.currentClip {
                    // Video player
                    VideoPlayerView(clip: currentClip, viewModel: viewModel)
                        .ignoresSafeArea()
                        .gesture(
                            DragGesture(minimumDistance: 50)
                                .onEnded { value in
                                    if value.translation.height < -50 {
                                        viewModel.nextClip()
                                    } else if value.translation.height > 50 {
                                        viewModel.previousClip()
                                    } else if value.translation.width < -50 {
                                        showInfoPanel = true
                                    } else if value.translation.width > 50 {
                                        showInfoPanel = false
                                    }
                                }
                        )
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                showOverlay.toggle()
                            }
                            viewModel.togglePlayback()
                        }

                    // Engagement buttons (right side)
                    VStack(spacing: 20) {
                        Spacer()

                        EngagementButton(
                            icon: "heart.fill",
                            isActive: viewModel.isLiked(currentClip),
                            color: .red
                        ) {
                            viewModel.likeClip(currentClip)
                        }

                        EngagementButton(
                            icon: "xmark.circle.fill",
                            isActive: false,
                            color: .white
                        ) {
                            viewModel.dislikeClip(currentClip)
                        }

                        EngagementButton(
                            icon: "bookmark.fill",
                            isActive: viewModel.isSaved(currentClip),
                            color: .yellow
                        ) {
                            viewModel.saveClip(currentClip)
                        }

                        Spacer()
                    }
                    .padding(.trailing, 16)
                    .frame(maxWidth: .infinity, alignment: .trailing)

                    // Progress bar (bottom)
                    VStack {
                        Spacer()
                        ProgressView(value: viewModel.playbackProgress)
                            .tint(.white.opacity(0.7))
                            .frame(height: 2)
                            .padding(.horizontal, 8)
                            .padding(.bottom, 4)
                    }

                    // Metadata overlay (on tap)
                    if showOverlay {
                        ClipOverlayView(clip: currentClip)
                            .transition(.opacity)
                    }

                    // Info panel (swipe left)
                    if showInfoPanel {
                        ClipInfoPanel(clip: currentClip, isShowing: $showInfoPanel)
                            .transition(.move(edge: .trailing))
                    }
                } else {
                    VStack(spacing: 16) {
                        Image(systemName: "film.stack")
                            .font(.system(size: 48))
                            .foregroundColor(.gray)
                        Text("No clips available")
                            .foregroundColor(.gray)
                        Text("Process your library to generate clips")
                            .font(.caption)
                            .foregroundColor(.gray.opacity(0.7))
                    }
                }
            }
        }
        .onAppear {
            OrientationManager.shared.lockLandscape()
        }
        .onDisappear {
            OrientationManager.shared.unlockOrientation()
        }
        .task {
            await viewModel.loadFeed()
        }
    }
}

struct EngagementButton: View {
    let icon: String
    let isActive: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(isActive ? color : .white.opacity(0.7))
                .frame(width: 44, height: 44)
                .background(Color.black.opacity(0.3))
                .clipShape(Circle())
        }
    }
}

struct ClipOverlayView: View {
    let clip: Clip

    var body: some View {
        VStack {
            Spacer()
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(clip.title)
                        .font(.headline)
                        .foregroundColor(.white)

                    if let seasonEp = clip.seasonEpisode {
                        Text(seasonEp)
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.8))
                    }

                    Text(clip.genreTags.joined(separator: " · "))
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.6))
                }
                .padding()
                .background(
                    LinearGradient(
                        colors: [.clear, .black.opacity(0.7)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                Spacer()
            }
        }
        .allowsHitTesting(false)
    }
}

struct ClipInfoPanel: View {
    let clip: Clip
    @Binding var isShowing: Bool

    var body: some View {
        HStack {
            Spacer()
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("Clip Info")
                        .font(.headline)
                        .foregroundColor(.white)
                    Spacer()
                    Button(action: { isShowing = false }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.gray)
                    }
                }

                InfoRow(label: "Title", value: clip.title)

                if let se = clip.seasonEpisode {
                    InfoRow(label: "Episode", value: se)
                }

                InfoRow(label: "Duration", value: "\(clip.durationMs / 1000)s")

                if !clip.actors.isEmpty {
                    InfoRow(label: "Cast", value: clip.actors.prefix(3).joined(separator: ", "))
                }

                if let director = clip.director {
                    InfoRow(label: "Director", value: director)
                }

                InfoRow(label: "Genres", value: clip.genreTags.joined(separator: ", "))

                Spacer()
            }
            .padding()
            .frame(width: 280)
            .background(Color.black.opacity(0.9))
        }
    }
}

struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption)
                .foregroundColor(.gray)
            Text(value)
                .font(.subheadline)
                .foregroundColor(.white)
        }
    }
}
