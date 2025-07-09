#!/usr/bin/env python3
"""
Script to test text-to-image generation quality and find the best model
for generating Instagram ads with high-quality text rendering.
"""

import os
import sys
import traceback
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import time

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Models to test for text-to-image capability
MODELS_TO_TEST = [
    'gemini-2.0-flash-preview-image-generation',  # Current model
    'gemini-3-flash-preview-image-generation',
    'gemini-pro-vision',
    'gemini-1.5-pro-001-vision',
    'imagen',                       # Potential dedicated models
    'imagen-2.0-flash',
    'imagen-3.0-flash',
    'text-to-image.preview'
]

def generate_instagram_ad_with_text(model_name):
    """
    Test the model's ability to generate an Instagram ad with high-quality text
    """
    print(f"\n🔍 Testing model: {model_name}")
    
    # Prompt designed to test text rendering quality
    prompt = """
    Create a professional Instagram advertisement image for a coffee machine.
    Price: $399
    
    Design Requirements:
    - Professional product photography
    - Beautiful gradient background
    - Include clearly readable advertising text "CAFÉ PREMIUM" on the image
    - Include the price: $399
    - Include call-to-action: "¡COMPRA AHORA!"
    - Professional Instagram ad design with modern typography
    - Text must be crisp, clear and professional
    - High quality and visually appealing
    - Square format (1:1 ratio)
    - All text must be perfectly readable
    """
    
    try:
        print(f"📤 Sending request to {model_name}...")
        
        # Try with specific config for image generation
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    temperature=0.2,
                    max_output_tokens=2048,
                    candidate_count=1
                )
            )
        except Exception as config_error:
            print(f"⚠️ Config error: {config_error}")
            print(f"🔄 Trying simpler request...")
            
            # Simpler fallback request
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
        
        # Process response
        if not response or not response.candidates or not response.candidates[0].content:
            print(f"❌ Model {model_name} failed: No valid response")
            return False, None
        
        # Look for image in response
        for part in response.candidates[0].content.parts:
            if hasattr(part, "mime_type") and part.mime_type and part.mime_type.startswith("image/"):
                # Save image
                timestamp = int(time.time())
                filename = f"text_quality_test_{model_name.replace('/', '_').replace('-', '_').replace('.', '_')}_{timestamp}.png"
                
                with open(filename, "wb") as f:
                    f.write(part.data)
                
                print(f"✅ Generated image saved as {filename}")
                return True, filename
        
        print(f"❌ Model {model_name} did not return an image")
        return False, None
        
    except Exception as e:
        print(f"❌ Error with model {model_name}: {e}")
        print(traceback.format_exc())
        return False, None

def main():
    """Main test function"""
    print("🚀 Starting Text-to-Image Quality Test")
    print("Testing models for Instagram ad generation with high-quality text")
    
    results = {
        "successful_models": [],
        "failed_models": []
    }
    
    # Test each model
    for model in MODELS_TO_TEST:
        success, filename = generate_instagram_ad_with_text(model)
        
        if success:
            results["successful_models"].append((model, filename))
        else:
            results["failed_models"].append(model)
    
    # Print results summary
    print("\n\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    print(f"\n✅ Successful models ({len(results['successful_models'])}):")
    for model, filename in results["successful_models"]:
        print(f"  - {model} → {filename}")
    
    print(f"\n❌ Failed models ({len(results['failed_models'])}):")
    for model in results["failed_models"]:
        print(f"  - {model}")
    
    print("\n📝 RECOMMENDATION:")
    if results["successful_models"]:
        print("Review the generated images and choose the model that produces the best text quality.")
        print("Update the TEXT_TO_IMAGE_MODEL variable in app.py with your preferred model.")
    else:
        print("No models succeeded. Continue using the current model configuration.")

if __name__ == "__main__":
    main()
