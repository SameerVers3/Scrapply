#!/bin/bash

echo "🔧 Installing Playwright with minimal approach..."

# Install Python dependencies
pip install -r requirements.txt

# Install only Chromium browser without system dependencies
echo "🌐 Installing Chromium browser only..."
playwright install chromium

# Set environment variables for headless operation
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
export DISPLAY=:99

echo "✅ Playwright installation completed!"