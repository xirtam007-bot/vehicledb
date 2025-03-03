import Foundation

protocol VINScannerDelegate: AnyObject {
    func didFindCode(_ code: String)
} 