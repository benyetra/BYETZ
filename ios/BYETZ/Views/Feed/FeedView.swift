import SwiftUI
import AVKit

struct FeedView: View {
    @StateObject private var viewModel = FeedViewModel()
    @State private var showInfoPanel = false
    @State private var showPauseIcon = false

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.black.ignoresSafeArea()

                if viewModel.clips.isEmpty && viewModel.isLoading {
                    ProgressView()
                        .tint(.white)
                } else if let currentClip = viewModel.currentClip {
                    // Video player
                    VideoPlayerView(clip: currentClip, isPlaying: viewModel.isPlaying)
                        .ignoresSafeArea()
                        .gesture(
                            DragGesture(minimumDistance: 50)
                                .onEnded { value in
                                    if value.translation.height < -50 {
                                        viewModel.nextClip()
                                    } else if value.translation.height > 50 {
                                        viewModel.previousClip()
                                    } else if value.translation.width < -50 {
                                        withAnimation(.easeInOut(duration: 0.25)) {
                                            showInfoPanel = true
                                        }
                                    } else if value.translation.width > 50 {
                                        withAnimation(.easeInOut(duration: 0.25)) {
                                            showInfoPanel = false
                                        }
                                    }
                                }
                        )
                        .onTapGesture {
                            viewModel.togglePlayback()
                            // Show play/pause indicator briefly
                            withAnimation(.easeIn(duration: 0.1)) {
                                showPauseIcon = true
                            }
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                                withAnimation(.easeOut(duration: 0.3)) {
                                    showPauseIcon = false
                                }
                            }
                        }

                    // Play/pause indicator (center)
                    if showPauseIcon {
                        Image(systemName: viewModel.isPlaying ? "play.fill" : "pause.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.white.opacity(0.8))
                            .shadow(color: .black.opacity(0.5), radius: 10)
                            .transition(.opacity)
                            .allowsHitTesting(false)
                    }

                    // Metadata scrim (always visible, full-width gradient)
                    ClipOverlayView(clip: currentClip)

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

                    // Progress bar (above tab bar)
                    VStack {
                        Spacer()
                        ProgressView(value: viewModel.playbackProgress)
                            .tint(.white.opacity(0.5))
                            .frame(height: 2)
                            .padding(.horizontal, 8)
                    }
                    .padding(.bottom, 50)

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
                            .font(.title3)
                            .foregroundColor(.gray)
                        Text("Go to Library tab to select and process your Plex libraries")
                            .font(.caption)
                            .foregroundColor(.gray.opacity(0.7))
                            .multilineTextAlignment(.center)
                    }
                }
            }
        }
        .toolbarBackground(.hidden, for: .tabBar)
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
        GeometryReader { geo in
            VStack {
                Spacer()
                ZStack(alignment: .bottomLeading) {
                    // Full-width gradient extending into safe area
                    LinearGradient(
                        stops: [
                            .init(color: .clear, location: 0),
                            .init(color: .black.opacity(0.03), location: 0.2),
                            .init(color: .black.opacity(0.1), location: 0.35),
                            .init(color: .black.opacity(0.25), location: 0.5),
                            .init(color: .black.opacity(0.45), location: 0.65),
                            .init(color: .black.opacity(0.6), location: 0.78),
                            .init(color: .black.opacity(0.75), location: 0.9),
                            .init(color: .black.opacity(0.85), location: 1.0),
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                    .frame(height: geo.size.height * 0.45)

                    // Text content — positioned above tab bar
                    VStack(alignment: .leading, spacing: 3) {
                        Text(clip.title)
                            .font(.headline)
                            .foregroundColor(.white)
                            .shadow(color: .black.opacity(0.5), radius: 2, x: 0, y: 1)

                        if let seasonEp = clip.seasonEpisode {
                            Text(seasonEp)
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.85))
                        }

                        if !clip.genreTags.isEmpty {
                            Text(clip.genreTags.joined(separator: " \u{00B7} "))
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.65))
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, geo.safeAreaInsets.bottom + 54)
                }
            }
            .ignoresSafeArea()
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
                    Button(action: {
                        withAnimation(.easeInOut(duration: 0.25)) {
                            isShowing = false
                        }
                    }) {
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
