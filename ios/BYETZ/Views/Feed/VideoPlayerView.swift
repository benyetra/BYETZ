import SwiftUI
import AVKit

struct VideoPlayerView: UIViewControllerRepresentable {
    let clip: Clip
    @ObservedObject var viewModel: FeedViewModel

    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.showsPlaybackControls = false
        controller.videoGravity = .resizeAspectFill

        if let url = APIClient.shared.streamURLSync(clipId: clip.id) {
            let player = AVPlayer(url: url)
            controller.player = player
            player.play()
        }

        return controller
    }

    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) {
        // Update player when clip changes
    }
}

extension APIClient {
    nonisolated func streamURLSync(clipId: UUID) -> URL? {
        let baseURL = "http://localhost:8000"
        return URL(string: "\(baseURL)/clips/\(clipId.uuidString)/stream")
    }
}
