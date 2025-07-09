import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from playwright.sync_api import sync_playwright
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
import re
import numpy as np
from collections import Counter

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
TEMP_FOLDER = 'temp'

# Create necessary directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Gemini Configuration
GEMINI_API_KEY = (
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('GOOGLE_API_KEY') 
)
client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini Models - Using models that work best for each task
VISION_MODEL = 'gemini-1.5-flash'  # Reliable vision model for analyzing images
TEXT_MODEL = 'gemini-1.5-flash'    # Reliable text model for ad concepts
IMAGE_GENERATION_MODEL = 'gemini-2.0-flash-preview-image-generation'  # For clean product images (text overlay mode)
TEXT_TO_IMAGE_MODEL = 'gemini-2.0-flash-preview-image-generation'  # For generating images with text (AI text mode) - UPDATED: Works for both!

# Fallback model if primary model fails
FALLBACK_TEXT_TO_IMAGE_MODEL = 'gemini-2.0-flash-preview-image-generation'

class MercadoLibreScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def setup_browser(self):
        """Setup Playwright browser"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-logging',
                    '--disable-in-process-stack-traces',
                    '--disable-web-security',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
                }
            )
            # Set longer default timeouts
            self.context.set_default_timeout(30000)
            self.page = self.context.new_page()
            print("Playwright browser setup successful")
            
        except Exception as e:
            print(f"Error setting up Playwright browser: {e}")
            raise Exception("Could not setup browser. Please install Playwright browsers with: playwright install")
    
    def scrape_product(self, url):
        """Scrape product information from MercadoLibre URL"""
        if not self.page:
            self.setup_browser()
        
        try:
            print(f"Navigating to: {url}")
            # Use a longer timeout and wait for the main content
            self.page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            # Wait for critical elements with shorter timeouts
            try:
                # Wait for either the title or price to appear
                self.page.wait_for_selector('h1, .andes-money-amount__fraction, .ui-pdp-price__fraction', timeout=10000)
                print("Page content loaded successfully")
            except Exception as wait_error:
                print(f"Warning: Timeout waiting for elements, proceeding anyway: {wait_error}")
            
            # Wait a bit more for dynamic content to load
            self.page.wait_for_timeout(2000)
            
            # Extract product information
            product_data = {
                'title': self._get_title(),
                'price': self._get_price(),
                'description': self._get_description(),
                'images': self._get_images(),
                'url': url
            }
            
            return product_data
            
        except Exception as e:
            print(f"Error scraping product: {e}")
            # Try to provide more specific error information
            if "Timeout" in str(e):
                print(f"Page loading timeout - MercadoLibre may be blocking requests or server is slow")
            return None
    
    def _get_title(self):
        """Extract product title"""
        try:
            title_selectors = [
                'h1.ui-pdp-title',
                'h1[data-testid="product-title"]',
                '.ui-pdp-title',
                'h1',
                '.item-title h1',
                '[data-testid="product-title"]'
            ]
            
            for selector in title_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        title = element.inner_text().strip()
                        if title:
                            print(f"Found title: {title}")
                            return title
                except Exception:
                    continue
            
            print("Title not found, returning default")
            return "Product Title Not Found"
            
        except Exception as e:
            print(f"Error getting title: {e}")
            return "Error getting title"
    
    def _get_price(self):
        """Extract product price"""
        try:
            price_selectors = [
                '.andes-money-amount__fraction',
                '.ui-pdp-price__fraction',
                '[data-testid="price-fraction"]',
                '.price-tag-fraction',
                '.price-tag-amount',
                '.ui-pdp-price .andes-money-amount__fraction'
            ]
            
            for selector in price_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        price = element.inner_text().strip()
                        if price:
                            print(f"Found price: {price}")
                            return price
                except Exception:
                    continue
            
            print("Price not found, returning default")
            return "Price Not Found"
            
        except Exception as e:
            print(f"Error getting price: {e}")
            return "Error getting price"
    
    def _get_description(self):
        """Extract product description"""
        try:
            description_selectors = [
                '.ui-pdp-description__content',
                '[data-testid="product-description"]',
                '.item-description',
                '.ui-vpp-strikethrough-text',
                '.ui-pdp-description p',
                '.item-description p'
            ]
            
            for selector in description_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        description = element.inner_text().strip()[:500]  # Limit description length
                        if description:
                            print(f"Found description: {description[:100]}...")
                            return description
                except Exception:
                    continue
            
            print("Description not found, returning default")
            return "Description not available"
            
        except Exception as e:
            print(f"Error getting description: {e}")
            return "Error getting description"
    
    def _get_images(self):
        """Extract product images"""
        try:
            image_urls = []
            
            # Try different selectors for images
            image_selectors = [
                '.ui-pdp-gallery img',
                '.ui-pdp-image img',
                '[data-testid="product-image"] img',
                '.gallery-image img',
                '.ui-pdp-gallery .ui-pdp-image img',
                '.gallery img'
            ]
            
            for selector in image_selectors:
                try:
                    images = self.page.query_selector_all(selector)
                    for img in images:
                        src = img.get_attribute('src') or img.get_attribute('data-src')
                        if src and src.startswith('http') and 'logo' not in src.lower():
                            image_urls.append(src)
                    
                    if image_urls:
                        break
                        
                except Exception:
                    continue
            
            # Remove duplicates and limit to first 5 images
            unique_urls = list(dict.fromkeys(image_urls))[:5]
            print(f"Found {len(unique_urls)} images")
            return unique_urls
            
        except Exception as e:
            print(f"Error getting images: {e}")
            return []
    
    def close(self):
        """Close the browser and playwright"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("Browser closed successfully")
        except Exception as e:
            print(f"Error closing browser: {e}")

