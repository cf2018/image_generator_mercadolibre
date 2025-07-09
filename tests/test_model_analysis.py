#!/usr/bin/env python3
"""
Script to check available Gemini models and their capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import client
from google.genai import types

def list_available_models():
    """List all available models and their supported methods"""
    
    print("🔍 Checking Available Gemini Models")
    print("=" * 50)
    
    try:
        # List all available models
        models = client.models.list()
        
        print(f"📋 Found {len(models.models)} available models:")
        print()
        
        image_generation_models = []
        text_to_image_models = []
        
        for model in models.models:
            model_name = model.name
            supported_methods = model.supported_generation_methods if hasattr(model, 'supported_generation_methods') else []
            
            print(f"🤖 {model_name}")
            if hasattr(model, 'description') and model.description:
                print(f"   Description: {model.description}")
            
            print(f"   Supported methods: {supported_methods}")
            
            # Check if it supports generateContent
            if 'generateContent' in supported_methods:
                print(f"   ✅ Supports generateContent")
                
                # Check if it's likely an image generation model
                if any(keyword in model_name.lower() for keyword in ['image', 'imagen', 'vision', 'generate']):
                    if 'imagen' in model_name.lower():
                        text_to_image_models.append(model_name)
                        print(f"   🎨 Potential text-to-image model")
                    else:
                        image_generation_models.append(model_name)
                        print(f"   🖼️  Potential image generation model")
            else:
                print(f"   ❌ Does not support generateContent")
            
            print()
        
        print("📊 Summary:")
        print(f"   Image generation models: {image_generation_models}")
        print(f"   Text-to-image models: {text_to_image_models}")
        
        return image_generation_models, text_to_image_models
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return [], []

def test_image_generation_models(models_to_test):
    """Test image generation with different models"""
    
    print(f"\n🧪 Testing Image Generation Models")
    print("=" * 50)
    
    test_prompt = "Professional studio photograph of a black exercise rope on a gradient background. High quality, Instagram-ready, square format."
    
    for model_name in models_to_test:
        print(f"\n🔄 Testing {model_name}...")
        
        try:
            # Test basic image generation
            response = client.models.generate_content(
                model=model_name,
                contents=test_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    temperature=0.1,
                    max_output_tokens=1024,
                    candidate_count=1
                )
            )
            
            if response and response.candidates:
                print(f"✅ {model_name} - Basic image generation works")
                
                # Check if it generated an image
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"   📸 Generated image data: {len(part.inline_data.data)} bytes")
                        break
                else:
                    print(f"   ⚠️  No image data found in response")
            else:
                print(f"❌ {model_name} - No response or candidates")
                
        except Exception as e:
            print(f"❌ {model_name} - Error: {e}")

def test_text_to_image_approach():
    """Test different approaches for text-to-image generation"""
    
    print(f"\n🎨 Testing Text-to-Image Approaches")
    print("=" * 50)
    
    # Test prompt that includes text requirements
    text_prompt = """
    Create a professional Instagram advertisement image (1080x1080) for a black exercise rope.
    
    Requirements:
    - Show a black exercise rope
    - Professional gradient background
    - Include Spanish advertising text on the image
    - Add the price: $79.999
    - Include an attractive Spanish call-to-action: "¡ENTRENA COMO UN PRO!"
    - Use professional Instagram ad design
    - Modern, eye-catching layout
    - High quality and visually appealing
    - Square format (1:1 ratio)
    - All text must be in perfect Spanish
    """
    
    # Try different models that might work for text-to-image
    models_to_try = [
        "gemini-2.0-flash-preview-image-generation",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
    
    for model_name in models_to_try:
        print(f"\n🔄 Testing text-to-image with {model_name}...")
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=text_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    temperature=0.3,
                    max_output_tokens=2048,
                    candidate_count=1
                )
            )
            
            if response and response.candidates:
                print(f"✅ {model_name} - Text-to-image generation works")
                
                # Check if it generated an image
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"   📸 Generated image with text: {len(part.inline_data.data)} bytes")
                        
                        # Save test image
                        filename = f"test_text_image_{model_name.replace('/', '_').replace('-', '_')}.jpg"
                        with open(filename, 'wb') as f:
                            if isinstance(part.inline_data.data, str):
                                import base64
                                f.write(base64.b64decode(part.inline_data.data))
                            else:
                                f.write(part.inline_data.data)
                        print(f"   💾 Saved test image: {filename}")
                        break
                else:
                    print(f"   ⚠️  No image data found in response")
            else:
                print(f"❌ {model_name} - No response or candidates")
                
        except Exception as e:
            print(f"❌ {model_name} - Error: {e}")

if __name__ == "__main__":
    print("🚀 Gemini Model Analysis and Text-to-Image Testing")
    print("=" * 60)
    
    try:
        # Step 1: List available models
        image_models, text_image_models = list_available_models()
        
        # Step 2: Test image generation models
        if image_models:
            test_image_generation_models(image_models[:3])  # Test first 3
        
        # Step 3: Test text-to-image approaches
        test_text_to_image_approach()
        
        print(f"\n✅ Model analysis complete!")
        print(f"💡 Recommendations:")
        print(f"   • Check generated test images to see which model works best for text-to-image")
        print(f"   • Update TEXT_TO_IMAGE_MODEL in app.py with the working model")
        print(f"   • Consider adjusting prompt structure for better text generation")
        
    except Exception as e:
        print(f"\n💥 Analysis failed: {e}")
        import traceback
        traceback.print_exc()
