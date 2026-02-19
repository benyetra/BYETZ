import Foundation

@MainActor
class TasteProfileViewModel: ObservableObject {
    @Published var titles: [TasteProfileTitle] = []
    @Published var selectedIds: Set<String> = []
    @Published var isLoading = false

    var selectedCount: Int { selectedIds.count }

    func isSelected(_ title: TasteProfileTitle) -> Bool {
        selectedIds.contains(title.mediaId)
    }

    func toggleSelection(_ title: TasteProfileTitle) {
        if selectedIds.contains(title.mediaId) {
            selectedIds.remove(title.mediaId)
        } else {
            selectedIds.insert(title.mediaId)
        }
    }

    func loadTitles() async {
        isLoading = true
        do {
            titles = try await APIClient.shared.getTasteProfileTitles()
        } catch {
            print("Failed to load titles: \(error)")
        }
        isLoading = false
    }

    func submitSelections() async {
        let selected = titles.filter { selectedIds.contains($0.mediaId) }

        struct SelectionBody: Encodable {
            let selections: [TasteProfileTitle]
        }

        do {
            let _: [String: String] = try await APIClient.shared.request(
                "/taste-profile/select",
                method: "POST",
                body: SelectionBody(selections: selected)
            )
        } catch {
            print("Failed to submit selections: \(error)")
        }
    }
}
