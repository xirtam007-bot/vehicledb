import Foundation

class VINNetworkService {
    private let baseURL = "https://vehicledb.onrender.com"
    private let apiKey = "5fe6a87f63ababfcb50fc3e15ed9cbbf"
    
    struct VINResponse: Codable {
        let found: Bool
        let description: String?
        let scan_date: String?
    }
    
    enum NetworkError: Error {
        case invalidURL
        case noData
        case decodingError
        case serverError(Int)
        case unknown(Error)
    }
    
    func checkVIN(_ vin: String) async throws -> VINResponse {
        guard let url = URL(string: "\(baseURL)/api/check_vin?vin=\(vin)") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.unknown(NSError(domain: "", code: -1))
        }
        
        guard httpResponse.statusCode == 200 else {
            throw NetworkError.serverError(httpResponse.statusCode)
        }
        
        let decoder = JSONDecoder()
        return try decoder.decode(VINResponse.self, from: data)
    }
} 