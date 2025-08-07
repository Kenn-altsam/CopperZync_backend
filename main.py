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
        # First, try to find JSON in markdown code blocks
        clean = re.search(r"```json(.*?)```", text, re.DOTALL)
        if clean:
            return json.loads(clean.group(1).strip())
        
        # Try to find JSON in regular code blocks
        clean = re.search(r"```(.*?)```", text, re.DOTALL)
        if clean:
            try:
                return json.loads(clean.group(1).strip())
            except:
                pass
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        # Try direct JSON parsing
        return json.loads(text.strip())
    except Exception as e:
        logger.warning(f"JSON extraction failed: {e}")
        logger.warning(f"Raw text: {text[:500]}...")  # Log first 500 chars for debugging
        return {"raw": text}

# Enhanced field mapping with multiple possible field names
def extract_field_value(data, possible_names, default="unknown"):
    """Extract field value from data using multiple possible field names"""
    if isinstance(data, dict):
        for name in possible_names:
            if name in data:
                value = data[name]
                if value and value != "unknown" and value != "Unknown":
                    return value
    return default

def enhance_with_text_analysis(raw_text, response):
    """Extract basic information from raw text when JSON parsing fails"""
    text_lower = raw_text.lower()
    
    # Try to identify country from common patterns
    country_patterns = {
        "france": ["france", "french", "republique francaise", "république française"],
        "usa": ["united states", "usa", "us", "american"],
        "uk": ["united kingdom", "uk", "britain", "british", "england"],
        "germany": ["germany", "german", "deutschland"],
        "italy": ["italy", "italian", "italia"],
        "spain": ["spain", "spanish", "españa"],
        "canada": ["canada", "canadian"],
        "australia": ["australia", "australian"],
        "japan": ["japan", "japanese", "nihon"],
        "china": ["china", "chinese", "zhongguo"]
    }
    
    for country, patterns in country_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            response["coin_analysis"]["basic_info"]["country"] = country.title()
            break
    
    # Try to identify denomination from common patterns
    denomination_patterns = {
        "1 cent": ["1 cent", "one cent", "penny"],
        "5 cents": ["5 cents", "five cents", "nickel"],
        "10 cents": ["10 cents", "ten cents", "dime"],
        "25 cents": ["25 cents", "quarter", "twenty-five cents"],
        "50 cents": ["50 cents", "half dollar", "fifty cents"],
        "1 dollar": ["1 dollar", "one dollar", "dollar coin"],
        "1 euro": ["1 euro", "one euro"],
        "2 euros": ["2 euros", "two euros"],
        "5 euros": ["5 euros", "five euros"],
        "10 euros": ["10 euros", "ten euros"],
        "20 euros": ["20 euros", "twenty euros"],
        "50 euros": ["50 euros", "fifty euros"],
        "1 pound": ["1 pound", "one pound", "pound sterling"],
        "2 pounds": ["2 pounds", "two pounds"],
        "1 yen": ["1 yen", "one yen"],
        "5 yen": ["5 yen", "five yen"],
        "10 yen": ["10 yen", "ten yen"],
        "50 yen": ["50 yen", "fifty yen"],
        "100 yen": ["100 yen", "hundred yen"]
    }
    
    for denomination, patterns in denomination_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            response["coin_analysis"]["basic_info"]["denomination"] = denomination
            break
    
    # Try to identify composition from common patterns
    composition_patterns = {
        "copper": ["copper", "cu"],
        "bronze": ["bronze"],
        "brass": ["brass"],
        "silver": ["silver", "ag"],
        "gold": ["gold", "au"],
        "nickel": ["nickel", "ni"],
        "zinc": ["zinc", "zn"],
        "aluminum": ["aluminum", "aluminium", "al"],
        "steel": ["steel", "iron"]
    }
    
    found_compositions = []
    for composition, patterns in composition_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            found_compositions.append(composition)
    
    if found_compositions:
        response["coin_analysis"]["basic_info"]["composition"] = ", ".join(found_compositions)
    
    return response

