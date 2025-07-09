#!/usr/bin/env python3
"""
Script to list all available Gemini API models and their capabilities.
"""

import os
import json
import sys
import traceback
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)

# Initialize the client
print("Initializing Gemini client...")
print(f"API Key: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-4:]}")
client = genai.Client(api_key=GEMINI_API_KEY)

def main():
    """List and analyze available models"""
    print("🔍 Retrieving available Gemini models...")
    
    try:
        print("Calling list_models() API...")
        # Get all available models
        models = client.list_models()
        
        print("API call complete")
        print(f"Models type: {type(models)}")
        
        if not models:
            print("❌ No models found or API didn't return model list")
            return
        
        models_list = list(models)
        print(f"✅ Found {len(models_list)} models\n")
        
        # Track models with specific capabilities
        image_generation_models = []
        multimodal_models = []
        vision_models = []
        text_models = []
        
        # Print model details
        for model in models_list:
            model_name = model.name
            print(f"\n📌 Model: {model_name}")
            
            # Display model description (truncated if too long)
            if hasattr(model, "description") and model.description:
                description = model.description[:150] + "..." if len(model.description) > 150 else model.description
                print(f"   Description: {description}")
            else:
                print("   Description: Not available")
                
            # Show supported generation methods
            if hasattr(model, "supported_generation_methods"):
                methods = model.supported_generation_methods
                print(f"   Methods: {', '.join(methods)}")
                
                # Check for specific capabilities based on methods
                if "generateContent" in methods:
                    print("   ✓ Can generate content")
                if "countTokens" in methods:
                    print("   ✓ Can count tokens")
                if "embedContent" in methods:
                    print("   ✓ Can embed content")
                if "batchEmbedContents" in methods:
                    print("   ✓ Can batch embed contents")
            else:
                print("   Methods: Not available")
            
            # Check for image generation capabilities
            if "image-generation" in model_name.lower() or "imagen" in model_name.lower():
                image_generation_models.append(model_name)
                print("   🎨 Potential image generation model")
            
            # Check for multimodal capabilities
            if "vision" in model_name.lower() or "multimodal" in model_name.lower():
                multimodal_models.append(model_name)
                print("   👁️ Potential vision/multimodal model")
                
            # Show input/output token limits if available
            if hasattr(model, "input_token_limit"):
                print(f"   Input Token Limit: {model.input_token_limit}")
            if hasattr(model, "output_token_limit"):
                print(f"   Output Token Limit: {model.output_token_limit}")
                
            # Show temperature range if available
            if hasattr(model, "temperature_range"):
                print(f"   Temperature Range: {model.temperature_range.min_value} to {model.temperature_range.max_value}")
                
            # Check for any other interesting attributes
            for attr in dir(model):
                if not attr.startswith("_") and attr not in ["name", "description", "supported_generation_methods", 
                                                           "input_token_limit", "output_token_limit", "temperature_range"]:
                    value = getattr(model, attr)
                    if value and not callable(value):
                        print(f"   {attr}: {value}")
                        
                        # Look for image generation capabilities in other attributes
                        value_str = str(value).lower()
                        if "image" in value_str and "generat" in value_str:
                            if model_name not in image_generation_models:
                                image_generation_models.append(model_name)
                                print("   🎨 Image generation capability detected")
        
        # Summarize findings
        print("\n\n📊 MODEL CAPABILITY SUMMARY")
        print("=" * 50)
        
        print(f"\n🎨 Models with image generation capabilities ({len(image_generation_models)}):")
        for model in image_generation_models:
            print(f"  - {model}")
            
        print(f"\n👁️ Multimodal/Vision models ({len(multimodal_models)}):")
        for model in multimodal_models:
            print(f"  - {model}")
            
        # Recommend models for the app
        print("\n💡 RECOMMENDATION:")
        print("Based on the available models:")
        
        if image_generation_models:
            print(f"For image generation, use: {image_generation_models[0]}")
        else:
            print("No dedicated image generation models found. Continue using the current model.")
            
        # Check if any model has "text-to-image" in its name or description
        text_to_image_models = [model.name for model in models if "text-to-image" in model.name.lower() or 
                              (hasattr(model, "description") and model.description and "text-to-image" in model.description.lower())]
        
        if text_to_image_models:
            print(f"For text-to-image generation, use: {text_to_image_models[0]}")
        else:
            print("No dedicated text-to-image models found. Continue using your current model for text overlay.")
            
    except Exception as e:
        print(f"❌ Error retrieving models: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
