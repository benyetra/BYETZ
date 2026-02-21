import SwiftUI
import AVKit

struct VideoPlayerView: UIViewControllerRepresentable {
    let clip: Clip
    let isPlaying: Bool

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
        guard let player = controller.player else { return }
        guard let url = streamURL(for: clip) else { return }

        // Replace player if clip changed
        if let currentURL = (player.currentItem?.asset as? AVURLAsset)?.url,
           currentURL != url {
            let newPlayer = AVPlayer(url: url)
            controller.player = newPlayer
            newPlayer.play()
            return
        }

        // Handle play/pause
        if isPlaying {
            if player.rate == 0 { player.play() }
        } else {
            if player.rate != 0 { player.pause() }
        }
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