# Custom JSON encoder for better serialization
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create a beautiful response structure
def create_beautiful_response(parsed_analysis, model_used, filename, image_size):
    # Enhanced field extraction with multiple possible field names
    released_year = extract_field_value(parsed_analysis, [
        "year first released", "year", "release_year", "mint_year", "first_released", "issued_year"
    ])
    
    country = extract_field_value(parsed_analysis, [
        "country", "nation", "origin", "issuing_country"
    ])
    
    denomination = extract_field_value(parsed_analysis, [
        "denomination", "value", "face_value", "coin_value", "monetary_value"
    ])
    
    composition = extract_field_value(parsed_analysis, [
        "composition", "material", "metal", "alloy", "composition_material"
    ])
    
    collector_value = extract_field_value(parsed_analysis, [
        "value", "collector_value", "market_value", "estimated_value", "worth"
    ])
    
    rarity = extract_field_value(parsed_analysis, [
        "rarity", "scarcity", "availability", "rarity_level"
    ])
    
    description = extract_field_value(parsed_analysis, [
        "description", "description_text", "coin_description", "details"
    ], "No description available")
    
    historical_context = extract_field_value(parsed_analysis, [
        "historical_context", "history", "historical_background", "context"
    ], "No historical context available")
    
    # Extract technical details
    technical_details = {}
    if isinstance(parsed_analysis.get("other_details"), dict):
        technical_details = parsed_analysis["other_details"]
    elif isinstance(parsed_analysis, dict):
        # Look for technical fields in the main response
        for key in ["mint_mark", "diameter_mm", "weight", "thickness", "edge_type"]:
            if key in parsed_analysis:
                technical_details[key] = parsed_analysis[key]
    
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "coin_analysis": {
            "basic_info": {
                "released_year": released_year,
                "country": country,
                "denomination": denomination,
                "composition": composition
            },
            "value_assessment": {
                "collector_value": collector_value,
                "rarity": rarity
            },
            "description": description,
            "historical_context": historical_context,
            "technical_details": technical_details
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
                    "role": "system",
                    "content": "You are a professional numismatist and coin expert. Your task is to analyze coin images and provide detailed, accurate information about them. You MUST respond with ONLY valid JSON in the exact format specified. Do not include any explanatory text before or after the JSON. If you cannot determine certain information, use \"unknown\" as the value. Be thorough in your analysis and provide historical context when possible."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this coin image and return ONLY a JSON object in this exact format:\n\n{\n  \"year first released\": \"1975\",\n  \"country\": \"USA\",\n  \"denomination\": \"1 cent\",\n  \"value\": \"low collector value\",\n  \"composition\": \"95% copper, 5% zinc\",\n  \"description\": \"This is a Lincoln cent featuring Abraham Lincoln. It has been minted since 1909.\",\n  \"historical_context\": \"Introduced to commemorate Lincoln's 100th birthday...\",\n  \"other_details\": {\n    \"mint_mark\": \"D\",\n    \"rarity\": \"common\",\n    \"diameter_mm\": 19.05\n  }\n}\n\nIMPORTANT: Return ONLY the JSON object. Do not include any markdown formatting, code blocks, or explanatory text. If any field cannot be determined from the image, use \"unknown\" as the value. Ensure all string values are properly quoted."
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
            "temperature": 0.1
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
                logger.info(f"Raw GPT response: {raw_analysis[:1000]}...")  # Log first 1000 chars
                
                parsed_analysis = extract_json(raw_analysis)
                logger.info(f"Parsed analysis: {parsed_analysis}")
                
                # Create beautiful, structured response
                beautiful_response = create_beautiful_response(
                    parsed_analysis, 
                    AZURE_OPENAI_DEPLOYMENT_NAME, 
                    image.filename, 
                    len(image_data)
                )
                
                # If we got mostly "unknown" values, try to extract more information from the raw text
                if (beautiful_response["coin_analysis"]["basic_info"]["country"] == "unknown" and 
                    beautiful_response["coin_analysis"]["basic_info"]["denomination"] == "unknown"):
                    logger.warning("Most fields are unknown, attempting to extract info from raw text")
                    # Try to extract basic info from the raw text using simple text analysis
                    enhanced_response = enhance_with_text_analysis(raw_analysis, beautiful_response)
                    return JSONResponse(
                        content=enhanced_response,
                        status_code=200,
                        headers={"Content-Type": "application/json"}
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

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check configuration and test basic functionality"""
    return {
        "azure_openai_api_key_set": bool(AZURE_OPENAI_API_KEY),
        "azure_openai_endpoint_set": bool(AZURE_OPENAI_ENDPOINT),
        "azure_openai_deployment_name": AZURE_OPENAI_DEPLOYMENT_NAME,
        "api_url": AZURE_OPENAI_API_URL,
        "environment_variables": {
            "AZURE_OPENAI_API_KEY_length": len(AZURE_OPENAI_API_KEY) if AZURE_OPENAI_API_KEY else 0,
            "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
            "AZURE_OPENAI_DEPLOYMENT_NAME": AZURE_OPENAI_DEPLOYMENT_NAME
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 