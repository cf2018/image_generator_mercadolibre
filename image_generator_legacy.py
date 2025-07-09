import google.generativeai as genai
import os
from PIL import Image
from io import BytesIO
import base64
import json
import re # For extracting potential JSON from Gemini's response

# --- Configuration ---
# Ensure you have your Gemini API key set as an environment variable
# For example, in your terminal:
# export GEMINI_API_KEY="YOUR_API_KEY"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Define models
VISION_MODEL = 'gemini-1.5-flash' # Good for image analysis and text extraction from images
TEXT_MODEL = 'gemini-1.5-flash' # For general text generation (prompts, descriptions)
IMAGE_GENERATION_MODEL = 'gemini-2.0-flash-preview-image-generation' # For creating new images

INPUT_DIR = "input_images"
OUTPUT_DIR = "output_images"

# Create directories if they don't exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions ---

def load_image_as_part(image_path):
    """Loads an image from a file path and returns it as a Gemini Part object."""
    try:
        img = Image.open(image_path)
        img_byte_arr = BytesIO()
        # Ensure the image is in a format Gemini accepts (e.g., JPEG, PNG)
        # Convert to RGB if it's not (e.g., some PNGs can be RGBA)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(img_byte_arr, format='JPEG') # Save as JPEG for common compatibility
        img_byte_arr = img_byte_arr.getvalue()
        return {
            "mime_type": "image/jpeg",
            "data": img_byte_arr

            
        }
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def save_image_from_bytes(image_bytes, output_path):
    """Saves image bytes to a file."""
    try:
        # Write the raw bytes directly to file first for debugging
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"Image saved to: {output_path}")
        
        # Verify the saved image can be opened
        try:
            with Image.open(output_path) as img:
                print(f"Image verified: {img.size} pixels, mode: {img.mode}")
        except Exception as verify_error:
            print(f"Warning: Could not verify saved image: {verify_error}")
            
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        # Try to save with PIL as backup
        try:
            img = Image.open(BytesIO(image_bytes))
            img.save(output_path)
            print(f"Image saved using PIL fallback to: {output_path}")
        except Exception as pil_error:
            print(f"PIL fallback also failed: {pil_error}")

# --- Core Pipeline Functions ---

