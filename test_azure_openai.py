#!/usr/bin/env python3
"""
Test script for Azure OpenAI integration with Entra ID authentication
"""

import os
import base64
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_openai_connection():
    """Test the Azure OpenAI connection with Entra ID authentication"""
    
    endpoint = os.getenv("ENDPOINT_URL", "https://copperzync.openai.azure.com/")
    deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")
    
    print(f"Testing connection to: {endpoint}")
    print(f"Using deployment: {deployment}")
    
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
        print("1. Make sure you're logged into Azure CLI: az login")
        print("2. Verify your Azure subscription has access to the OpenAI resource")
        print("3. Check that the endpoint URL and deployment name are correct")
        print("4. Ensure your account has the necessary permissions")
        return False

if __name__ == "__main__":
    print("🧪 Testing Azure OpenAI Integration with Entra ID Authentication")
    print("=" * 60)
    
    success = test_azure_openai_connection()
    
    if success:
        print("\n✅ All tests passed! Your Azure OpenAI integration is ready.")
    else:
        print("\n❌ Tests failed. Please check your configuration.") 