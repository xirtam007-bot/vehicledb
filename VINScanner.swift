import UIKit
import AVFoundation
import CoreData
import Foundation
import SwiftUI

class VINScanner: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    weak var delegate: VINScannerDelegate?
    private var captureSession: AVCaptureSession!
    private var previewLayer: AVCaptureVideoPreviewLayer!
    private let context = (UIApplication.shared.delegate as! AppDelegate).persistentContainer.viewContext
    
    // UI Elements
    private let scannerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private let statusLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textAlignment = .center
        label.numberOfLines = 0
        label.backgroundColor = .black.withAlphaComponent(0.7)
        label.textColor = .white
        return label
    }()
    
    private let activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .large)
        indicator.translatesAutoresizingMaskIntoConstraints = false
        indicator.color = .white
        indicator.hidesWhenStopped = true
        return indicator
    }()
    
    private var isChecking = false {
        didSet {
            DispatchQueue.main.async {
                if self.isChecking {
                    self.activityIndicator.startAnimating()
                    self.statusLabel.text = "Checking VIN..."
                } else {
                    self.activityIndicator.stopAnimating()
                }
            }
        }
    }
    
    private let apiURL = ProcessInfo.processInfo.environment["API_URL"] ?? "https://your-app-name.onrender.com"
    private let apiKey = ProcessInfo.processInfo.environment["API_KEY"] ?? "your-secret-key-here"
    
    private let networkService = VINNetworkService()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupCamera()
        setupUI()
    }
    
    private func setupUI() {
        view.backgroundColor = .black
        view.addSubview(scannerView)
        view.addSubview(statusLabel)
        view.addSubview(activityIndicator)
        
        NSLayoutConstraint.activate([
            scannerView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scannerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scannerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scannerView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            statusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusLabel.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            statusLabel.heightAnchor.constraint(equalToConstant: 50),
            
            activityIndicator.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
    }
    
    private func setupCamera() {
        captureSession = AVCaptureSession()
        
        guard let videoCaptureDevice = AVCaptureDevice.default(for: .video) else { return }
        let videoInput: AVCaptureDeviceInput
        
        do {
            videoInput = try AVCaptureDeviceInput(device: videoCaptureDevice)
        } catch {
            return
        }
        
        if (captureSession.canAddInput(videoInput)) {
            captureSession.addInput(videoInput)
        } else {
            failed()
            return
        }
        
        let metadataOutput = AVCaptureMetadataOutput()
        
        if (captureSession.canAddOutput(metadataOutput)) {
            captureSession.addOutput(metadataOutput)
            
            metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
            metadataOutput.metadataObjectTypes = [.qr]
        } else {
            failed()
            return
        }
        
        previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        scannerView.layer.addSublayer(previewLayer)
        
        DispatchQueue.global(qos: .background).async {
            self.captureSession.startRunning()
        }
    }
    
    func failed() {
        let ac = UIAlertController(title: "Scanner not supported", 
                                  message: "Your device does not support scanning QR codes", 
                                  preferredStyle: .alert)
        ac.addAction(UIAlertAction(title: "OK", style: .default))
        present(ac, animated: true)
        captureSession = nil
    }
    
    func metadataOutput(_ output: AVCaptureMetadataOutput,
                       didOutput metadataObjects: [AVMetadataObject],
                       from connection: AVCaptureConnection) {
        guard !isChecking else { return }  // Prevent multiple simultaneous checks
        
        if let metadataObject = metadataObjects.first {
            guard let readableObject = metadataObject as? AVMetadataMachineReadableCodeObject else { return }
            guard let stringValue = readableObject.stringValue else { return }
            
            AudioServicesPlaySystemSound(SystemSoundID(kSystemSoundID_Vibrate))
            
            isChecking = true
            captureSession.stopRunning()  // Pause scanning while checking
            
            Task {
                do {
                    let response = try await networkService.checkVIN(stringValue)
                    processVINResponse(response)
                    delegate?.didFindCode(stringValue)
                } catch {
                    print("Error checking VIN: \(error)")
                    updateStatus("Error checking VIN", isSuccess: false)
                }
                
                isChecking = false
                DispatchQueue.global(qos: .background).async {
                    self.captureSession.startRunning()  // Resume scanning
                }
            }
        }
    }
    
    private func processVIN(_ vin: String) {
        guard isValidVIN(vin) else {
            updateStatus("Invalid VIN format", isSuccess: false)
            return
        }
        
        checkVINUniqueness(vin) { [weak self] isUnique in
            if isUnique {
                self?.saveVIN(vin)
                self?.updateStatus("VIN successfully added", isSuccess: true)
            } else {
                self?.updateStatus("VIN already exists", isSuccess: false)
            }
        }
    }
    
    private func isValidVIN(_ vin: String) -> Bool {
        return vin.count == 17 && vin.range(of: "^[A-HJ-NPR-Z0-9]{17}$", 
                                          options: .regularExpression) != nil
    }
    
    private func checkVINUniqueness(_ vin: String, completion: @escaping (Bool) -> Void) {
        let request = NSFetchRequest<VINRecord>(entityName: "VINRecord")
        request.predicate = NSPredicate(format: "vinNumber == %@", vin)
        
        do {
            let count = try context.count(for: request)
            completion(count == 0)
        } catch {
            print("Error checking VIN uniqueness: \(error)")
            completion(false)
        }
    }
    
    private func saveVIN(_ vin: String) {
        let vinRecord = VINRecord(context: context)
        vinRecord.vinNumber = vin
        vinRecord.scanDate = Date()
        
        do {
            try context.save()
        } catch {
            print("Error saving VIN: \(error)")
        }
    }
    
    private func updateStatus(_ message: String, isSuccess: Bool) {
        DispatchQueue.main.async {
            self.statusLabel.text = message
            self.statusLabel.textColor = isSuccess ? .green : .red
            
            // Automatically clear success messages after delay
            if isSuccess {
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    self.statusLabel.text = "Ready to scan"
                    self.statusLabel.textColor = .white
                }
            }
        }
    }
    
    private func processVINResponse(_ response: VINResponse) {
        if response.found {
            updateStatus("VIN found: \(response.description ?? "")", isSuccess: true)
        } else {
            updateStatus("VIN not found", isSuccess: false)
        }
    }
}

struct VINScanner_Previews: PreviewProvider {
    static var previews: some View {
        VINScanner()
    }
} 