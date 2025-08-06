# Coin Analyzer API 🪙

A FastAPI backend that analyzes coin images using OpenAI's GPT-4 Vision model. Perfect for iOS apps that need coin identification and historical information.

## Features

- **Image Upload**: Accepts coin images via multipart/form-data
- **AI Analysis**: Uses OpenAI GPT-4 Vision for coin identification
- **Structured Response**: Returns detailed coin information including country, denomination, year, metal, and historical context
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: Built-in health monitoring endpoints

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Azure OpenAI Configuration

Create a `.env` file in the project root:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-vision

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Run the Server

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
  "analysis": "This appears to be a 1964 Kennedy Half Dollar...",
  "model_used": "gpt-4-vision",
  "image_filename": "coin.jpg",
  "image_size": 12345
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
  "deployment_name": "gpt-4-vision"
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
    let analysis: String
    let modelUsed: String
    let imageFilename: String
    let imageSize: Int
    
    enum CodingKeys: String, CodingKey {
        case success
        case analysis
        case modelUsed = "model_used"
        case imageFilename = "image_filename"
        case imageSize = "image_size"
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
- **500 Internal Server Error**: OpenAI API issues or server errors
- **504 Gateway Timeout**: OpenAI API timeout
- **500 Server Error**: Missing OpenAI API key

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | Yes |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Your deployment name (default: gpt-4-vision) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `PORT` | Server port (default: 8000) | No |

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

## License

MIT License - feel free to use this for your vibe coding projects! 🚀 