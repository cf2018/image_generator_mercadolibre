# MercadoLibre Instagram Ad Generator 🚀

A robust Flask application that automatically generates professional Instagram ad images from MercadoLibre product listings. The app scrapes product data using Playwright and creates high-quality Spanish ad images using Google Gemini AI and programmatic text overlay.

## Features

- � **MercadoLibre Scraping**: Extracts product titles, prices, descriptions, and images using Playwright
- 🤖 **AI-Powered Ad Concepts**: Generates professional Spanish ad copy using Google Gemini
- 🎨 **Professional Image Generation**: Creates clean product images with AI, then adds text programmatically
- 📱 **Instagram-Ready Format**: 1080x1080 square format optimized for Instagram
- 🇪🇸 **Spanish Language**: All ad text and concepts are generated in Spanish
- � **Docker Ready**: Fully containerized for easy deployment
- 🔍 **Debug Logging**: Comprehensive logging for troubleshooting

## Key Innovation

The app uses a **two-step approach** to ensure perfect ad quality:

1. **Clean Image Generation**: Uses minimal prompts to generate text-free product images
2. **Programmatic Text Overlay**: Adds all Spanish ad text (title, price, CTA) using PIL with professional styling

This approach eliminates AI-generated text errors and ensures consistent, professional results.

## Requirements

- Python 3.9+
- Google Gemini API key
- Docker (optional, for containerized deployment)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd image_generator_mercadolibre

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file , check .env_example rename it to .env and add ONE api key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
```

### 3. Run the Application ( LOCAL DEVELOPMENT )

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## API Usage

### Generate Instagram Ad

**POST** `/generate-ad`

```json
{
  "mercadolibre_url": "https://articulo.mercadolibre.com.ar/MLA-XXXXXXXX-product-name"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ad generated successfully",
  "ad_concept": "## Concepto Publicitario...",
  "image_filename": "instagram_ad_1234567890.jpg",
  "download_url": "/download/instagram_ad_1234567890.jpg"
}
```

### Download Generated Image

**GET** `/download/<filename>`

Returns the generated Instagram ad image file.

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t instagram-ad-generator .

# Run with environment variables
docker run -p 5000:5000 -e GEMINI_API_KEY=your_key_here instagram-ad-generator
```

### Using Docker Compose

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Project Structure

```
image_generator_mercadolibre/
├── app.py                      # Main Flask application
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── .env                        # Environment variables (create this)
├── README.md                   # This file
├── generated_ads/              # Output directory for generated images
├── tests/                      # Test scripts
│   ├── test_gemini_image.py   # Gemini image generation tests
│   └── test_quick_image.py    # Quick image tests
├── test_flask_workflow.py     # Full workflow integration test
├── test_text_free.py          # Text-free image validation
└── minimal_test.py            # Minimal Gemini API test
```

## Technical Architecture

### Scraping Engine (Playwright)
- Headless browser automation for reliable MercadoLibre scraping
- Handles dynamic content
- Extracts: title, price, description, images

### AI Ad Concept Generation (Google Gemini)
- Uses `gemini-2.0-flash-thinking-exp` for Spanish ad copy generation
- Generates compelling titles, descriptions, and CTAs
- Optimized prompts for Instagram ad best practices

### Image Generation Pipeline
1. **Product Image**: Minimal prompt to `gemini-2.0-flash-preview-image-generation`
2. **Text Overlay**: PIL-based professional Spanish text overlay
   - Gradient backgrounds for text readability
   - Professional fonts and typography
   - Price formatting and CTA placement

### Error Handling
- Comprehensive logging throughout the pipeline
- Graceful fallbacks for scraping failures
- Validation of generated content quality

## Testing

### Run All Tests

```bash
# Test individual components
python tests/test_gemini_image.py
python minimal_test.py
python test_text_free.py

# Test complete workflow
python test_flask_workflow.py
```

### Development Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with debug logging
FLASK_ENV=development python app.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `FLASK_ENV` | Flask environment | `production` |
| `PORT` | Port to run the app | `5000` |

### Gemini Models Used

- **Ad Concept**: `gemini-2.0-flash-thinking-exp` - For Spanish ad copy generation
- **Image Generation**: `gemini-2.0-flash-preview-image-generation` - For product images

## Troubleshooting

### Common Issues

1. **Gemini API Errors**
   - Verify API key in `.env` file
   - Check API quota and billing
   - Ensure you have access to image generation models

2. **Scraping Failures**
   - MercadoLibre may have changed their page structure
   - Check if the URL is valid and accessible
   - Review Playwright logs for detailed errors

3. **Image Generation Issues**
   - Ensure the model supports image generation
   - Check prompt length and content
   - Review debug logs for detailed error messages

### Debug Mode

Enable detailed logging:

```bash
FLASK_ENV=development python app.py
```

## Getting Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy it to your `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## Changelog

### v2.0.0 (Current)
- ✅ Migrated from Selenium to Playwright for better reliability
- ✅ Switched to new `google-genai` SDK
- ✅ Implemented two-step image generation approach
- ✅ Added programmatic Spanish text overlay
- ✅ Enhanced error handling and logging
- ✅ Added comprehensive testing suite
- ✅ Docker optimization and deployment ready

### v1.0.0 (Legacy)
- Basic Selenium-based scraping
- Direct AI image generation with text
- Single-step process (deprecated)
- Adding more customization options

## License

This project is for educational purposes. Please respect MercadoLibre's terms of service when scraping their content.

## Disclaimer

This tool is for educational and research purposes. Always respect website terms of service and rate limits when scraping. Use responsibly and ensure you have permission to scrape the target websites.
