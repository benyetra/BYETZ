import Foundation
import AVFoundation
import Combine

@MainActor
class FeedViewModel: ObservableObject {
    @Published var clips: [Clip] = []
    @Published var currentIndex: Int = 0
    @Published var isLoading = false
    @Published var isPlaying = true
    @Published var playbackProgress: Double = 0.0

    private var likedClipIds: Set<UUID> = []
    private var savedClipIds: Set<UUID> = []
    private let sessionId = UUID()
    private var player: AVPlayer?
    private var timeObserver: Any?

    var currentClip: Clip? {
        guard currentIndex >= 0 && currentIndex < clips.count else { return nil }
        return clips[currentIndex]
    }

    func loadFeed() async {
        guard !isLoading else { return }
        isLoading = true

        do {
            let response = try await APIClient.shared.getFeed(limit: 20, offset: clips.count)
            clips.append(contentsOf: response.clips)
        } catch {
            print("Failed to load feed: \(error)")
        }

        isLoading = false
    }

    func nextClip() {
        guard currentIndex < clips.count - 1 else {
            Task { await loadFeed() }
            return
        }
        currentIndex += 1
        playbackProgress = 0

        if currentIndex >= clips.count - 5 {
            Task { await loadFeed() }
        }
    }

    func previousClip() {
        guard currentIndex > 0 else { return }
        currentIndex -= 1
        playbackProgress = 0
    }

    func togglePlayback() {
        isPlaying.toggle()
    }

    func likeClip(_ clip: Clip) {
        HapticManager.shared.like()
        likedClipIds.insert(clip.id)
        submitInteraction(clipId: clip.id, action: .like)
    }

    func dislikeClip(_ clip: Clip) {
        HapticManager.shared.dislike()
        submitInteraction(clipId: clip.id, action: .dislike)
        nextClip()
    }

    func saveClip(_ clip: Clip) {
        HapticManager.shared.save()
        savedClipIds.insert(clip.id)
        submitInteraction(clipId: clip.id, action: .save)
    }

    func isLiked(_ clip: Clip) -> Bool {
        likedClipIds.contains(clip.id)
    }

    func isSaved(_ clip: Clip) -> Bool {
        savedClipIds.contains(clip.id)
    }

    private func submitInteraction(clipId: UUID, action: ActionType) {
        Task {
            let interaction = InteractionRequest(
                clipId: clipId,
                action: action,
                watchDurationMs: nil,
                sessionId: sessionId
            )
            do {
                _ = try await APIClient.shared.submitInteraction(interaction)
            } catch {
                print("Failed to submit interaction: \(error)")
            }
        }
    }
}
