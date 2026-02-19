import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        Group {
            switch authManager.authState {
            case .unauthenticated:
                PlexAuthView()
            case .needsTasteProfile:
                TasteProfileView()
            case .authenticated:
                MainTabView()
            case .loading:
                SplashView()
            }
        }
        .animation(.easeInOut, value: authManager.authState)
    }
}

struct SplashView: View {
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 20) {
                Text("BYETZ")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                Text("Your Personal Clip Feed")
                    .font(.subheadline)
                    .foregroundColor(.gray)
                ProgressView()
                    .tint(.white)
            }
        }
    }
}
