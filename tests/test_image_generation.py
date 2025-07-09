import os
import traceback
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
from PIL import Image
from io import BytesIO
import base64

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)
client = genai.Client(api_key=GEMINI_API_KEY)

def test_image_generation_models():
    """Test various models for image generation with text capabilities"""
    
    # Models to test
    models_to_test = [
        'gemini-2.0-flash-preview-image-generation',  # Current model in the app
        'gemini-1.5-pro',  # May have image generation capabilities
        'gemini-pro-vision',  # May have image capabilities
        'imagen',  # Generic Imagen model name
        'imagen-2.0',  # Newer Imagen model
        'imagen-3.0',  # Latest Imagen model
    ]
    
    # Test prompt with specific text requirements
    test_prompt = """
    Create a professional Instagram advertisement image (1080x1080) for a 'Smartphone Samsung Galaxy S25'.
    Price: $999
    
    Requirements:
    - Professional product photography
    - Beautiful gradient background
    - Include Spanish advertising text on the image that says "NUEVO GALAXY S25"
    - Add the price: $999
    - Include a Spanish call-to-action: "¡COMPRA AHORA!"
    - Professional Instagram ad design with modern typography
    - High quality and visually appealing
    - Square format (1:1 ratio)
    - Text should be very crisp and clearly readable
    - All text must be in perfect Spanish
    """.strip()
    
    results = []
    
    for model_name in models_to_test:
        print(f"\n🔍 Testing model: {model_name}")
        
        try:
            print(f"Attempting generation with {model_name}...")
            
            # Try to generate with response_modalities specified
            try:
                start_time = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=test_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                        temperature=0.2
                    )
                )
                duration = time.time() - start_time
                print(f"✅ Generation completed in {duration:.2f} seconds with specific config")
                
            except Exception as config_error:
                print(f"⚠️ Specific config failed: {config_error}")
                print(f"Trying without config...")
                
                start_time = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=test_prompt
                )
                duration = time.time() - start_time
                print(f"✅ Fallback method succeeded in {duration:.2f} seconds")
            
            # Process and save the image
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                print(f"✅ Response generated successfully")
                
                # Check for image part
                image_found = False
                for i, part in enumerate(response.candidates[0].content.parts):
                    if hasattr(part, 'image') and part.image:
                        print(f"✅ Image found in part {i+1}")
                        image_found = True
                        
                        # Save the generated image
                        image_data = part.image
                        if image_data:
                            try:
                                if hasattr(image_data, 'data'):
                                    image_bytes = image_data.data  # Binary image data
                                else:
                                    # Handle potential alternative formats
                                    image_bytes = base64.b64decode(image_data)
                                
                                # Save the image
                                img_path = f"test_output_{model_name.replace('-', '_')}.jpg"
                                with open(img_path, 'wb') as f:
                                    f.write(image_bytes)
                                print(f"✅ Image saved to {img_path}")
                                
                                results.append({
                                    'model': model_name,
                                    'success': True,
                                    'duration': duration,
                                    'output_path': img_path
                                })
                            except Exception as img_error:
                                print(f"❌ Error saving image: {img_error}")
                
                if not image_found:
                    print("❌ No image found in response")
                    results.append({
                        'model': model_name,
                        'success': False,
                        'error': 'No image in response'
                    })
            else:
                print("❌ No valid content in response")
                results.append({
                    'model': model_name,
                    'success': False,
                    'error': 'No valid content'
                })
                
        except Exception as e:
            print(f"❌ Error with model {model_name}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            results.append({
                'model': model_name,
                'success': False,
                'error': str(e)
            })
    
    # Summary of results
    print("\n====== TEST RESULTS SUMMARY ======")
    
    successful_models = [r['model'] for r in results if r.get('success', False)]
    if successful_models:
        print(f"\n✅ Models that successfully generated images ({len(successful_models)}):")
        for model in successful_models:
            result = next(r for r in results if r['model'] == model)
            print(f"- {model} (generation time: {result.get('duration', 'N/A'):.2f}s)")
            print(f"  Output: {result.get('output_path', 'N/A')}")
    else:
        print("\n❌ No models successfully generated images")
    
    failed_models = [r['model'] for r in results if not r.get('success', False)]
    if failed_models:
        print(f"\n❌ Models that failed ({len(failed_models)}):")
        for model in failed_models:
            result = next(r for r in results if r['model'] == model)
            print(f"- {model}: {result.get('error', 'Unknown error')}")
    
    return successful_models

if __name__ == "__main__":
    test_image_generation_models()
