import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var scannerVM = ScannerViewModel()
    @State private var showScanner = false
    @State private var scanResult: String?
    @State private var isLoading = false
    @State private var vinResponse: VINResponse?
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("Checking VIN...")
                        .progressViewStyle(CircularProgressViewStyle())
                } else if let response = vinResponse {
                    ResultsView(vinResponse: response, isLoading: false)
                }
                
                Button("Scan VIN") {
                    showScanner = true
                }
                .buttonStyle(.borderedProminent)
                .disabled(isLoading)
                .sheet(isPresented: $showScanner) {
                    ScannerView(result: $scanResult)
                }
            }
            .navigationTitle("VIN Scanner")
            .onChange(of: scanResult) { newValue in
                if let vin = newValue {
                    checkVIN(vin)
                }
            }
        }
    }
    
    private func checkVIN(_ vin: String) {
        isLoading = true
        scanResult = nil
        
        Task {
            do {
                let url = URL(string: "\(ProcessInfo.processInfo.environment["API_URL"] ?? "")/api/check_vin")!
                var request = URLRequest(url: url)
                request.addValue(ProcessInfo.processInfo.environment["API_KEY"] ?? "", 
                               forHTTPHeaderField: "X-API-Key")
                
                let (data, _) = try await URLSession.shared.data(for: request)
                vinResponse = try JSONDecoder().decode(VINResponse.self, from: data)
            } catch {
                print("Error: \(error)")
            }
            
            isLoading = false
        }
    }
} 