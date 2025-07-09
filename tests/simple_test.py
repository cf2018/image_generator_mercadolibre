#!/usr/bin/env python3
import os
from google import genai
from google.genai import types


print("Testing Gemini image generation...")

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash-preview-image-generation',
        contents="Create a red square",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"]
        )
    )
    
    print(f"Response received")
    
    if response.candidates:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            for i, part in enumerate(candidate.content.parts):
                print(f"Part {i+1}:")
                if hasattr(part, 'text') and part.text:
                    print(f"  Text: {part.text[:50]}...")
                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"  Has image data: {bool(part.inline_data.data)}")
                    if part.inline_data.data:
                        print(f"  Data length: {len(part.inline_data.data)}")
                        print("SUCCESS: Image data found!")
                        
                        # Save the image
                        import base64
                        if isinstance(part.inline_data.data, str):
                            image_data = base64.b64decode(part.inline_data.data)
                        else:
                            image_data = part.inline_data.data
                        
                        with open('test_output.png', 'wb') as f:
                            f.write(image_data)
                        print("Image saved as test_output.png")
                        exit(0)
    
    print("No image data found")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
