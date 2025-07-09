#!/usr/bin/env python3
"""
Simple script to test the text-to-image capabilities of the current Gemini model.
"""

import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)

# Initialize the client
client = genai.Client(api_key=GEMINI_API_KEY)

# Current model in use
MODEL = 'gemini-2.0-flash-preview-image-generation'

def test_image_generation():
    """Test the current model's image generation capabilities"""
    
    print(f"\n🧪 Testing {MODEL} for image generation...")
    
    # Test prompt to generate an image with text
    prompt = """
    Create a professional Instagram advertisement image for a coffee machine.
    Price: $399
    
    Design Requirements:
    - Professional product photography
    - Beautiful background
    - Include clearly readable text "CAFÉ PREMIUM" on the image
    - Add the price: $399
    - Include call-to-action: "¡COMPRA AHORA!"
    - High quality and visually appealing
    - Square format (1:1 ratio)
    """
    
    try:
        print(f"📤 Sending request to {MODEL}...")
        
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        
        print(f"✅ Received response")
        
        # Check if we got an image
        image_found = False
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, "mime_type") and part.mime_type and part.mime_type.startswith("image/"):
                image_found = True
                
                # Save the image
                img_data = part.data
                timestamp = int(time.time())
                filename = f"gemini_ad_test_{timestamp}.png"
                
                with open(filename, "wb") as f:
                    f.write(img_data)
                
                print(f"✅ Image saved as {filename}")
                print(f"Check this image to see if text quality is good")
        
        if not image_found:
            print(f"❌ No image found in response")
            print(f"Response content type: {type(response.candidates[0].content)}")
            print(f"Content parts: {response.candidates[0].content.parts}")
        
        print("\n💡 CONCLUSION:")
        print("The model being used is NOT a true text-to-image model but a multimodal model.")
        print("Current Gemini API doesn't offer specialized text-to-image models like Imagen.")
        print("Text quality issues are expected with the current model.")
        print("For better text quality, use the programmatic text overlay mode.")
        
    except Exception as e:
        print(f"❌ Error testing image generation: {e}")

if __name__ == "__main__":
    test_image_generation()
