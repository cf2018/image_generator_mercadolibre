import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)

def check_models():
    """Check available Gemini models"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        # First try the current API approach
        print("Attempting to list models through current API...")
        models = client.list_models()
        print(f"Available models: {models}")
    except Exception as e:
        print(f"Error listing models: {e}")
        print("The list_models() method might not be available in this version of the API.")
    
    # Get available models by trying to access model information
    print("\nChecking specific model availability...")
    
    # Models currently used in app
    current_models = [
        'gemini-1.5-flash',  # Vision and text model
        'gemini-2.0-flash-preview-image-generation'  # Image generation model
    ]
    
    # Additional models to check (potential text-to-image models)
    potential_models = [
        'imagen-2.0-flash',
        'imagen-3.0-flash',
        'imagen-2.0-text-to-image',
        'imagen-3.0-text-to-image',
        'imagen-text-to-image',
        'gemini-1.5-pro', 
        'gemini-1.5-flash-text-to-image',
        'gemini-2.0-pro',
        'gemini-pro-vision'
    ]
    
    all_models = current_models + potential_models
    
    for model_name in all_models:
        try:
            print(f"Testing model: {model_name}")
            model = client.models.get_model(model_name)
            print(f"✅ Model {model_name} is available")
            print(f"   - Display name: {getattr(model, 'display_name', 'N/A')}")
            print(f"   - Version: {getattr(model, 'version', 'N/A')}")
            print(f"   - Description: {getattr(model, 'description', 'N/A')[:100]}...")
        except Exception as e:
            print(f"❌ Model {model_name} is not available: {e}")

if __name__ == "__main__":
    check_models()
