import Foundation

struct LibraryStatus: Codable {
    let serverName: String
    let serverReachable: Bool
    let libraries: [LibraryDetail]

    enum CodingKeys: String, CodingKey {
        case serverName = "server_name"
        case serverReachable = "server_reachable"
        case libraries
    }
}

struct LibraryDetail: Codable, Identifiable {
    let id: UUID
    let libraryTitle: String
    let libraryType: String
    let enabled: Bool
    let totalItems: Int
    let processedItems: Int
    let processingPercentage: Double
    let lastScanned: String?

    enum CodingKeys: String, CodingKey {
        case id
        case libraryTitle = "library_title"
        case libraryType = "library_type"
        case enabled
        case totalItems = "total_items"
        case processedItems = "processed_items"
        case processingPercentage = "processing_percentage"
        case lastScanned = "last_scanned"
    }
}

struct TasteProfileTitle: Codable, Identifiable {
    var id: String { mediaId }
    let mediaId: String
    let title: String
    let year: Int?
    let posterUrl: String?
    let genreTags: [String]
    let mediaType: String

    /// Resolves relative poster paths (e.g. "/library/poster?url=...") to full URLs via the BYETZ API.
    var resolvedPosterURL: URL? {
        guard let posterUrl else { return nil }
        if posterUrl.hasPrefix("http") {
            return URL(string: posterUrl)
        }
        // Relative path — prepend the API base URL
        let base = "http://192.168.1.9:8101"
        return URL(string: "\(base)\(posterUrl)")
    }

    enum CodingKeys: String, CodingKey {
        case mediaId = "media_id"
        case title
        case year
        case posterUrl = "poster_url"
        case genreTags = "genre_tags"
        case mediaType = "media_type"
    }
}
