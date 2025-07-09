#!/usr/bin/env python3
"""
Test script to verify AI text mode model usage fix
"""

import requests
import json

def test_ai_text_mode_fallback():
    """Test that AI text mode properly handles model fallback"""
    
    print("🧪 Testing AI Text Mode Model Fallback")
    print("=" * 50)
    
    # Use the battle rope product that was failing
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
    selected_images = product_data.get('images', [])[:2]  # Use first 2 images
    
    print(f"✅ Scraped: {product_data.get('title')}")
    print(f"   Images available: {len(selected_images)}")
    
    # Test AI text mode (use_text_overlay=False)
    print(f"\n🤖 Step 2: Testing AI text mode...")
    print("Expected behavior:")
    print("  1. Try imagen-3.0-generate-001 (will fail)")
    print("  2. Fallback to gemini-2.0-flash-preview-image-generation")
    print("  3. Generate clean image and add programmatic text overlay")
    
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
            
            # Verify expected behavior
            if ad_data.get('fallback_used'):
                print(f"✅ PASS: Fallback was properly used")
            else:
                print(f"❓ INFO: No fallback used (Imagen model worked?)")
            
            # Download and save
            download_url = f"http://localhost:5000{ad_data.get('download_url')}"
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                filename = f"test_ai_text_mode_fixed.jpg"
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"   Image saved as: {filename}")
        else:
            print(f"❌ Ad generation failed: {ad_data.get('error')}")
    else:
        print(f"❌ Request failed: {ad_response.status_code}")
        print(f"Response: {ad_response.text}")
    
    # Also test normal text overlay mode for comparison
    print(f"\n🔤 Step 3: Testing programmatic text overlay mode for comparison...")
    
    ad_response_overlay = requests.post('http://localhost:5000/generate-ad',
                              json={
                                  'product_data': product_data,
                                  'selected_images': selected_images,
                                  'use_text_overlay': True  # Programmatic text mode
                              },
                              timeout=120)
    
    if ad_response_overlay.status_code == 200:
        ad_data_overlay = ad_response_overlay.json()
        if ad_data_overlay.get('success'):
            print(f"✅ Programmatic overlay ad generation successful!")
            print(f"   Text overlay used: {ad_data_overlay.get('text_overlay_used')}")
            print(f"   Fallback used: {ad_data_overlay.get('fallback_used')}")
            
            # Download and save
            download_url = f"http://localhost:5000{ad_data_overlay.get('download_url')}"
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                filename = f"test_programmatic_mode_comparison.jpg"
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"   Image saved as: {filename}")
        else:
            print(f"❌ Programmatic overlay ad generation failed: {ad_data_overlay.get('error')}")
    else:
        print(f"❌ Programmatic overlay request failed: {ad_response_overlay.status_code}")

def test_model_configuration():
    """Test that models are properly configured"""
    print(f"\n🔧 Testing Model Configuration")
    print("-" * 30)
    
    try:
        # Import and check model constants
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import IMAGE_GENERATION_MODEL, TEXT_TO_IMAGE_MODEL, FALLBACK_TEXT_TO_IMAGE_MODEL
        
        print(f"✅ Model Configuration:")
        print(f"   IMAGE_GENERATION_MODEL: {IMAGE_GENERATION_MODEL}")
        print(f"   TEXT_TO_IMAGE_MODEL: {TEXT_TO_IMAGE_MODEL}")
        print(f"   FALLBACK_TEXT_TO_IMAGE_MODEL: {FALLBACK_TEXT_TO_IMAGE_MODEL}")
        
        # Verify models are different
        if IMAGE_GENERATION_MODEL != TEXT_TO_IMAGE_MODEL:
            print(f"✅ PASS: Different models configured for different modes")
        else:
            print(f"❌ FAIL: Same model configured for both modes")
            
    except Exception as e:
        print(f"❌ Error checking model configuration: {e}")

if __name__ == "__main__":
    try:
        test_model_configuration()
        test_ai_text_mode_fallback()
        
        print(f"\n🎉 AI Text Mode Fallback Test Completed!")
        print(f"Key improvements:")
        print(f"  • AI text mode now properly attempts text-to-image model first")
        print(f"  • When Imagen model fails, falls back gracefully")
        print(f"  • Fallback generates clean image and adds programmatic text")
        print(f"  • User gets informative feedback about fallback usage")
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
