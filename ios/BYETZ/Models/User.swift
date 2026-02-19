import Foundation

struct UserProfile: Codable {
    let id: UUID
    let plexUsername: String
    let plexEmail: String?
    let plexThumb: String?
    let totalLikes: Int
    let totalSaves: Int
    let totalClipsWatched: Int
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case plexUsername = "plex_username"
        case plexEmail = "plex_email"
        case plexThumb = "plex_thumb"
        case totalLikes = "total_likes"
        case totalSaves = "total_saves"
        case totalClipsWatched = "total_clips_watched"
        case createdAt = "created_at"
    }
}

struct UserSettings: Codable {
    var subtitleOverlay: Bool
    var contentMaturityFilter: String
    var clipQuality: String
    var notificationsEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case subtitleOverlay = "subtitle_overlay"
        case contentMaturityFilter = "content_maturity_filter"
        case clipQuality = "clip_quality"
        case notificationsEnabled = "notifications_enabled"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let tokenType: String
    let userId: UUID
    let username: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case userId = "user_id"
        case username
    }
}
