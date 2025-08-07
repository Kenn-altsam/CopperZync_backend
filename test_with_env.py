#!/usr/bin/env python3
"""
Test script for Azure OpenAI integration using environment variables
This simulates the Render deployment environment
"""

import os
import base64
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_openai_with_env():
    """Test the Azure OpenAI connection using environment variables"""
    
    endpoint = os.getenv("ENDPOINT_URL", "https://copperzync.openai.azure.com/")
    deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")
    
    # Check for service principal environment variables
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    
    print(f"Testing connection to: {endpoint}")
    print(f"Using deployment: {deployment}")
    print(f"Service Principal configured: {bool(client_id and client_secret and tenant_id)}")
    
    try:
        # Initialize Azure OpenAI client with Entra ID authentication
        print("Initializing Azure OpenAI client...")
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )
        
        print("✅ Azure OpenAI client initialized successfully!")
        
        # Test with a simple text prompt
        print("Testing with a simple text prompt...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'Connection successful!' if you can see this message."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            print(f"✅ Response received: {response.choices[0].message.content}")
            print("🎉 Azure OpenAI integration is working correctly!")
            return True
        else:
            print("❌ No response received from Azure OpenAI")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Azure OpenAI connection: {e}")
        print("\nTroubleshooting tips:")
        print("1. Set environment variables for service principal:")
        print("   - AZURE_CLIENT_ID")
        print("   - AZURE_CLIENT_SECRET") 
        print("   - AZURE_TENANT_ID")
        print("2. Or run 'az login' for interactive authentication")
        print("3. Verify your Azure subscription has access to the OpenAI resource")
        print("4. Check that the endpoint URL and deployment name are correct")
        return False

if __name__ == "__main__":
    print("🧪 Testing Azure OpenAI Integration with Environment Variables")
    print("=" * 65)
    
    success = test_azure_openai_with_env()
    
    if success:
        print("\n✅ All tests passed! Your Azure OpenAI integration is ready for Render deployment.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        print("\nFor Render deployment, you need to:")
        print("1. Create a service principal: az ad sp create-for-rbac --name 'coin-analyzer-render'")
        print("2. Set environment variables in Render dashboard:")
        print("   - AZURE_CLIENT_ID")
        print("   - AZURE_CLIENT_SECRET")
        print("   - AZURE_TENANT_ID")
        print("   - ENDPOINT_URL")
        print("   - DEPLOYMENT_NAME") 