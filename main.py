from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional
import logging
from dotenv import load_dotenv
import re
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coin Analyzer API",
    description="Analyze coins using OpenAI GPT-4 Vision",
    version="1.0.0"
)

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

if not AZURE_OPENAI_API_KEY:
    logger.warning("AZURE_OPENAI_API_KEY not found in environment variables")
if not AZURE_OPENAI_ENDPOINT:
    logger.warning("AZURE_OPENAI_ENDPOINT not found in environment variables")

# Azure OpenAI API URL
AZURE_OPENAI_API_URL = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-15-preview"

# Extract JSON from markdown-style code block
def extract_json(text):
    try:
        # Remove ```json ... ```
        clean = re.search(r"```json(.*?)```", text, re.DOTALL)
        if clean:
            return json.loads(clean.group(1))
        else:
            return json.loads(text)  # Try direct JSON
    except Exception:
        return {"raw": text}

# Custom JSON encoder for better serialization
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create a beautiful response structure
def create_beautiful_response(parsed_analysis, model_used, filename, image_size):
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "coin_analysis": {
            "basic_info": {
                "released_year": parsed_analysis.get("year first released", parsed_analysis.get("year", "unknown")),
                "country": parsed_analysis.get("country", "unknown"),
                "denomination": parsed_analysis.get("denomination", "unknown"),
                "composition": parsed_analysis.get("composition", "unknown")
            },
            "value_assessment": {
                "collector_value": parsed_analysis.get("value", "unknown"),
                "rarity": parsed_analysis.get("other_details", {}).get("rarity", "unknown")
            },
            "description": parsed_analysis.get("description", "No description available"),
            "historical_context": parsed_analysis.get("historical_context", "No historical context available"),
            "technical_details": parsed_analysis.get("other_details", {})
        },
        "metadata": {
            "model_used": model_used,
            "image_filename": filename,
            "image_size_bytes": image_size,
            "processing_time": datetime.now().isoformat()
        }
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Coin Analyzer API is running! 🪙"}

@app.post("/analyze")
async def analyze_coin(image: UploadFile = File(...)):
    """
    Analyze a coin image using OpenAI GPT-4 Vision
    
    Args:
        image: The coin image file (multipart/form-data)
    
    Returns:
        JSON response with coin analysis from GPT-4 Vision
    """
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        raise HTTPException(
            status_code=500, 
            detail="Azure OpenAI configuration not complete. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT"
        )
    
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image"
        )
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Prepare the request to Azure OpenAI
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json",
            "Azure-OpenAI-Image-Encoding": "base64"  # Required for image_url base64
        }
        
        # Convert image to base64 for OpenAI API
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this coin image and return your response in the following JSON format. If you cannot determine certain information, use \"unknown\" as the value. Always return valid JSON that can be parsed by a computer.\n\n{\n  \"year first released\": \"1975\",\n  \"country\": \"USA\",\n  \"denomination\": \"1 cent\",\n  \"value\": \"low collector value\",\n  \"composition\": \"95% copper, 5% zinc\",\n  \"description\": \"This is a Lincoln cent featuring Abraham Lincoln. It has been minted since 1909.\",\n  \"historical_context\": \"Introduced to commemorate Lincoln's 100th birthday...\",\n  \"other_details\": {\n    \"mint_mark\": \"D\",\n    \"rarity\": \"common\",\n    \"diameter_mm\": 19.05\n  }\n}\n\nProvide accurate information about the coin shown in the image. If any field cannot be determined, use \"unknown\" as the value. Ensure the JSON is properly formatted and all string values are properly quoted."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image.content_type.split('/')[-1]};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        # Make request to Azure OpenAI
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                AZURE_OPENAI_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Azure OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Error communicating with Azure OpenAI API"
                )
            
            azure_response = response.json()
            
            # Extract the analysis from Azure OpenAI response
            if "choices" in azure_response and len(azure_response["choices"]) > 0:
                raw_analysis = azure_response["choices"][0]["message"]["content"]
                parsed_analysis = extract_json(raw_analysis)
                
                # Create beautiful, structured response
                beautiful_response = create_beautiful_response(
                    parsed_analysis, 
                    AZURE_OPENAI_DEPLOYMENT_NAME, 
                    image.filename, 
                    len(image_data)
                )
                
                return JSONResponse(
                    content=beautiful_response,
                    status_code=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected response format from Azure OpenAI"
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout while communicating with Azure OpenAI API")
        raise HTTPException(
            status_code=504,
            detail="Request timeout - Azure OpenAI API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "azure_openai_configured": bool(AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT),
        "deployment_name": AZURE_OPENAI_DEPLOYMENT_NAME
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 