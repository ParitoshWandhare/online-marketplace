"""
Test Gemini API Key - Simple diagnostic script
Run this to verify your API key works
"""

import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

print("=" * 60)
print("🔍 GEMINI API KEY DIAGNOSTIC TEST")
print("=" * 60)

if not api_key:
    print("❌ ERROR: No API key found in environment!")
    print("Please check your .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:15]}...{api_key[-5:]}")
print()

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    print("✅ Gemini configured successfully")
except Exception as e:
    print(f"❌ Failed to configure Gemini: {e}")
    exit(1)

# List available models
print("\n" + "=" * 60)
print("📋 LISTING AVAILABLE MODELS")
print("=" * 60)

try:
    models = genai.list_models()
    vision_models = []
    
    for model in models:
        print(f"\n📦 Model: {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Supported methods: {model.supported_generation_methods}")
        
        # Check if it supports vision (generateContent)
        if 'generateContent' in model.supported_generation_methods:
            vision_models.append(model.name)
            print(f"   ✅ Supports Vision (generateContent)")
    
    print("\n" + "=" * 60)
    print(f"✅ Found {len(vision_models)} vision-capable models:")
    for vm in vision_models:
        print(f"   • {vm}")
    
except Exception as e:
    print(f"❌ Failed to list models: {e}")
    print("\nPossible reasons:")
    print("1. Invalid API key")
    print("2. API key doesn't have proper permissions")
    print("3. Network/firewall issues")
    print("4. Gemini API service is down")
    exit(1)

# Test a simple text generation
print("\n" + "=" * 60)
print("🧪 TESTING TEXT GENERATION")
print("=" * 60)

if vision_models:
    test_model_name = vision_models[0].replace('models/', '')
    print(f"Using model: {test_model_name}")
    
    try:
        model = genai.GenerativeModel(test_model_name)
        response = model.generate_content("Say 'Hello, API is working!'")
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        exit(1)

# Test vision with a simple image
print("\n" + "=" * 60)
print("🖼️  TESTING VISION CAPABILITY")
print("=" * 60)

try:
    from PIL import Image
    import io
    
    # Create a simple test image (red square)
    test_image = Image.new('RGB', (100, 100), color='red')
    
    model = genai.GenerativeModel(test_model_name)
    response = model.generate_content(["What color is this image?", test_image])
    
    print(f"✅ Vision Response: {response.text}")
    print("\n🎉 SUCCESS! Your Gemini API key is working perfectly!")
    
except Exception as e:
    print(f"❌ Vision test failed: {e}")
    print("\nThis might be because:")
    print("1. The model doesn't support vision")
    print("2. Pillow library is not installed")
    print("3. API quota exceeded")
    
print("\n" + "=" * 60)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 60)