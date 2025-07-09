#!/usr/bin/env python3
"""
Isolated test for Gemini image generation functionality
"""

import os
import sys
import time
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_image_generation():
    """Test Gemini image generation in isolation"""
    
    print("🧪 Testing Gemini Image Generation")
    print("=" * 40)
    
    # Configure API - try multiple sources
    api_key = (
        os.getenv('GEMINI_API_KEY') or 
        os.getenv('GOOGLE_API_KEY') 
    )
    
    if not api_key:
        print("❌ No API key found")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    genai.configure(api_key=api_key)
    print(f"✅ API configured")
    
    # Test different models - focus on image generation models
    models_to_test = [
        'gemini-2.0-flash-exp-image-generation',
        'gemini-2.0-flash-preview-image-generation',
        'imagen-3.0-generate-002',
        'imagen-4.0-generate-preview-06-06'
    ]
    
    for model_name in models_to_test:
        print(f"\n🔍 Testing model: {model_name}")
        
        try:
            model = genai.GenerativeModel(model_name)
            
            # Simple test prompt
            simple_prompt = "Create a simple red square image, 100x100 pixels"
            
            print(f"📤 Sending simple prompt: {simple_prompt}")
            response = model.generate_content(simple_prompt)
            
            if not response:
                print(f"❌ No response from {model_name}")
                continue
            
            print(f"✅ Got response from {model_name}")
            
            # Check response structure
            if not response.candidates:
                print(f"❌ No candidates in response")
                continue
            
            print(f"✅ Found {len(response.candidates)} candidates")
            
            candidate = response.candidates[0]
            
            if not candidate.content:
                print(f"❌ No content in candidate")
                continue
            
            if not candidate.content.parts:
                print(f"❌ No parts in content")
                continue
            
            print(f"✅ Found {len(candidate.content.parts)} parts")
            
            # Look for image data
            image_found = False
            for i, part in enumerate(candidate.content.parts):
                print(f"  Part {i+1}:")
                
                if hasattr(part, 'text') and part.text:
                    print(f"    📝 Text: {part.text[:100]}...")
                
                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"    🖼️  Has inline_data")
                    
                    if part.inline_data.data:
                        print(f"    ✅ Has image data")
                        data_type = type(part.inline_data.data)
                        print(f"    Data type: {data_type}")
                        
                        if isinstance(part.inline_data.data, str):
                            print(f"    Data length: {len(part.inline_data.data)} chars")
                        else:
                            print(f"    Data length: {len(part.inline_data.data)} bytes")
                        
                        # Try to save the image
                        try:
                            if isinstance(part.inline_data.data, str):
                                image_data = base64.b64decode(part.inline_data.data)
                            else:
                                image_data = part.inline_data.data
                            
                            filename = f"test_image_{model_name.replace('-', '_')}_{int(time.time())}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(image_data)
                            
                            print(f"    ✅ Image saved as: {filename}")
                            print(f"    Image size: {len(image_data)} bytes")
                            image_found = True
                            
                        except Exception as save_error:
                            print(f"    ❌ Failed to save image: {save_error}")
                    else:
                        print(f"    ❌ No data in inline_data")
                else:
                    print(f"    ℹ️  No inline_data")
            
            if image_found:
                print(f"🎉 SUCCESS: {model_name} can generate images!")
                return True
            else:
                print(f"⚠️  {model_name} responded but no image data found")
                
        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    print(f"\n❌ No working image generation model found")
    return False

def test_text_generation():
    """Test basic text generation to verify API works"""
    
    print("\n🧪 Testing Basic Text Generation")
    print("=" * 40)
    
    # Configure API - try multiple sources
    api_key = (
        os.getenv('GEMINI_API_KEY') or 
        os.getenv('GOOGLE_API_KEY') 
    )
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello and confirm you're working")
        
        if response and response.text:
            print(f"✅ Text generation works: {response.text}")
            return True
        else:
            print(f"❌ No text response")
            return False
            
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        return False

def list_available_models():
    """List all available models"""
    
    print("\n🔍 Listing Available Models")
    print("=" * 40)
    
    # Configure API - try multiple sources
    api_key = (
        os.getenv('GEMINI_API_KEY') or 
        os.getenv('GOOGLE_API_KEY') 
    )
    
    genai.configure(api_key=api_key)
    
    try:
        models = genai.list_models()
        model_list = list(models)
        
        print(f"Found {len(model_list)} models:")
        
        for model in model_list:
            print(f"  - {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                methods = model.supported_generation_methods
                print(f"    Methods: {methods}")
        
        return model_list
        
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return []

def main():
    """Main test function"""
    
    print("🚀 Gemini Image Generation Debug Test")
    print("=" * 50)
    
    # Test basic connectivity
    if not test_text_generation():
        print("❌ Basic API connection failed. Check your API key.")
        return
    
    # List available models
    models = list_available_models()
    
    # Test image generation
    success = test_gemini_image_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Image generation test successful!")
    else:
        print("❌ Image generation test failed.")
        print("\nPossible issues:")
        print("1. The model doesn't support image generation")
        print("2. API quota exceeded")
        print("3. Model name changed or deprecated")
        print("4. Image generation requires different parameters")

if __name__ == '__main__':
    main()
