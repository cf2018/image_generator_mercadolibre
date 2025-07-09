#!/usr/bin/env python3
"""
Test enhanced backgrounds with different colored products
"""

import requests
import json

def test_product_colors():
    print("🧪 Testing Enhanced Backgrounds with Different Product Colors")
    print("=" * 60)
    
    # Test URLs with different colored products
    test_products = [
        {
            'name': 'White Coat Rack (Blanco)',
            'url': 'https://www.mercadolibre.com.ar/perchero-colgante-puerta-horizontal-mite-color-blanco/p/MLA46720949',
            'expected_color': 'blanco'
        }
        # Note: We'll use the same product but the system will analyze the actual colors
    ]
    
    for i, product in enumerate(test_products):
        print(f"\n🎨 Test {i+1}: {product['name']}")
        print("-" * 40)
        
        # Scrape product
        scrape_response = requests.post('http://localhost:5000/scrape', 
                                      json={'url': product['url']},
                                      timeout=60)
        
        if scrape_response.status_code != 200:
            print(f"❌ Scraping failed for {product['name']}")
            continue
            
        scrape_data = scrape_response.json()
        if not scrape_data.get('success'):
            print(f"❌ Scraping unsuccessful for {product['name']}")
            continue
        
        product_data = scrape_data['product_data']
        selected_images = product_data.get('images', [])[:2]
        
        print(f"✅ Product: {product_data.get('title')}")
        print(f"   Description preview: {product_data.get('description', '')[:100]}...")
        
        # Generate ad with enhanced background
        ad_response = requests.post('http://localhost:5000/generate-ad',
                                  json={
                                      'product_data': product_data,
                                      'selected_images': selected_images,
                                      'use_text_overlay': True
                                  },
                                  timeout=120)
        
        if ad_response.status_code == 200:
            ad_data = ad_response.json()
            if ad_data.get('success'):
                print(f"✅ Enhanced background ad generated!")
                
                # Download and save
                download_url = f"http://localhost:5000{ad_data.get('download_url')}"
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    filename = f"test_color_{i+1}_{product['expected_color']}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"   Saved as: {filename}")
            else:
                print(f"❌ Ad generation failed: {ad_data.get('error')}")
        else:
            print(f"❌ Request failed: {ad_response.status_code}")
    
    print(f"\n🎉 Color-based background tests completed!")
    print(f"Check the generated images to see how backgrounds adapt to product colors.")

def test_background_consistency():
    """Test that the same product generates consistent backgrounds"""
    print(f"\n🔄 Testing Background Consistency")
    print("-" * 40)
    
    test_url = "https://www.mercadolibre.com.ar/perchero-colgante-puerta-horizontal-mite-color-blanco/p/MLA46720949"
    
    # Scrape once
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
    selected_images = product_data.get('images', [])[:2]
    
    # Generate 2 ads to test consistency
    for i in range(2):
        print(f"\n   Generation {i+1}:")
        
        ad_response = requests.post('http://localhost:5000/generate-ad',
                                  json={
                                      'product_data': product_data,
                                      'selected_images': selected_images,
                                      'use_text_overlay': True
                                  },
                                  timeout=120)
        
        if ad_response.status_code == 200:
            ad_data = ad_response.json()
            if ad_data.get('success'):
                download_url = f"http://localhost:5000{ad_data.get('download_url')}"
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    filename = f"test_consistency_{i+1}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"     Saved as: {filename}")
    
    print(f"   Both images should have similar background styling!")

if __name__ == "__main__":
    try:
        test_product_colors()
        test_background_consistency()
        
        print(f"\n✅ All enhanced background tests completed!")
        print(f"Generated images should show:")
        print(f"   • Color-appropriate backgrounds")
        print(f"   • Professional lighting and gradients")
        print(f"   • Product-focused composition")
        print(f"   • Instagram-ready aesthetic")
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
