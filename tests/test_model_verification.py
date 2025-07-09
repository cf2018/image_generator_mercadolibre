#!/usr/bin/env python3
"""
Test script to verify model differentiation based on text overlay mode
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import InstagramAdGenerator, IMAGE_GENERATION_MODEL, TEXT_TO_IMAGE_MODEL, VISION_MODEL, TEXT_MODEL, FALLBACK_TEXT_TO_IMAGE_MODEL, client

def test_model_selection():
    """Test that different models are selected based on text overlay preference"""
    
    print("🧪 Testing Model Selection Logic")
    print("=" * 50)
    
    # Mock product data
    mock_product = {
        'title': 'iPhone 15 Pro Max 256GB',
        'price': '$1,299',
        'images': ['https://example.com/iphone1.jpg', 'https://example.com/iphone2.jpg']
    }
    
    mock_concept = "Premium smartphone advertisement focusing on camera quality"
    mock_images = ['https://example.com/iphone1.jpg']
    
    generator = InstagramAdGenerator()
    
    # Test 1: Programmatic text overlay mode (should use IMAGE_GENERATION_MODEL)
    print("\n🔤 Test 1: Programmatic Text Overlay Mode")
    print("Expected model: IMAGE_GENERATION_MODEL (gemini-2.0-flash-preview-image-generation)")
    
    try:
        # We'll monkey patch the generate_content method to capture the model used
        original_generate_content = client.models.generate_content
        captured_model = None
        
        def mock_generate_content(model, contents, config=None):
            nonlocal captured_model
            captured_model = model
            print(f"📋 Model used: {model}")
            # Return a mock response to avoid actual API call
            raise Exception("Mock error to avoid API call")
        
        client.models.generate_content = mock_generate_content
        
        # This should use IMAGE_GENERATION_MODEL
        try:
            generator.generate_instagram_ad(mock_product, mock_concept, mock_images, use_text_overlay=True)
        except Exception as e:
            if "Mock error" in str(e):
                print(f"✅ Captured model for programmatic overlay: {captured_model}")
                if captured_model == IMAGE_GENERATION_MODEL:
                    print("✅ PASS: Correct model selected for programmatic text overlay")
                else:
                    print(f"❌ FAIL: Wrong model selected. Expected {IMAGE_GENERATION_MODEL}, got {captured_model}")
            else:
                print(f"❌ Unexpected error: {e}")
        
        # Reset for next test
        captured_model = None
        
        # Test 2: AI text generation mode (should use TEXT_TO_IMAGE_MODEL)
        print("\n🤖 Test 2: AI Text Generation Mode")
        print("Expected model: TEXT_TO_IMAGE_MODEL (imagen-3.0-generate-001)")
        
        try:
            generator.generate_instagram_ad(mock_product, mock_concept, mock_images, use_text_overlay=False)
        except Exception as e:
            if "Mock error" in str(e):
                print(f"✅ Captured model for AI text: {captured_model}")
                if captured_model == TEXT_TO_IMAGE_MODEL:
                    print("✅ PASS: Correct model selected for AI text generation")
                else:
                    print(f"❌ FAIL: Wrong model selected. Expected {TEXT_TO_IMAGE_MODEL}, got {captured_model}")
            else:
                print(f"❌ Unexpected error: {e}")
        
        # Restore original method
        client.models.generate_content = original_generate_content
        
    except Exception as e:
        print(f"❌ Test setup error: {e}")
    
    print("\n📊 Model Configuration Summary:")
    print(f"VISION_MODEL: {VISION_MODEL}")
    print(f"TEXT_MODEL: {TEXT_MODEL}")
    print(f"IMAGE_GENERATION_MODEL: {IMAGE_GENERATION_MODEL}")
    print(f"TEXT_TO_IMAGE_MODEL: {TEXT_TO_IMAGE_MODEL}")
    print(f"FALLBACK_TEXT_TO_IMAGE_MODEL: {FALLBACK_TEXT_TO_IMAGE_MODEL}")

if __name__ == "__main__":
    test_model_selection()
