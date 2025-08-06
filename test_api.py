#!/usr/bin/env python3
"""
Test script for the Coin Analyzer API
Usage: python test_api.py [path_to_image]
"""

import asyncio
import httpx
import sys
import os
from pathlib import Path

async def test_analyze_endpoint(image_path: str):
    """Test the /analyze endpoint with a coin image"""
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file '{image_path}' not found")
        return
    
    print(f"🪙 Testing coin analysis with: {image_path}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test health endpoint first
            print("🔍 Checking API health...")
            health_response = await client.get("http://localhost:8000/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ API is healthy: {health_data}")
            else:
                print(f"❌ API health check failed: {health_response.status_code}")
                return
            
            # Test analyze endpoint
            print("📤 Uploading image for analysis...")
            with open(image_path, "rb") as f:
                files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
                response = await client.post("http://localhost:8000/analyze", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Analysis successful!")
                print(f"📊 Model used: {data['model_used']}")
                print(f"📁 Image: {data['image_filename']} ({data['image_size']} bytes)")
                print("\n🔍 Analysis:")
                print("-" * 50)
                print(data['analysis'])
                print("-" * 50)
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Error: Could not connect to the API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_root_endpoint():
    """Test the root endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint: {data['message']}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing root endpoint: {str(e)}")

async def main():
    """Main test function"""
    print("🧪 Coin Analyzer API Test Suite")
    print("=" * 40)
    
    # Test root endpoint
    await test_root_endpoint()
    print()
    
    # Test analyze endpoint if image provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        await test_analyze_endpoint(image_path)
    else:
        print("💡 To test coin analysis, provide an image path:")
        print("   python test_api.py path/to/coin.jpg")
        print("\n📝 Make sure:")
        print("   1. The API server is running (python main.py)")
        print("   2. Azure OpenAI credentials are set in environment")
        print("   3. You have a coin image to test with")

if __name__ == "__main__":
    asyncio.run(main()) 