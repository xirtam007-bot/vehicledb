import SwiftUI

struct ScannerView: View {
    @Environment(\.presentationMode) var presentationMode
    @StateObject private var viewModel = ScannerViewModel()
    @Binding var result: String?
    
    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.isAuthorized {
                    CameraView(scannedCode: $result)
                        .ignoresSafeArea()
                } else if let error = viewModel.error {
                    Text(error)
                        .foregroundColor(.red)
                        .padding()
                }
            }
            .navigationTitle("Scan VIN")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
            .onChange(of: result) { newValue in
                if newValue != nil {
                    presentationMode.wrappedValue.dismiss()
                }
            }
        }
    }
} 