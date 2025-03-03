import CoreData

@objc(VINRecord)
public class VINRecord: NSManagedObject {
    @NSManaged public var vinNumber: String
    @NSManaged public var scanDate: Date
}

struct VINRecord: Codable {
    let vinValue: String
    let description: String?
    let scanDate: String?
    
    enum CodingKeys: String, CodingKey {
        case vinValue = "vin_value"
        case description
        case scanDate = "scan_date"
    }
}

struct VINResponse: Codable {
    let found: Bool
    let description: String?
    let scanDate: String?
} 