import Foundation

enum ActionType: String, Codable {
    case like
    case dislike
    case save
    case skip
    case watchComplete = "watch_complete"
}

struct InteractionRequest: Codable {
    let clipId: UUID
    let action: ActionType
    let watchDurationMs: Int?
    let sessionId: UUID?

    enum CodingKeys: String, CodingKey {
        case clipId = "clip_id"
        case action
        case watchDurationMs = "watch_duration_ms"
        case sessionId = "session_id"
    }
}

struct InteractionResponse: Codable {
    let id: UUID
    let clipId: UUID
    let action: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case clipId = "clip_id"
        case action
        case createdAt = "created_at"
    }
}