def describe_image(image_path: str) -> str:
    """
    Analyzes an image and returns a thorough textual description.

    Args:
        image_path: The file path to the image.

    Returns:
        A detailed string description of the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    print(f"Describing image: {image_path}...")
    image_part = load_image_as_part(image_path)
    if image_part is None:
        return "Could not load image for description."

    prompt_parts = [
        image_part,
        "Provide an extremely detailed description of this image. "
        "Include the main subject(s), background, lighting, colors, "
        "composition, style (e.g., realistic, illustrative, abstract), "
        "any text visible (transcribe it), and the overall mood or feeling. "
        "Identify any objects, people, or brand elements clearly. "
        "Be as comprehensive as possible, as this description will be used to conceptually "
        "edit and recreate a similar image with new elements."
    ]

    model = genai.GenerativeModel(VISION_MODEL)
    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"Error describing image with Gemini: {e}")
        return f"Failed to describe image due to an API error: {e}"

def generate_edited_image_prompt(
    original_description: str,
    new_brand_details: dict,
    new_message_details: dict,
    specific_visual_edits: list = None
) -> str:
    """
    Generates a detailed prompt for a new image based on an original description
    and new brand/message details.

    Args:
        original_description: The detailed description of the original image.
        new_brand_details: A dictionary with 'name', 'colors', 'logo_style', 'placement_idea'.
                           Example: {'name': 'EcoFuture', 'colors': 'green and white',
                                     'logo_style': 'modern leaf icon', 'placement_idea': 'top right corner'}
        new_message_details: A dictionary with 'headline', 'body_text_concept', 'cta_text'.
                             Example: {'headline': 'Sustainable Living',
                                       'body_text_concept': 'emphasize eco-friendly products',
                                       'cta_text': 'Discover More'}
        specific_visual_edits: An optional list of strings for additional visual changes.
                               Example: ["replace old product with a sleek, minimalist water bottle", "add a lush, natural environment"]

    Returns:
        A comprehensive string prompt for the image generation model.
    """
    print("Generating new image prompt...")
    edits = specific_visual_edits if specific_visual_edits else []
    edits_str = "\n".join([f"- {edit}" for edit in edits]) if edits else "No specific additional visual edits."

    prompt = f"""
    You are an expert image prompt engineer for advertising. Your task is to create a new image generation prompt.
    This new image MUST be visually IDENTICAL in style, composition, layout, and mood to the ORIGINAL IMAGE described below,
    but with ALL brand elements replaced with a NEW BRAND and NEW MESSAGE.

    --- ORIGINAL IMAGE DESCRIPTION ---
    {original_description}
    --- END ORIGINAL IMAGE DESCRIPTION ---

    --- NEW AD DETAILS ---
    Brand Name: {new_brand_details.get('name', 'New Brand')}
    Brand Colors: {new_brand_details.get('colors', 'a vibrant, modern palette')}
    Logo Style: {new_brand_details.get('logo_style', 'a clean, symbolic icon')}
    Logo Placement Idea: {new_brand_details.get('placement_idea', 'subtly integrated into the scene')}
    New Headline Concept: "{new_message_details.get('headline', 'New Opportunity')}"
    New Body Text Concept: "{new_message_details.get('body_text_concept', 'focused on innovation and user benefits')}"
    New Call-to-Action Text: "{new_message_details.get('cta_text', 'Learn More')}"
    Specific Visual Edits:
    {edits_str}
    --- END NEW AD DETAILS ---

    CRITICAL INSTRUCTIONS FOR THE NEW IMAGE:
    1.  **MAINTAIN EXACT COMPOSITION**: Keep the same layout, positioning, perspective, and overall visual structure as the original image.
    2.  **PRESERVE STYLE**: Match the lighting, color tone, artistic style, and mood exactly.
    3.  **REPLACE ONLY BRAND ELEMENTS**: Remove all original brand logos, text, and brand-specific colors. Replace with the new brand's aesthetic seamlessly.
    4.  **KEEP SAME VISUAL HIERARCHY**: If the original has text in certain positions, place implied new messaging in the same positions.
    5.  **MATCH QUALITY LEVEL**: Maintain the same level of professionalism and visual quality as the original.

    Generate a detailed image generation prompt that will recreate the EXACT same visual structure and style as the original,
    but featuring the new brand. Be very specific about maintaining the original's composition, layout, and visual elements
    while only changing the brand-related content.
    """
    model = genai.GenerativeModel(TEXT_MODEL)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating image prompt with Gemini: {e}")
        return f"Failed to generate prompt due to an API error: {e}"

def create_image(generation_prompt: str, output_image_path: str):
    """
    Generates an image based on a prompt and saves it to a specified path.

    Args:
        generation_prompt: The detailed text prompt for image generation.
        output_image_path: The file path where the generated image will be saved.

    Returns:
        The file path of the saved image, or None if generation failed.
    """
    print(f"Creating image with prompt: '{generation_prompt[:100]}...'")
    model = genai.GenerativeModel(IMAGE_GENERATION_MODEL)
    try:
        # Try different ways to specify response modalities
        try:
            # Method 1: Try with response_modalities in generation_config
            response = model.generate_content(
                generation_prompt,
                generation_config={
                    "response_modalities": ["IMAGE", "TEXT"]
                }
            )
        except Exception as config_error:
            print(f"Config method failed: {config_error}")
            # Method 2: Try without explicit config (model should default to IMAGE generation)
            response = model.generate_content(generation_prompt)

        # Check if the response contains image data
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Debug: print the type and first few bytes
                        print(f"Image data type: {type(part.inline_data.data)}")
                        print(f"Image data length: {len(part.inline_data.data) if hasattr(part.inline_data.data, '__len__') else 'unknown'}")
                        
                        # Try to decode the image data
                        try:
                            if isinstance(part.inline_data.data, str):
                                # If it's a base64 string, decode it
                                image_data = base64.b64decode(part.inline_data.data)
                            else:
                                # If it's already bytes, use it directly
                                image_data = part.inline_data.data
                            
                            save_image_from_bytes(image_data, output_image_path)
                            return output_image_path
                        except Exception as decode_error:
                            print(f"Error decoding image data: {decode_error}")
                            continue
        
        print("No image data received from Gemini.")
        return None
    except Exception as e:
        print(f"Error creating image with Gemini: {e}")
        print(f"Gemini response content (if available): {getattr(e, 'text', 'N/A')}")
        return None

# --- Main Execution for Testing ---

if __name__ == "__main__":
    # --- Step 0: Use the actual Spotify ad image ---
    original_input_image_name = "spotify_ad.png"  # Use the actual Spotify ad
    original_input_image_path = os.path.join(INPUT_DIR, original_input_image_name)

    if not os.path.exists(original_input_image_path):
        print(f"ERROR: Could not find the original ad image at: {original_input_image_path}")
        print("Please ensure 'spotify_ad.png' is in the 'input_images' directory.")
        print("Available files in input_images:")
        try:
            files = os.listdir(INPUT_DIR)
            for file in files:
                print(f"  - {file}")
        except:
            print("  Could not list directory contents")
        exit(1)

    # --- Pipeline Step 1: Describe the original image ---
    print("\n--- Step 1: Describing the Original Spotify Ad ---")
    original_image_description = describe_image(original_input_image_path)
    print("Original Image Description:")
    print(original_image_description)

    # --- Step 2: Define new brand and message details ---
    print("\n--- Step 2: Defining New Brand and Message ---")
    new_brand_details = {
        'name': 'Quantum Leap Academy',
        'colors': 'deep blues and vibrant purples',
        'logo_style': 'abstract symbol of interconnected nodes or a stylized lightwave',
        'placement_idea': 'subtly integrated into the bottom left corner, or as a watermark effect'
    }
    new_message_details = {
        'headline': 'Unlock Your Future Potential',
        'body_text_concept': 'emphasize cutting-edge online education, career growth, and expert-led courses in AI and data science.',
        'cta_text': 'Enroll Now'
    }
    specific_edits = [
        "replace any old product with a futuristic, holographic learning interface or a person engaged with a high-tech tablet",
        "background should evoke a sense of innovation, knowledge, or limitless possibilities, like a starry sky with data visualizations or a sleek modern learning environment",
        "ensure no old text is visible, and no human faces from the original if present" # Reinforce
    ]
    print("New Brand Details:", new_brand_details)
    print("New Message Details:", new_message_details)
    print("Specific Edits:", specific_edits)

    # --- Pipeline Step 3: Generate the prompt for the new image ---
    print("\n--- Step 3: Generating the New Image Prompt ---")
    generated_prompt = generate_edited_image_prompt(
        original_image_description,
        new_brand_details,
        new_message_details,
        specific_edits
    )
    print("Generated Image Prompt:")
    print(generated_prompt)

    # --- Pipeline Step 4: Create the new image ---
    print("\n--- Step 4: Creating the New Image ---")
    output_image_name = "new_ad_image.png"
    output_image_path = os.path.join(OUTPUT_DIR, output_image_name)

    created_image_path = create_image(generated_prompt, output_image_path)

    if created_image_path:
        print(f"\nSuccessfully generated new ad image at: {created_image_path}")
    else:
        print("\nFailed to generate new ad image.")