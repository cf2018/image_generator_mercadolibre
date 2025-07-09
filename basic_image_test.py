#!/usr/bin/env python3
"""
Basic test of the Gemini API for image generation.
"""

import os
from google import genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Gemini API key
API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)

# Initialize Gemini
print(f"Initializing Gemini with API key: {API_KEY[:5]}...{API_KEY[-4:]}")
genai.configure(api_key=API_KEY)

# Current model
MODEL = "gemini-2.0-flash-preview-image-generation"

def main():
    try:
        print(f"Testing model: {MODEL}")
        
        # Create model
        model = genai.GenerativeModel(MODEL)
        
        # Simple prompt for image generation
        prompt = "Create an image of a coffee machine with text saying 'CAFÉ PREMIUM'"
        
        print("Sending request...")
        response = model.generate_content(prompt)
        
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        # Check for image in response
        if hasattr(response, "candidates") and response.candidates:
            print(f"Found {len(response.candidates)} candidates")
            
            for i, candidate in enumerate(response.candidates):
                print(f"Candidate {i+1}:")
                
                if hasattr(candidate, "content") and candidate.content:
                    print(f"  Content: {candidate.content}")
                    
                    for j, part in enumerate(candidate.content.parts):
                        print(f"  Part {j+1} type: {type(part)}")
                        
                        if hasattr(part, "mime_type"):
                            print(f"  Mime type: {part.mime_type}")
                            
                            if part.mime_type and part.mime_type.startswith("image/"):
                                # Save image
                                timestamp = int(time.time())
                                filename = f"gemini_test_{timestamp}.png"
                                
                                with open(filename, "wb") as f:
                                    f.write(part.data)
                                
                                print(f"✅ Image saved as {filename}")
                            else:
                                print(f"  Content: {part.text[:100]}...")
        else:
            print("No candidates in response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
