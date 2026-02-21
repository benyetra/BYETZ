import Foundation

struct Clip: Codable, Identifiable {
    let id: UUID
    let mediaId: String
    let title: String
    let seasonEpisode: String?
    let startTimeMs: Int
    let endTimeMs: Int
    let durationMs: Int
    let compositeScore: Double
    let genreTags: [String]
    let actors: [String]
    let director: String?
    let decade: String?
    let moodTags: [String]
    let thumbnailUrl: String?
    let streamUrl: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case mediaId = "media_id"
        case title
        case seasonEpisode = "season_episode"
        case startTimeMs = "start_time_ms"
        case endTimeMs = "end_time_ms"
        case durationMs = "duration_ms"
        case compositeScore = "composite_score"
        case genreTags = "genre_tags"
        case actors
        case director
        case decade
        case moodTags = "mood_tags"
        case thumbnailUrl = "thumbnail_url"
        case streamUrl = "stream_url"
        case createdAt = "created_at"
    }
}

struct FeedResponse: Codable {
    let clips: [Clip]
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case clips
        case hasMore = "has_more"
    }
}
