import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case unauthorized
    case serverError(Int)
    case decodingError
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .unauthorized: return "Authentication required"
        case .serverError(let code): return "Server error: \(code)"
        case .decodingError: return "Failed to decode response"
        case .networkError(let error): return error.localizedDescription
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    private let baseURL: String
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: String = "http://192.168.1.9:8101") {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    private func buildRequest(path: String, method: String = "GET", body: Encodable? = nil) throws -> URLRequest {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = try encoder.encode(AnyEncodable(body))
        }

        return request
    }

    func request<T: Decodable>(_ path: String, method: String = "GET", body: Encodable? = nil) async throws -> T {
        let request = try buildRequest(path: path, method: method, body: body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }

        switch httpResponse.statusCode {
        case 200...299:
            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError
            }
        case 401:
            throw APIError.unauthorized
        default:
            throw APIError.serverError(httpResponse.statusCode)
        }
    }

    func authenticatePlex(token: String) async throws -> AuthResponse {
        struct PlexAuthBody: Encodable {
            let plex_token: String
        }
        return try await request("/auth/plex", method: "POST", body: PlexAuthBody(plex_token: token))
    }

    func getFeed(limit: Int = 10, offset: Int = 0) async throws -> FeedResponse {
        return try await request("/feed?limit=\(limit)&offset=\(offset)")
    }

    func streamURL(clipId: UUID) -> URL? {
        var urlString = "\(baseURL)/clips/\(clipId.uuidString)/stream"
        if let token = KeychainService.shared.getToken() {
            urlString += "?token=\(token)"
        }
        return URL(string: urlString)
    }

    func submitInteraction(_ interaction: InteractionRequest) async throws -> InteractionResponse {
        return try await request("/interactions", method: "POST", body: interaction)
    }

    func getProfile() async throws -> UserProfile {
        return try await request("/profile")
    }

    func getSavedClips() async throws -> [Clip] {
        return try await request("/profile/saved")
    }

    func getLibraryStatus() async throws -> LibraryStatus {
        return try await request("/library/status")
    }

    func discoverLibraries() async throws {
        let _: [String: String] = try await request("/library/discover", method: "POST")
    }

    func processLibraries() async throws {
        let _: [String: String] = try await request("/library/process", method: "POST")
    }

    func triggerRescan() async throws {
        let _: [String: String] = try await request("/library/rescan", method: "POST")
    }

    func getTasteProfileTitles() async throws -> [TasteProfileTitle] {
        return try await request("/taste-profile/titles")
    }

    func getSettings() async throws -> UserSettings {
        return try await request("/settings")
    }

    func updateSettings(_ settings: UserSettings) async throws -> UserSettings {
        return try await request("/settings", method: "PUT", body: settings)
    }
}

struct AnyEncodable: Encodable {
    private let encodeClosure: (Encoder) throws -> Void

    init(_ value: Encodable) {
        encodeClosure = { encoder in
            try value.encode(to: encoder)
        }
    }

    func encode(to encoder: Encoder) throws {
        try encodeClosure(encoder)
    }
}
