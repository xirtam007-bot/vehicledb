import Foundation
import AVFoundation

class ScannerViewModel: ObservableObject {
    @Published var isAuthorized = false
    @Published var error: String?
    
    init() {
        checkPermissions()
    }
    
    func checkPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isAuthorized = true
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    self?.isAuthorized = granted
                }
            }
        default:
            isAuthorized = false
            error = "Camera access is required to scan VINs"
        }
    }
} 