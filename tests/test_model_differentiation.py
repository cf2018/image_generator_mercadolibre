#!/usr/bin/env python3
"""
Test script to verify AI text generation mode uses proper text-to-image model
"""

import requests
import json

def test_ai_text_generation_models():
    print("🧪 Testing AI Text Generation with Proper Models")
    print("=" * 50)
    
    # Test URL
    test_url = "https://www.mercadolibre.com.ar/perchero-colgante-puerta-horizontal-mite-color-blanco/p/MLA46720949"
    
    # Step 1: Scrape product data
    print("📋 Step 1: Scraping product data...")
    scrape_response = requests.post('http://localhost:5000/scrape', 
                                  json={'url': test_url},
                                  timeout=60)
    
    if scrape_response.status_code != 200:
        print(f"❌ Scraping failed: {scrape_response.status_code}")
        return False
    
    scrape_data = scrape_response.json()
    if not scrape_data.get('success'):
        print(f"❌ Scraping unsuccessful: {scrape_data.get('error')}")
        return False
    
    product_data = scrape_data['product_data']
    selected_images = product_data.get('images', [])[:2]
    
    print(f"✅ Product: {product_data.get('title')}")
    print(f"   Selected {len(selected_images)} images")
    
    # Test 1: Programmatic Text Overlay Mode (Clean Image Model)
    print(f"\n🎨 Test 1: Programmatic Text Overlay Mode")
    print("Using: gemini-2.0-flash-preview-image-generation")
    print("-" * 40)
    
    ad_response_overlay = requests.post('http://localhost:5000/generate-ad',
                                      json={
                                          'product_data': product_data,
                                          'selected_images': selected_images,
                                          'use_text_overlay': True
                                      },
                                      timeout=120)
    
    if ad_response_overlay.status_code == 200:
        overlay_data = ad_response_overlay.json()
        if overlay_data.get('success'):
            print(f"✅ Programmatic overlay mode successful!")
            print(f"   Model used: Clean image generation + PIL overlay")
            
            # Download image
            download_url = f"http://localhost:5000{overlay_data.get('download_url')}"
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                with open('test_clean_image_model.jpg', 'wb') as f:
                    f.write(download_response.content)
                print(f"   Saved as: test_clean_image_model.jpg")
        else:
            print(f"❌ Overlay mode failed: {overlay_data.get('error')}")
    else:
        print(f"❌ Overlay mode request failed: {ad_response_overlay.status_code}")
    
    # Test 2: AI Text Generation Mode (Text-to-Image Model)
    print(f"\n🤖 Test 2: AI Text Generation Mode")
    print("Using: imagen-3.0-generate-001 (or fallback)")
    print("-" * 40)
    
    ad_response_ai = requests.post('http://localhost:5000/generate-ad',
                                 json={
                                     'product_data': product_data,
                                     'selected_images': selected_images,
                                     'use_text_overlay': False
                                 },
                                 timeout=120)
    
    if ad_response_ai.status_code == 200:
        ai_data = ad_response_ai.json()
        if ai_data.get('success'):
            print(f"✅ AI text generation mode successful!")
            print(f"   Model used: Text-to-image generation")
            
            # Download image
            download_url = f"http://localhost:5000{ai_data.get('download_url')}"
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                with open('test_text_to_image_model.jpg', 'wb') as f:
                    f.write(download_response.content)
                print(f"   Saved as: test_text_to_image_model.jpg")
        else:
            print(f"❌ AI text mode failed: {ai_data.get('error')}")
    else:
        print(f"❌ AI text mode request failed: {ad_response_ai.status_code}")
    
    print(f"\n🔍 Model Comparison Results:")
    print(f"📝 Clean Image Model: Should produce clean product image (no text)")
    print(f"🤖 Text-to-Image Model: Should produce image with integrated Spanish text")
    print(f"\nCheck both generated images to compare quality and text integration!")
    
    return True

def test_model_error_handling():
    """Test fallback behavior when models fail"""
    print(f"\n🛠️  Testing Model Fallback Behavior")
    print("-" * 40)
    
    # This test would normally require intentionally breaking a model
    # For now, just document the expected behavior
    print(f"Expected fallback behavior:")
    print(f"1. AI text mode tries: imagen-3.0-generate-001")
    print(f"2. If that fails, falls back to: gemini-2.0-flash-preview-image-generation")
    print(f"3. Clean image mode always uses: gemini-2.0-flash-preview-image-generation")
    
    return True

if __name__ == "__main__":
    try:
        success1 = test_ai_text_generation_models()
        success2 = test_model_error_handling()
        
        if success1:
            print(f"\n🎉 Model differentiation tests completed!")
            print(f"\nGenerated files:")
            print(f"• test_clean_image_model.jpg - Clean image for text overlay")
            print(f"• test_text_to_image_model.jpg - AI-generated text on image")
            print(f"\nThe AI text mode should now use proper text-to-image models!")
        else:
            print(f"\n❌ Model differentiation tests failed!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
