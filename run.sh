#!/bin/bash

# MercadoLibre Instagram Ad Generator Startup Script

echo "🚀 Starting MercadoLibre Instagram Ad Generator"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your Gemini API key before running the app."
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
    read -p "Press enter when you've added your API key to .env file..."
fi

# Create necessary directories
mkdir -p output uploads temp

# Start the Flask application
echo "🌐 Starting Flask application..."
echo "   Open your browser and go to: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

python app.py
