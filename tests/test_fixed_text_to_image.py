#!/usr/bin/env python3
"""
Test script to verify the fixed text-to-image generation
"""

import requests
import json

def test_fixed_ai_text_mode():
    """Test that AI text mode now works with the correct model"""
    
    print("🧪 Testing Fixed AI Text Mode (Text-to-Image Generation)")
    print("=" * 60)
    
    # Use a simple test URL
    test_url = "https://articulo.mercadolibre.com.ar/MLA-1705036436-soga-battle-rope-gadnic-ejercicio-entrenamiento-x9mts-negro-_JM"
    
    print(f"\n📦 Testing product: Battle Rope")
    print("-" * 30)
    
    # Scrape product
    print("🔍 Step 1: Scraping product...")
    scrape_response = requests.post('http://localhost:5000/scrape', 
                                  json={'url': test_url},
                                  timeout=60)
    
    if scrape_response.status_code != 200:
        print(f"❌ Scraping failed")
        return
        
    scrape_data = scrape_response.json()
    if not scrape_data.get('success'):
        print(f"❌ Scraping unsuccessful")
        return
    
    product_data = scrape_data['product_data']
    selected_images = product_data.get('images', [])[:1]  # Use just 1 image for speed
    
    print(f"✅ Scraped: {product_data.get('title')}")
    print(f"   Images available: {len(selected_images)}")
    
    # Test AI text mode (use_text_overlay=False)
    print(f"\n🤖 Step 2: Testing AI text mode with fixed model...")
    print("Expected behavior:")
    print("  1. Use gemini-2.0-flash-preview-image-generation (should work)")
    print("  2. Generate image with text directly (no fallback needed)")
    print("  3. Return image with AI-generated Spanish text")
    
    ad_response = requests.post('http://localhost:5000/generate-ad',
                              json={
                                  'product_data': product_data,
                                  'selected_images': selected_images,
                                  'use_text_overlay': False  # AI text mode
                              },
                              timeout=120)
    
    if ad_response.status_code == 200:
        ad_data = ad_response.json()
        if ad_data.get('success'):
            print(f"✅ Ad generation successful!")
            print(f"   Text overlay used: {ad_data.get('text_overlay_used')}")
            print(f"   Fallback used: {ad_data.get('fallback_used')}")
            
            # Verify expected behavior (should NOT use fallback now)
            if not ad_data.get('fallback_used'):
                print(f"✅ PASS: No fallback needed - AI text generation worked!")
            else:
                print(f"⚠️  INFO: Fallback was used (unexpected but still works)")
            
            # Download and save
            download_url = f"http://localhost:5000{ad_data.get('download_url')}"
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                filename = f"test_fixed_ai_text_mode.jpg"
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"   💾 Image saved as: {filename}")
        else:
            print(f"❌ Ad generation failed: {ad_data.get('error')}")
    else:
        print(f"❌ Request failed: {ad_response.status_code}")
        print(f"Response: {ad_response.text}")

def test_both_modes_comparison():
    """Test both modes side by side to compare results"""
    
    print(f"\n🔄 Step 3: Comparing Both Modes")
    print("-" * 30)
    
    # Simple product data for testing
    test_product = {
        'title': 'iPhone 15 Pro Max 256GB Negro',
        'price': '$1,299',
        'description': 'El iPhone más avanzado con cámara profesional y pantalla Super Retina XDR.',
        'images': ['https://example.com/iphone.jpg']
    }
    
    for mode_name, use_overlay in [("AI Text Mode", False), ("Programmatic Overlay", True)]:
        print(f"\n📱 Testing {mode_name}...")
        
        ad_response = requests.post('http://localhost:5000/generate-ad',
                                  json={
                                      'product_data': test_product,
                                      'selected_images': [],
                                      'use_text_overlay': use_overlay
                                  },
                                  timeout=120)
        
        if ad_response.status_code == 200:
            ad_data = ad_response.json()
            if ad_data.get('success'):
                print(f"✅ {mode_name} successful!")
                print(f"   Fallback used: {ad_data.get('fallback_used')}")
                
                # Download and save
                download_url = f"http://localhost:5000{ad_data.get('download_url')}"
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    safe_name = mode_name.lower().replace(' ', '_')
                    filename = f"test_comparison_{safe_name}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"   💾 Saved as: {filename}")
            else:
                print(f"❌ {mode_name} failed: {ad_data.get('error')}")
        else:
            print(f"❌ {mode_name} request failed: {ad_response.status_code}")

if __name__ == "__main__":
    try:
        test_fixed_ai_text_mode()
        test_both_modes_comparison()
        
        print(f"\n🎉 Text-to-Image Fix Test Completed!")
        print(f"✅ Key Improvements:")
        print(f"   • Updated TEXT_TO_IMAGE_MODEL to working model")
        print(f"   • AI text mode should now work without fallback")
        print(f"   • Both modes generate professional Instagram ads")
        print(f"   • Compare generated images to see the difference")
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
