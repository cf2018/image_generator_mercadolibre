#!/usr/bin/env python3
"""
Quick test for the specific image generation model
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

def test_specific_model():
    """Test the specific image generation model"""
    
    print("🧪 Testing Specific Image Generation Model")
    print("=" * 50)
    
    # Configure API
    api_key = (
        os.getenv('GEMINI_API_KEY') or 
        os.getenv('GOOGLE_API_KEY')  # Working API key from your code
    )
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    genai.configure(api_key=api_key)
    
    # Try the model that works according to the provided code
    models_to_test = [
        'gemini-2.0-flash-preview-image-generation'
    ]
    
    for model_name in models_to_test:
        print(f"\n🎯 Testing model: {model_name}")
        
        try:
            model = genai.GenerativeModel(model_name)
            
            # Simple test prompt
            prompt = "Create a red square image"
            
            print(f"📤 Sending simple prompt: {prompt}")
            
            # Use the exact response modalities that the model accepts: TEXT, IMAGE
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_modalities": ["TEXT", "IMAGE"]
                }
            )
            print(f"✅ Request sent successfully")
            
            print(f"✅ Got response")
            
            if not response or not response.candidates:
                print(f"❌ No candidates in response")
                continue
            
            candidate = response.candidates[0]
            
            if not candidate.content or not candidate.content.parts:
                print(f"❌ No content parts")
                continue
            
            print(f"✅ Found {len(candidate.content.parts)} parts")
            
            for i, part in enumerate(candidate.content.parts):
                print(f"  Part {i+1}:")
                
                if hasattr(part, 'text') and part.text:
                    print(f"    📝 Text: {part.text[:100]}...")
                
                if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                    print(f"    🖼️  Has image data!")
                    
                    try:
                        if isinstance(part.inline_data.data, str):
                            image_data = base64.b64decode(part.inline_data.data)
                        else:
                            image_data = part.inline_data.data
                        
                        filename = f"test_{model_name.replace('-', '_')}_{int(time.time())}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"    ✅ Image saved: {filename}")
                        print(f"    Size: {len(image_data)} bytes")
                        
                        return True, model_name
                        
                    except Exception as e:
                        print(f"    ❌ Error saving: {e}")
            
            print(f"❌ No image data found in {model_name}")
            
        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")
    
    return False, None

if __name__ == '__main__':
    success, working_model = test_specific_model()
    
    if success:
        print(f"\n🎉 SUCCESS! Image generation is working with model: {working_model}")
        print(f"Update your app.py to use: IMAGE_GENERATION_MODEL = '{working_model}'")
    else:
        print("\n❌ Image generation failed with all models.")
        print("\nPossible reasons:")
        print("1. These models might not support direct image generation")
        print("2. Different API or configuration needed")
        print("3. Models might be for different use cases")
        print("4. Need to use Imagen models instead")
