import SwiftUI

struct TasteProfileView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = TasteProfileViewModel()

    private let columns = [
        GridItem(.adaptive(minimum: 120), spacing: 12)
    ]

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VStack(spacing: 16) {
                VStack(spacing: 8) {
                    Text("Build Your Taste Profile")
                        .font(.title2.bold())
                        .foregroundColor(.white)

                    Text("Select at least 10 titles you enjoy")
                        .font(.subheadline)
                        .foregroundColor(.gray)

                    ProgressView(value: Double(viewModel.selectedCount), total: 10)
                        .tint(viewModel.selectedCount >= 10 ? .green : .orange)
                        .padding(.horizontal)

                    Text("\(viewModel.selectedCount) selected")
                        .font(.caption)
                        .foregroundColor(viewModel.selectedCount >= 10 ? .green : .orange)
                }
                .padding(.top)

                ScrollView {
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(viewModel.titles) { title in
                            TasteTitleCard(
                                title: title,
                                isSelected: viewModel.isSelected(title),
                                onTap: { viewModel.toggleSelection(title) }
                            )
                        }
                    }
                    .padding(.horizontal)
                }

                Button(action: submitProfile) {
                    Text("Continue")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(viewModel.selectedCount >= 10 ? Color.orange : Color.gray)
                        .foregroundColor(.black)
                        .cornerRadius(12)
                }
                .disabled(viewModel.selectedCount < 10)
                .padding(.horizontal)
                .padding(.bottom)
            }
        }
        .task {
            await viewModel.loadTitles()
        }
    }

    private func submitProfile() {
        Task {
            await viewModel.submitSelections()
            authManager.completeTasteProfile()
        }
    }
}

struct TasteTitleCard: View {
    let title: TasteProfileTitle
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 4) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.3))
                .aspectRatio(2/3, contentMode: .fit)
                .overlay(
                    VStack {
                        Image(systemName: "film")
                            .font(.title)
                            .foregroundColor(.gray)
                        Text(title.title)
                            .font(.caption2)
                            .foregroundColor(.white)
                            .multilineTextAlignment(.center)
                            .lineLimit(2)
                            .padding(.horizontal, 4)
                    }
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(isSelected ? Color.orange : Color.clear, lineWidth: 3)
                )
                .overlay(alignment: .topTrailing) {
                    if isSelected {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.orange)
                            .padding(4)
                    }
                }

            if let year = title.year {
                Text(String(year))
                    .font(.caption2)
                    .foregroundColor(.gray)
            }
        }
        .onTapGesture(perform: onTap)
    }
}
