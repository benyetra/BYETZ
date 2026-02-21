import SwiftUI
import AVKit

struct VideoPlayerView: UIViewControllerRepresentable {
    let clip: Clip
    @ObservedObject var viewModel: FeedViewModel

    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.showsPlaybackControls = false
        controller.videoGravity = .resizeAspectFill

        if let url = streamURL(for: clip) {
            let player = AVPlayer(url: url)
            controller.player = player
            player.play()

            // Loop playback
            NotificationCenter.default.addObserver(
                forName: .AVPlayerItemDidPlayToEndTime,
                object: player.currentItem,
                queue: .main
            ) { _ in
                player.seek(to: .zero)
                player.play()
            }
        }

        return controller
    }

    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) {
        guard let url = streamURL(for: clip) else { return }

        // Only replace player if the clip changed
        if let currentURL = (controller.player?.currentItem?.asset as? AVURLAsset)?.url,
           currentURL == url {
            return
        }

        let player = AVPlayer(url: url)
        controller.player = player
        player.play()
    }

    private func streamURL(for clip: Clip) -> URL? {
        let baseURL = "http://192.168.1.9:8101"
        var urlString = "\(baseURL)/clips/\(clip.id.uuidString)/stream"
        if let token = KeychainService.shared.getToken() {
            urlString += "?token=\(token)"
        }
        return URL(string: urlString)
    }
}
