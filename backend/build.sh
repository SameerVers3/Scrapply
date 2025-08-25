#!/bin/bash

# Render Build Script for Playwright Support

echo "🔧 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install --with-deps

# Verify installation
echo "✅ Verifying Playwright installation..."
python -c "from playwright.async_api import async_playwright; print('Playwright installed successfully')"

echo "🎉 Build completed successfully!"