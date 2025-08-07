# Coin Analyzer API 🪙

A FastAPI backend that analyzes coin images using OpenAI's GPT-4 Vision model with Azure Entra ID authentication. Perfect for iOS apps that need coin identification and historical information.

## Features

- **Image Upload**: Accepts coin images via multipart/form-data
- **AI Analysis**: Uses OpenAI GPT-4 Vision for coin identification
- **Entra ID Authentication**: Secure authentication using Azure Entra ID (formerly Azure AD)
- **Structured Response**: Returns detailed coin information including country, denomination, year, metal, and historical context
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: Built-in health monitoring endpoints

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Azure Authentication

This project uses Azure Entra ID (formerly Azure AD) authentication instead of API keys. You have several options:

#### Option A: Azure CLI (Recommended for Development)

1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. Login to Azure:
```bash
az login
```

#### Option B: Service Principal (For Production)

1. Create a service principal:
```bash
az ad sp create-for-rbac --name "coin-analyzer-api" --role contributor
```

2. Set environment variables:
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

#### Option C: Managed Identity (For Azure-hosted apps)

If running in Azure (App Service, VM, etc.), enable managed identity in your Azure resource.

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Azure OpenAI Configuration with Entra ID Authentication
# No API key needed - uses Azure Entra ID (formerly Azure AD) authentication
ENDPOINT_URL=https://copperzync.openai.azure.com/
DEPLOYMENT_NAME=gpt-4o

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 4. Test the Connection

Run the test script to verify your Azure OpenAI connection:

```bash
python test_azure_openai.py
```

### 5. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /analyze

Analyzes a coin image and returns detailed information.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Image file with key `image`

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00.000000",
  "coin_analysis": {
    "basic_info": {
      "released_year": "1964",
      "country": "United States",
      "denomination": "50 cents",
      "composition": "Silver (90%)"
    },
    "value_assessment": {
      "collector_value": "Around $10-15 USD",
      "rarity": "Common"
    },
    "description": "This is a Kennedy Half Dollar featuring President John F. Kennedy...",
    "historical_context": "The Kennedy Half Dollar was introduced in 1964...",
    "technical_details": {
      "mint_mark": "D",
      "diameter_mm": "30.6",
      "composition": "Silver"
    }
  },
  "metadata": {
    "model_used": "gpt-4o",
    "image_filename": "coin.jpg",
    "image_size_bytes": 12345,
    "processing_time": "2024-01-01T12:00:00.000000"
  }
}
```

### GET /

Health check endpoint.

**Response:**
```json
{
  "message": "Coin Analyzer API is running! 🪙"
}
```

### GET /health

Detailed health check with configuration status.

**Response:**
```json
{
  "status": "healthy",
  "azure_openai_configured": true,
  "deployment_name": "gpt-4o",
  "authentication_method": "Entra ID (Azure AD)"
}
```

### GET /debug

Debug information for troubleshooting.

**Response:**
```json
{
  "azure_openai_client_initialized": true,
  "azure_openai_endpoint_set": true,
  "azure_openai_deployment_name": "gpt-4o",
  "authentication_method": "Entra ID (Azure AD)",
  "environment_variables": {
    "ENDPOINT_URL": "https://copperzync.openai.azure.com/",
    "DEPLOYMENT_NAME": "gpt-4o"
  }
}
```

## iOS Integration Example

Here's how to call the API from your iOS app using Swift:

```swift
import Foundation

func analyzeCoin(imageData: Data) async throws -> CoinAnalysis {
    let url = URL(string: "http://localhost:8000/analyze")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    
    // Add image data
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"image\"; filename=\"coin.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n".data(using: .utf8)!)
    body.append("--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let analysis = try JSONDecoder().decode(CoinAnalysis.self, from: data)
    return analysis
}

struct CoinAnalysis: Codable {
    let success: Bool
    let timestamp: String
    let coinAnalysis: CoinAnalysisData
    let metadata: Metadata
    
    enum CodingKeys: String, CodingKey {
        case success
        case timestamp
        case coinAnalysis = "coin_analysis"
        case metadata
    }
}

struct CoinAnalysisData: Codable {
    let basicInfo: BasicInfo
    let valueAssessment: ValueAssessment
    let description: String
    let historicalContext: String
    let technicalDetails: TechnicalDetails
    
    enum CodingKeys: String, CodingKey {
        case basicInfo = "basic_info"
        case valueAssessment = "value_assessment"
        case description
        case historicalContext = "historical_context"
        case technicalDetails = "technical_details"
    }
}

struct BasicInfo: Codable {
    let releasedYear: String
    let country: String
    let denomination: String
    let composition: String
    
    enum CodingKeys: String, CodingKey {
        case releasedYear = "released_year"
        case country
        case denomination
        case composition
    }
}

struct ValueAssessment: Codable {
    let collectorValue: String
    let rarity: String
    
    enum CodingKeys: String, CodingKey {
        case collectorValue = "collector_value"
        case rarity
    }
}

struct TechnicalDetails: Codable {
    let mintMark: String
    let diameterMm: String
    let composition: String
    
    enum CodingKeys: String, CodingKey {
        case mintMark = "mint_mark"
        case diameterMm = "diameter_mm"
        case composition
    }
}

struct Metadata: Codable {
    let modelUsed: String
    let imageFilename: String
    let imageSizeBytes: Int
    let processingTime: String
    
    enum CodingKeys: String, CodingKey {
        case modelUsed = "model_used"
        case imageFilename = "image_filename"
        case imageSizeBytes = "image_size_bytes"
        case processingTime = "processing_time"
    }
}
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid file type (not an image)
- **500 Internal Server Error**: Azure OpenAI API issues or server errors
- **500 Server Error**: Azure OpenAI client not initialized

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENDPOINT_URL` | Your Azure OpenAI endpoint URL | Yes |
| `DEPLOYMENT_NAME` | Your deployment name (default: gpt-4o) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `PORT` | Server port (default: 8000) | No |

## Troubleshooting

### Authentication Issues

1. **Azure CLI not logged in**: Run `az login`
2. **Insufficient permissions**: Ensure your account has access to the Azure OpenAI resource
3. **Service principal issues**: Verify your client ID, secret, and tenant ID are correct

### Connection Issues

1. **Endpoint URL**: Verify the endpoint URL is correct and accessible
2. **Deployment name**: Ensure the deployment name matches your Azure OpenAI resource
3. **Network connectivity**: Check if you can reach the Azure OpenAI endpoint

### Testing

Use the provided test script to verify your setup:

```bash
python test_azure_openai.py
```

## Development

### Running with Auto-reload

```bash
uvicorn main:app --reload
```

### Testing with curl

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@path/to/your/coin.jpg"
```

## Security Benefits

Using Entra ID authentication provides several security advantages:

- **No API keys to manage**: Eliminates the risk of exposed API keys
- **Automatic token rotation**: Tokens are automatically refreshed
- **Fine-grained permissions**: Use Azure RBAC for precise access control
- **Audit logging**: All authentication events are logged in Azure AD
- **Multi-factor authentication**: Leverage Azure AD MFA policies

## License

MIT License - feel free to use this for your vibe coding projects! 🚀 