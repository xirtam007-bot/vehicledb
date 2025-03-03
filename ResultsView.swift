import SwiftUI

struct ResultsView: View {
    let vinResponse: VINResponse?
    let isLoading: Bool
    
    var body: some View {
        VStack(spacing: 20) {
            if isLoading {
                ProgressView("Checking VIN...")
                    .progressViewStyle(CircularProgressViewStyle(tint: .blue))
            } else if let response = vinResponse {
                if response.found {
                    Text("✅ VIN Found")
                        .font(.title)
                        .foregroundColor(.green)
                    
                    if let description = response.description {
                        Text(description)
                            .multilineTextAlignment(.center)
                    }
                    
                    if let date = response.scanDate {
                        Text("Scanned: \(date)")
                            .font(.caption)
                    }
                } else {
                    Text("❌ VIN Not Found")
                        .font(.title)
                        .foregroundColor(.red)
                }
            }
        }
        .padding()
    }
} 