class InstagramAdGenerator:
    def __init__(self):
        pass
    
    def download_image(self, url):
        """Download image from URL"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                return BytesIO(response.content)
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def load_image_as_part(self, image_data):
        """Convert image data to Gemini part format"""
        try:
            if isinstance(image_data, BytesIO):
                img = Image.open(image_data)
            else:
                img = Image.open(image_data)
            
            img_byte_arr = BytesIO()
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return {
                "mime_type": "image/jpeg",
                "data": img_byte_arr
            }
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    def add_text_overlay(self, image_data, product_data, ad_concept):
        """Add Spanish text overlay to the generated image"""
        try:
            # Open the generated image
            img = Image.open(BytesIO(image_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create drawing context
            draw = ImageDraw.Draw(img)
            
            # Try to load good fonts with different sizes
            try:
                # Try to find system fonts
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
                price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95) 
                desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
                cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                # Fallback to default font with larger sizes
                title_font = ImageFont.load_default()
                price_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
                cta_font = ImageFont.load_default()
            
            # Prepare Spanish text - clean and accurate
            title = product_data['title']
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Clean the price display
            price_raw = product_data['price']
            # Format price nicely
            if '.' in price_raw:
                price = f"${price_raw}"
            else:
                price = f"${price_raw}"
            
            # Create professional Spanish marketing text
            cta = "¡COMPRA AHORA!"
            subtitle = "Diseño único y funcional"
            
            # Image dimensions
            width, height = img.size
            
            # Add professional gradient overlays for text readability
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Top gradient overlay for title area
            for i in range(140):
                alpha = int(160 * (140 - i) / 140)  # Gradient effect
                overlay_draw.rectangle([(0, i), (width, i+1)], fill=(0, 0, 0, alpha))
            
            # Bottom gradient overlay for price and CTA
            for i in range(180):
                alpha = int(160 * i / 180)  # Gradient effect
                overlay_draw.rectangle([(0, height-180+i), (width, height-180+i+1)], fill=(0, 0, 0, alpha))
            
            # Blend overlay with image
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Add title text (top) - wrapped if needed
            lines = []
            words = title.split()
            current_line = ""
            
            for word in words:
                test_line = f"{current_line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=title_font)
                if bbox[2] - bbox[0] <= width - 40:  # Leave 20px margin on each side
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Draw title lines
            y_offset = 25
            for line in lines[:2]:  # Max 2 lines
                draw.text((20, y_offset), line, font=title_font, fill='white', stroke_width=2, stroke_fill='black')
                y_offset += 55
            
            # Add subtitle
            draw.text((20, y_offset + 10), subtitle, font=desc_font, fill='#E0E0E0', stroke_width=1, stroke_fill='black')
            
            # Add price (bottom left) - large and prominent
            price_bbox = draw.textbbox((0, 0), price, font=price_font)
            draw.text((20, height-150), price, font=price_font, fill='#FFD700', stroke_width=3, stroke_fill='black')  # Gold color
            
            # Add CTA (bottom right) - professional button style
            cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
            cta_width = cta_bbox[2] - cta_bbox[0]
            cta_height = cta_bbox[3] - cta_bbox[1]
            
            # Draw CTA button background
            button_padding = 15
            button_x = width - cta_width - 40 - button_padding
            button_y = height - 100 - button_padding
            button_width = cta_width + (button_padding * 2)
            button_height = cta_height + (button_padding * 2)
            
            # Button with rounded corners effect
            overlay_draw = ImageDraw.Draw(overlay)
            draw.rectangle([button_x, button_y, button_x + button_width, button_y + button_height], 
                          fill='#FF6B35', outline='white', width=3)  # Orange button
            
            # Add CTA text
            draw.text((button_x + button_padding, button_y + button_padding), cta, 
                     font=cta_font, fill='white', stroke_width=2, stroke_fill='black')
            
            # Convert back to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            print(f"❌ Error adding text overlay: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Return original image if text overlay fails
            return image_data
        """Convert image data to Gemini part format"""
        try:
            if isinstance(image_data, BytesIO):
                img = Image.open(image_data)
            else:
                img = Image.open(image_data)
            
            img_byte_arr = BytesIO()
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return {
                "mime_type": "image/jpeg",
                "data": img_byte_arr
            }
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def analyze_product_info(self, product_data):
        """Analyze product information to create ad concept"""
        print(f"💡 Analyzing product info for ad concept...")
        print(f"Title: {product_data.get('title', 'N/A')}")
        print(f"Price: {product_data.get('price', 'N/A')}")
        print(f"Description length: {len(product_data.get('description', ''))}")
        
        prompt = f"""
        Eres un experto en marketing digital que habla español nativo. Tu tarea es analizar este producto de MercadoLibre y crear un concepto publicitario para Instagram.

        INFORMACIÓN DEL PRODUCTO:
        Título del producto: {product_data['title']}
        Precio exacto: {product_data['price']}
        Descripción: {product_data['description']}
        
        INSTRUCCIONES ESPECÍFICAS:
        - Responde ÚNICAMENTE en español de España o Latinoamérica
        - Crea un concepto de anuncio de Instagram profesional
        - Usa EXACTAMENTE el precio proporcionado: {product_data['price']}
        - Asegúrate de que todo el texto esté en español correcto sin errores
        
        Incluye en tu respuesta:
        1. Un titular llamativo en español (máximo 25 caracteres)
        2. Texto descriptivo atractivo en español (máximo 100 caracteres)  
        3. Texto de llamada a la acción en español
        4. Elementos visuales a destacar
        5. Sugerencias de esquema de colores
        6. Sugerencias de diseño para formato Instagram (1080x1080)
        
        IMPORTANTE: Todo debe estar en español perfecto, dirigido a consumidores hispanohablantes.
        """
        
        print(f"📤 Sending analysis request to Gemini...")
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Lower temperature for more accurate text
                    max_output_tokens=1024,
                    candidate_count=1,
                    system_instruction="Eres un experto en marketing digital hispanohablante. Respondes únicamente en español perfecto, sin errores ortográficos. Creas conceptos publicitarios para consumidores de habla hispana."
                )
            )
            print(f"✅ Ad concept analysis complete")
            print(f"Concept preview: {response.text[:100]}...")
            return response.text
        except Exception as e:
            print(f"❌ Error analyzing product info: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Detect model overload (503 or 'overloaded' in error)
            err_str = str(e).lower()
            if '503' in err_str or 'overload' in err_str or 'unavailable' in err_str:
                return "MODEL_OVERLOADED_ERROR"
            return "Error creating ad concept"
    
    def extract_color_info(self, product_data, image_description=""):
        """Extract color information from product data to create complementary backgrounds"""
        
        # Combine all text sources
        text_sources = [
            product_data.get('title', ''),
            product_data.get('description', ''),
            image_description
        ]
        combined_text = ' '.join(text_sources).lower()
        
        # Enhanced Spanish color mappings for sophisticated backgrounds
        color_backgrounds = {
            # Product colors -> Background suggestions with styling
            'blanco': 'soft gradient from light grey to cream with subtle blue highlights and modern geometric elements',
            'negro': 'elegant dark gradient with charcoal tones, silver accents, and sophisticated lighting',
            'azul': 'serene blue gradient with cloud-like textures and professional lighting',
            'rojo': 'warm crimson gradient fading to cream with golden accents',
            'verde': 'natural sage green gradient with organic textures and soft lighting',
            'amarillo': 'sunny yellow gradient with warm cream tones and radial lighting',
            'rosa': 'soft rose gradient with pearl highlights and dreamy atmosphere',
            'morado': 'royal purple gradient fading to lavender with elegant accents',
            'naranja': 'vibrant orange gradient with warm amber tones and dynamic lighting',
            'gris': 'sophisticated grey gradient with silver highlights and modern aesthetic',
            'marrón': 'rich brown gradient with coffee tones and warm golden accents',
            'beige': 'neutral beige gradient with cream highlights and soft shadows',
            'dorado': 'luxurious gold gradient with champagne tones and premium lighting',
            'plateado': 'metallic silver gradient with chrome accents and professional finish',
            'metalico': 'industrial metallic gradient with brushed steel textures and modern lighting',
            
            # Additional product-specific backgrounds
            'madera': 'warm wooden texture gradient with natural grain and soft lighting',
            'cuero': 'rich leather texture gradient with brown tones and luxury feel',
            'vidrio': 'crystal clear gradient with subtle reflections and modern lighting',
            'plastico': 'clean modern gradient with smooth textures and contemporary feel',
            'tela': 'soft fabric texture gradient with textile patterns and cozy lighting'
        }
        
        # Look for color mentions with priority scoring
        detected_colors = []
        for color, background in color_backgrounds.items():
            if color in combined_text:
                # Count occurrences for priority
                count = combined_text.count(color)
                detected_colors.append((count, color, background))
        
        # Sort by frequency and use the most mentioned color
        if detected_colors:
            detected_colors.sort(reverse=True)  # Most frequent first
            count, color, background = detected_colors[0]
            print(f"🎨 Detected primary color '{color}' (mentioned {count} times)")
            print(f"   Background style: {background[:60]}...")
            return background
        else:
            # Default sophisticated background for unknown colors
            print(f"🎨 No specific color detected -> Using elegant default background")
            return "sophisticated gradient background with soft curves, gentle shadows, and modern professional lighting that complements any product"
    
    def extract_dominant_colors(self, image_data, num_colors=5):
        """Extract dominant colors from an image"""
        try:
            # Open image from bytes
            image = Image.open(BytesIO(image_data))
            
            # Resize for faster processing
            image = image.resize((150, 150))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get pixel data
            pixels = np.array(image)
            pixels = pixels.reshape(-1, 3)
            
            # Remove white/very light pixels (background)
            mask = ~((pixels[:, 0] > 240) & (pixels[:, 1] > 240) & (pixels[:, 2] > 240))
            filtered_pixels = pixels[mask]
            
            if len(filtered_pixels) == 0:
                return ['#333333', '#666666', '#999999']  # Default colors
            
            # Use K-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=min(num_colors, len(filtered_pixels)), random_state=42, n_init=10)
            kmeans.fit(filtered_pixels)
            
            # Get the colors and convert to hex
            colors = []
            for color in kmeans.cluster_centers_:
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(color[0]), int(color[1]), int(color[2]))
                colors.append(hex_color)
            
            return colors
            
        except Exception as e:
            print(f"❌ Error extracting colors: {e}")
            # Fallback colors
            return ['#4a90e2', '#7b68ee', '#50c878']
    
    def generate_color_palette(self, dominant_colors):
        """Generate a professional color palette for backgrounds"""
        try:
            # Convert hex to RGB for calculations
            def hex_to_rgb(hex_color):
                return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
            
            def rgb_to_hex(rgb):
                return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
            
            # Get the most prominent color
            main_color = dominant_colors[0]
            main_rgb = hex_to_rgb(main_color)
            
            # Generate complementary and analogous colors
            palette = {
                'primary': main_color,
                'light': rgb_to_hex((min(255, main_rgb[0] + 60), min(255, main_rgb[1] + 60), min(255, main_rgb[2] + 60))),
                'dark': rgb_to_hex((max(0, main_rgb[0] - 40), max(0, main_rgb[1] - 40), max(0, main_rgb[2] - 40))),
                'complement': rgb_to_hex((255 - main_rgb[0], 255 - main_rgb[1], 255 - main_rgb[2])),
                'neutral': '#f8f9fa'
            }
            
            return palette
            
        except Exception as e:
            print(f"❌ Error generating palette: {e}")
            return {
                'primary': '#4a90e2',
                'light': '#87ceeb', 
                'dark': '#2c5aa0',
                'complement': '#e24a4a',
                'neutral': '#f8f9fa'
            }
    
    def create_background_prompt(self, product_title, image_description, color_palette):
        """Create a sophisticated background prompt based on colors"""
        
        background_styles = [
            f"Modern gradient background from {color_palette['light']} to {color_palette['primary']}, subtle geometric patterns",
            f"Professional studio setup with {color_palette['primary']} accent lighting and soft shadows",
            f"Contemporary minimalist background with {color_palette['primary']} and {color_palette['light']} color blocking",
            f"Elegant backdrop with {color_palette['primary']} gradient and subtle texture, modern lighting",
            f"Stylish environment with {color_palette['primary']} and {color_palette['neutral']} color scheme, professional photography"
        ]
        
        # Select style based on product type (simple heuristic)
        if any(word in product_title.lower() for word in ['ropa', 'clothing', 'fashion', 'shirt', 'vestido']):
            style = background_styles[0]  # Gradient for fashion
        elif any(word in product_title.lower() for word in ['tech', 'electronic', 'phone', 'laptop']):
            style = background_styles[1]  # Studio for tech
        elif any(word in product_title.lower() for word in ['home', 'hogar', 'furniture', 'mueble']):
            style = background_styles[2]  # Minimalist for home
        else:
            style = background_styles[3]  # Elegant for general products
        
        return style
    
    def generate_instagram_ad(self, product_data, ad_concept, primary_image_urls=None, use_text_overlay=True):
        """Generate Instagram ad image using Gemini with selected reference images"""
        
        print(f"🎨 Starting Instagram ad generation...")
        print(f"Product: {product_data.get('title', 'Unknown')}")
        print(f"Reference images: {len(primary_image_urls) if primary_image_urls else 0}")
        print(f"Text overlay mode: {'Programmatic' if use_text_overlay else 'AI-generated'}")
        
        # Analyze selected images to create a comprehensive description
        combined_image_description = ""
        processed_images = []
        
        if primary_image_urls:
            print(f"📸 Processing {len(primary_image_urls)} selected reference images...")
            
            for i, image_url in enumerate(primary_image_urls):
                print(f"🔍 Analyzing image {i+1}/{len(primary_image_urls)}...")
                image_data = self.download_image(image_url)
                
                if image_data:
                    print(f"✅ Image {i+1} downloaded successfully")
                    image_part = self.load_image_as_part(image_data)
                    
                    if image_part:
                        print(f"✅ Image {i+1} converted to Gemini format")
                        processed_images.append(image_part)
                        
                        # Analyze each image individually
                        analysis_prompt = f"Describe esta imagen del producto en español, enfocándote en: apariencia, colores, materiales, estilo, posición y características notables que deben preservarse en un anuncio publicitario."
                        
                        try:
                            print(f"🔍 Analyzing image {i+1} with Gemini Vision...")
                            image_content = types.Part.from_bytes(
                                data=image_part["data"], 
                                mime_type=image_part["mime_type"]
                            )
                            response = client.models.generate_content(
                                model=VISION_MODEL,
                                contents=[analysis_prompt, image_content]
                            )
                            image_description = response.text
                            print(f"✅ Image {i+1} analysis complete: {image_description[:100]}...")
                            
                            # Combine descriptions
                            if combined_image_description:
                                combined_image_description += f" Además, {image_description}"
                            else:
                                combined_image_description = image_description
                                
                        except Exception as e:
                            print(f"❌ Error analyzing image {i+1}: {e}")
                    else:
                        print(f"❌ Failed to convert image {i+1} to Gemini format")
                else:
                    print(f"❌ Failed to download image {i+1} from URL: {image_url}")
        
        # Extract color information for background styling
        color_palette = None
        if primary_image_urls and len(primary_image_urls) > 0:
            print(f"🎨 Extracting colors from primary image for background styling...")
            try:
                # Use the first selected image for color extraction
                primary_image_data = self.download_image(primary_image_urls[0])
                if primary_image_data:
                    # Convert BytesIO to bytes for color extraction
                    if hasattr(primary_image_data, 'getvalue'):
                        image_bytes = primary_image_data.getvalue()
                    else:
                        image_bytes = primary_image_data
                    dominant_colors = self.extract_dominant_colors(image_bytes)
                    color_palette = self.generate_color_palette(dominant_colors)
                    print(f"✅ Color palette extracted: {color_palette}")
                else:
                    print(f"❌ Could not download image for color extraction")
            except Exception as e:
                print(f"❌ Error extracting colors: {e}")
        
        # Create background style prompt
        background_style = ""
        if color_palette:
            background_style = self.create_background_prompt(
                product_data.get('title', ''), 
                combined_image_description, 
                color_palette
            )
            print(f"🎨 Generated background style: {background_style}")
        
        # Generate enhanced prompt based on selected images and text overlay preference
        if use_text_overlay:
            # Mode 1: Enhanced image for programmatic text overlay
            if combined_image_description and background_style:
                generation_prompt = f"""
                Professional studio photograph of {product_data['title']}. 
                
                IMPORTANT: The product must match this exact description: {combined_image_description[:350]}
                
                Requirements:
                - Same product as described above with identical visual characteristics
                - {background_style}
                - Product prominently featured and well-lit in center
                - Professional studio lighting with soft shadows
                - High quality product photography
                - Square format (1:1 ratio)
                - Instagram-ready composition
                - No text or watermarks on the image
                - Sophisticated and modern aesthetic
                - Clean, professional look suitable for advertising
                """.strip()
            elif combined_image_description:
                generation_prompt = f"""
                Professional studio photograph of {product_data['title']}. 
                
                IMPORTANT: The product must match this exact description: {combined_image_description[:400]}
                
                Requirements:
                - Same product as described above with identical visual characteristics
                - Stylish gradient background with colors matching the product
                - Product prominently featured and well-lit
                - Professional studio lighting
                - High quality product photography
                - Square format (1:1 ratio)
                - No text or watermarks
                """.strip()
            else:
                generation_prompt = f"""
                Professional studio photograph of {product_data['title']}. 
                Modern gradient background with colors that complement the product.
                Product prominently featured with professional lighting.
                Square format. High quality. Instagram-ready composition.
                No text on the image.
                """.strip()
        else:
            # Mode 2: AI-generated text on image with styled background
            title = product_data.get('title', '')
            price = product_data.get('price', '')
            
            if combined_image_description and background_style:
                generation_prompt = f"""
                Create a professional Instagram advertisement image (1080x1080) for {title}.
                
                Product details: {combined_image_description[:300]}
                Price: {price}
                
                Requirements:
                - Show the exact product as described above
                - {background_style}
                - Include Spanish advertising text on the image
                - Add the price: {price}
                - Include an attractive Spanish call-to-action
                - Use professional Instagram ad design
                - Modern, eye-catching layout
                - High quality and visually appealing
                - Square format (1:1 ratio)
                - All text must be in perfect Spanish
                """.strip()
            else:
                generation_prompt = f"""
                Create a professional Instagram advertisement image (1080x1080) for {title}.
                Price: {price}
                
                Requirements:
                - Professional product photography with stylish background
                - Include Spanish advertising text on the image
                - Add the price: {price}
                - Include an attractive Spanish call-to-action
                - Use professional Instagram ad design
                - Modern, eye-catching layout
                - High quality and visually appealing
                - Square format (1:1 ratio)
                - All text must be in perfect Spanish
                """.strip()
            title = product_data.get('title', '')
            price = product_data.get('price', '')
            
            if combined_image_description:
                generation_prompt = f"""
                Create a professional Instagram advertisement image (1080x1080) for {title}.
                
                Product details: {combined_image_description[:250]}
                Price: {price}
                
                Design Requirements:
                - Show the exact product as described above
                - Beautiful {background_style} behind the product
                - Include Spanish advertising text on the image
                - Add the price: {price}
                - Include an attractive Spanish call-to-action
                - Professional Instagram ad design with modern typography
                - High quality and visually appealing
                - Square format (1:1 ratio)
                - All text must be in perfect Spanish
                - Sophisticated color scheme that complements the product
                """.strip()
            else:
                generation_prompt = f"""
                Create a professional Instagram advertisement image (1080x1080) for {title}.
                Price: {price}
                
                Design Requirements:
                - Professional product photography
                - Beautiful {background_style} behind the product
                - Include Spanish advertising text on the image
                - Add the price: {price}
                - Include an attractive Spanish call-to-action
                - Professional Instagram ad design with modern typography
                - High quality and visually appealing
                - Square format (1:1 ratio)
                - All text must be in perfect Spanish
                - Sophisticated and modern aesthetic
                """.strip()
        
        # Choose the appropriate model based on text overlay preference
        if use_text_overlay:
            # Mode 1: Use image generation model for clean images (no text)
            selected_model = IMAGE_GENERATION_MODEL
            print(f"🎨 Mode: Clean image generation (for text overlay)")
        else:
            # Mode 2: Use text-to-image model for images with text
            selected_model = TEXT_TO_IMAGE_MODEL
            print(f"🤖 Mode: Text-to-image generation (AI text)")
        
        # Track if we used a fallback model
        used_fallback = False
        
        print(f"🚀 Generating ad with enhanced prompt (length: {len(generation_prompt)} characters)")
        print(f"Using model: {selected_model}")
        
        try:
            print(f"📤 Sending request to Gemini...")
            
            # Use different generation approaches based on the model
            if use_text_overlay:
                # Mode 1: Clean image generation (existing approach)
                try:
                    response = client.models.generate_content(
                        model=selected_model,
                        contents=generation_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                            temperature=0.1,  # Low temperature for more consistent results
                            max_output_tokens=2048,
                            candidate_count=1
                        )
                    )
                    print(f"✅ Clean image generation request sent successfully")
                except Exception as config_error:
                    print(f"⚠️  Specific config failed: {config_error}")
                    print(f"🔄 Trying without config...")
                    response = client.models.generate_content(
                        model=selected_model,
                        contents=generation_prompt
                    )
                    print(f"✅ Fallback method succeeded")
            else:
                # Mode 2: Text-to-image generation
                try:
                    print(f"🔄 Attempting text-to-image generation with {selected_model}...")
                    response = client.models.generate_content(
                        model=selected_model,
                        contents=generation_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                            temperature=0.3,  # Slightly higher for creative text placement
                            max_output_tokens=2048,
                            candidate_count=1
                        )
                    )
                    print(f"✅ Text-to-image generation request sent successfully")
                except Exception as text_to_image_error:
                    print(f"⚠️  Text-to-image model failed: {text_to_image_error}")
                    print(f"🔄 Falling back to image generation model with modified prompt...")
                    
                    used_fallback = True  # Track that we used fallback
                    
                    # Modify the prompt to be more suitable for the image generation model
                    # Remove text generation requirements and focus on image with overlay approach
                    fallback_prompt = f"""
                    Professional studio photograph of {product_data.get('title', '')}.
                    
                    {f"Product details: {combined_image_description[:300]}" if combined_image_description else ""}
                    
                    Requirements:
                    - Show the exact product as described
                    - {background_style if background_style else "Professional gradient background"}
                    - Product prominently featured and well-lit
                    - Professional studio lighting with soft shadows
                    - High quality product photography
                    - Square format (1:1 ratio)
                    - Instagram-ready composition
                    - Clean, professional look suitable for advertising
                    - No text or watermarks on the image (text will be added separately)
                    """.strip()
                    
                    print(f"🔄 Using fallback approach: generate clean image, then add programmatic text overlay")
                    
                    # Use image generation approach (same as text overlay mode)
                    response = client.models.generate_content(
                        model=FALLBACK_TEXT_TO_IMAGE_MODEL,
                        contents=fallback_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                            temperature=0.3,
                            max_output_tokens=2048,
                            candidate_count=1
                        )
                    )
                    print(f"✅ Fallback image generation succeeded - will add programmatic text overlay")
            
            print(f"📥 Received response from Gemini")
            
            if not response:
                print(f"❌ No response received from Gemini")
                return None
            
            if not response.candidates:
                print(f"❌ No candidates in response")
                print(f"Response: {response}")
                return None
            
            print(f"✅ Found {len(response.candidates)} candidates")
            
            if len(response.candidates) == 0:
                print(f"❌ Empty candidates list")
                return None
            
            candidate = response.candidates[0]
            print(f"📋 Processing candidate...")
            
            if not candidate.content:
                print(f"❌ No content in candidate")
                print(f"Candidate: {candidate}")
                return None
            
            if not candidate.content.parts:
                print(f"❌ No parts in candidate content")
                print(f"Content: {candidate.content}")
                return None
            
            print(f"✅ Found {len(candidate.content.parts)} parts in content")
            
            for i, part in enumerate(candidate.content.parts):
                print(f"🔍 Processing part {i+1}...")
                
                if hasattr(part, 'text') and part.text:
                    print(f"📝 Part {i+1} contains text: {part.text[:100]}...")
                    continue
                
                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"🖼️  Part {i+1} contains inline_data")
                    
                    if not part.inline_data.data:
                        print(f"❌ No data in inline_data")
                        continue
                    
                    print(f"✅ Found image data in part {i+1}")
                    
                    try:
                        if isinstance(part.inline_data.data, str):
                            print(f"🔄 Decoding base64 string...")
                            image_data = base64.b64decode(part.inline_data.data)
                        else:
                            print(f"🔄 Using raw bytes...")
                            image_data = part.inline_data.data
                        
                        print(f"✅ Image data decoded successfully, size: {len(image_data)} bytes")
                        
                        # Apply text overlay based on user preference and model used
                        if use_text_overlay:
                            print(f"🔤 Adding programmatic Spanish text overlay...")
                            final_image_data = self.add_text_overlay(image_data, product_data, ad_concept)
                            print(f"✅ Text overlay added successfully")
                            return (final_image_data, used_fallback)
                        else:
                            # Check if we used the fallback model (which generates clean images)
                            if not used_fallback:
                                print(f"🎨 Using AI-generated text on image (no overlay)")
                                print(f"✅ Returning image with AI-generated text")
                                return (image_data, used_fallback)
                            else:
                                # Fallback scenario: we wanted AI text but had to use image generation model
                                print(f"🔄 Fallback scenario: Adding programmatic text overlay since AI text generation failed")
                                final_image_data = self.add_text_overlay(image_data, product_data, ad_concept)
                                print(f"✅ Programmatic text overlay added as fallback")
                                return (final_image_data, used_fallback)
                        
                    except Exception as decode_error:
                        print(f"❌ Error decoding image data in part {i+1}: {decode_error}")
                        continue
                else:
                    print(f"ℹ️  Part {i+1} has no inline_data")
                    print(f"Part attributes: {dir(part)}")
            
            print(f"❌ No image data found in any part")
            return (None, used_fallback)
            
        except Exception as e:
            print(f"❌ Error generating Instagram ad: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return (None, False)

# Initialize global objects
scraper = None
ad_generator = InstagramAdGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape_product():
    global scraper
    
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate MercadoLibre URL
        if 'mercadolibre' not in url.lower():
            return jsonify({'error': 'Please provide a valid MercadoLibre URL'}), 400
        
        print(f"🌐 Scraping request for URL: {url}")
        
        # Initialize scraper if needed
        if not scraper:
            print("🔧 Initializing new scraper...")
            scraper = MercadoLibreScraper()
        
        # Scrape product data
        print("🔍 Starting product scraping...")
        product_data = scraper.scrape_product(url)
        
        if not product_data:
            print("❌ Scraping returned no data")
            return jsonify({
                'error': 'Failed to scrape product data. The page may be loading slowly or the URL format may have changed. Please try again.'
            }), 500
        
        print(f"✅ Scraping successful!")
        print(f"   Title: {product_data.get('title', 'N/A')}")
        print(f"   Price: {product_data.get('price', 'N/A')}")
        print(f"   Images: {len(product_data.get('images', []))}")
        
        return jsonify({
            'success': True,
            'product_data': product_data
        })
        
    except Exception as e:
        print(f"❌ Scraping endpoint error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Provide user-friendly error messages
        error_message = str(e)
        if "Timeout" in error_message:
            error_message = "The page is taking too long to load. Please try again or check if the URL is correct."
        elif "net::" in error_message:
            error_message = "Network error. Please check your internet connection and try again."
        elif "Navigation failed" in error_message:
            error_message = "Could not navigate to the page. Please verify the URL is correct."
        
        return jsonify({'error': error_message}), 500

@app.route('/generate-ad', methods=['POST'])
def generate_ad():
    print(f"🎯 Generate ad endpoint called")
    try:
        data = request.get_json()
        product_data = data.get('product_data')
        selected_images = data.get('selected_images', [])
        use_text_overlay = data.get('use_text_overlay', True)  # Default to True
        
        if not product_data:
            print(f"❌ No product data provided")
            return jsonify({'error': 'Product data is required'}), 400
        
        print(f"✅ Product data received:")
        print(f"   Title: {product_data.get('title', 'N/A')}")
        print(f"   Price: {product_data.get('price', 'N/A')}")
        print(f"   Total Images: {len(product_data.get('images', []))}")
        print(f"   Selected Images: {len(selected_images)}")
        print(f"   Use Text Overlay: {use_text_overlay}")
        
        if selected_images:
            print(f"📸 Selected image URLs:")
            for i, img_url in enumerate(selected_images):
                print(f"   {i+1}. {img_url}")
        
        # Generate ad concept
        print(f"🔄 Step 1: Generating ad concept...")
        ad_concept = ad_generator.analyze_product_info(product_data)
        
        if ad_concept == "MODEL_OVERLOADED_ERROR":
            print(f"❌ Model is overloaded, inform user to try again later")
            return jsonify({'error': 'El modelo de IA está sobrecargado. Por favor, inténtalo de nuevo en unos minutos.'}), 503
        if "Error creating ad concept" in ad_concept:
            print(f"❌ Failed to create ad concept")
            return jsonify({'error': 'Failed to analyze product for ad concept'}), 500
        
        print(f"✅ Ad concept generated successfully")
        
        # Use selected images or fallback to first available image
        primary_image_urls = selected_images if selected_images else (product_data.get('images', [])[:1])
        
        if not primary_image_urls:
            print(f"ℹ️  No images available for product")
        else:
            print(f"✅ Using {len(primary_image_urls)} reference image(s)")
        
        # Generate Instagram ad image
        print(f"🔄 Step 2: Generating Instagram ad image...")
        ad_result = ad_generator.generate_instagram_ad(
            product_data, 
            ad_concept, 
            primary_image_urls,
            use_text_overlay
        )
        
        if not ad_result or not ad_result[0]:
            print(f"❌ Failed to generate Instagram ad image")
            return jsonify({'error': 'Failed to generate Instagram ad image'}), 500
        
        ad_image_data, used_fallback = ad_result
        
        print(f"✅ Instagram ad image generated successfully")
        print(f"   Image size: {len(ad_image_data)} bytes")
        print(f"   Text overlay used: {use_text_overlay}")
        print(f"   Fallback used: {used_fallback}")
        
        # Save the generated image
        timestamp = str(int(time.time()))
        filename = f"instagram_ad_{timestamp}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        print(f"💾 Saving image to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(ad_image_data)
        
        print(f"✅ Image saved successfully")
        
        return jsonify({
            'success': True,
            'ad_concept': ad_concept,
            'image_filename': filename,
            'download_url': f'/download/{filename}',
            'selected_images_count': len(selected_images),
            'text_overlay_used': use_text_overlay,
            'fallback_used': used_fallback
        })
        
    except Exception as e:
        print(f"❌ Unexpected error in generate_ad: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.teardown_appcontext
def cleanup(error):
    global scraper
    if scraper:
        scraper.close()
        scraper = None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
