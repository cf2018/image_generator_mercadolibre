"""
Test suite for the MercadoLibre Instagram Ad Generator
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import InstagramAdGenerator, app
import google.generativeai as genai

class TestInstagramAdGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.ad_generator = InstagramAdGenerator()
        self.sample_product_data = {
            'title': 'Test Product Title',
            'price': '1234',
            'description': 'This is a test product description for testing purposes.',
            'images': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg'],
            'url': 'https://articulo.mercadolibre.com.ar/test'
        }
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_analyze_product_info_basic(self):
        """Test basic product info analysis"""
        print("\n🧪 Testing analyze_product_info...")
        
        try:
            result = self.ad_generator.analyze_product_info(self.sample_product_data)
            
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, "Error creating ad concept")
            self.assertGreater(len(result), 10)  # Should have some content
            
            print(f"✅ Product analysis successful")
            print(f"   Result length: {len(result)} characters")
            print(f"   Preview: {result[:100]}...")
            
        except Exception as e:
            print(f"❌ Product analysis failed: {e}")
            self.fail(f"analyze_product_info failed: {e}")
    
    def test_gemini_models_availability(self):
        """Test if Gemini models are accessible"""
        print("\n🧪 Testing Gemini model availability...")
        
        try:
            # Test text model
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Say 'Hello, test!'")
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.text)
            print(f"✅ Text model working: {response.text}")
            
        except Exception as e:
            print(f"❌ Text model failed: {e}")
            self.fail(f"Text model not accessible: {e}")
        
        try:
            # Test image generation model
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # Simple test prompt
            response = model.generate_content("Create a simple red square image")
            self.assertIsNotNone(response)
            print(f"✅ Image model accessible")
            
        except Exception as e:
            print(f"❌ Image model failed: {e}")
            print(f"   This might be expected if the model doesn't support image generation")
    
    def test_image_download(self):
        """Test image downloading functionality"""
        print("\n🧪 Testing image download...")
        
        # Test with a simple image URL (placeholder service)
        test_url = "https://via.placeholder.com/150"
        
        try:
            result = self.ad_generator.download_image(test_url)
            
            if result:
                self.assertIsNotNone(result)
                print(f"✅ Image download successful")
                print(f"   Downloaded {len(result.getvalue())} bytes")
            else:
                print(f"⚠️  Image download returned None (might be network issue)")
                
        except Exception as e:
            print(f"❌ Image download failed: {e}")
    
    def test_generate_ad_with_mock_data(self):
        """Test ad generation with mock product data (no real API calls)"""
        print("\n🧪 Testing ad generation with mock...")
        
        # Mock the Gemini API calls
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Mock ad concept: Great product with amazing features!"
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            try:
                # Test ad concept generation
                ad_concept = self.ad_generator.analyze_product_info(self.sample_product_data)
                self.assertIsInstance(ad_concept, str)
                print(f"✅ Mock ad concept generation successful")
                
                # Test image generation (will fail but we can see the flow)
                ad_image = self.ad_generator.generate_instagram_ad(
                    self.sample_product_data, 
                    ad_concept, 
                    None  # No image URL to avoid network calls
                )
                
                # This will likely return None since we're mocking, but it tests the flow
                print(f"ℹ️  Mock image generation result: {'Success' if ad_image else 'None (expected with mock)'}")
                
            except Exception as e:
                print(f"❌ Mock test failed: {e}")
    
    def test_flask_endpoints(self):
        """Test Flask endpoints"""
        print("\n🧪 Testing Flask endpoints...")
        
        # Test home page
        try:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            print(f"✅ Home page accessible")
        except Exception as e:
            print(f"❌ Home page test failed: {e}")
        
        # Test scrape endpoint with invalid data
        try:
            response = self.client.post('/scrape', 
                                     json={'url': 'invalid-url'},
                                     content_type='application/json')
            self.assertEqual(response.status_code, 400)
            print(f"✅ Scrape endpoint properly validates URLs")
        except Exception as e:
            print(f"❌ Scrape endpoint test failed: {e}")
        
        # Test generate-ad endpoint with missing data
        try:
            response = self.client.post('/generate-ad', 
                                     json={},
                                     content_type='application/json')
            self.assertEqual(response.status_code, 400)
            print(f"✅ Generate-ad endpoint properly validates input")
        except Exception as e:
            print(f"❌ Generate-ad endpoint test failed: {e}")

class TestGeminiIntegration(unittest.TestCase):
    """Test Gemini API integration specifically"""
    
    def test_api_key_configuration(self):
        """Test if Gemini API key is properly configured"""
        print("\n🧪 Testing Gemini API configuration...")
        
        try:
            import google.generativeai as genai
            
            # Try to list models to test API key
            models = genai.list_models()
            model_list = list(models)
            
            self.assertGreater(len(model_list), 0)
            print(f"✅ API key valid, found {len(model_list)} models")
            
            # Check if our required models are available
            model_names = [model.name for model in model_list]
            
            required_models = [
                'models/gemini-1.5-flash',
                'models/gemini-2.0-flash-exp'
            ]
            
            for model_name in required_models:
                if model_name in model_names:
                    print(f"✅ Model available: {model_name}")
                else:
                    print(f"⚠️  Model not found: {model_name}")
            
        except Exception as e:
            print(f"❌ API configuration test failed: {e}")
            print(f"   Check your GEMINI_API_KEY environment variable")

def run_debug_tests():
    """Run specific tests to debug the ad generation issue"""
    print("🔍 Running debug tests for Instagram ad generation...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add specific tests
    suite.addTest(TestGeminiIntegration('test_api_key_configuration'))
    suite.addTest(TestInstagramAdGenerator('test_gemini_models_availability'))
    suite.addTest(TestInstagramAdGenerator('test_analyze_product_info_basic'))
    suite.addTest(TestInstagramAdGenerator('test_image_download'))
    suite.addTest(TestInstagramAdGenerator('test_generate_ad_with_mock_data'))
    suite.addTest(TestInstagramAdGenerator('test_flask_endpoints'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All debug tests passed!")
    else:
        print(f"⚠️  {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

if __name__ == '__main__':
    run_debug_tests()
