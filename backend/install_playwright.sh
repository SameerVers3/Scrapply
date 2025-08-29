#!/bin/bash

echo "🔧 Installing Playwright with custom approach..."

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers without system dependencies
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Set environment variables to avoid system dependency installation
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

# Verify installation
echo "✅ Verifying Playwright installation..."
python -c "
from playwright.async_api import async_playwright
import asyncio

async def test_playwright():
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        await browser.close()
        await playwright.stop()
        print('✅ Playwright installed and working successfully!')
        return True
    except Exception as e:
        print(f'❌ Playwright test failed: {e}')
        return False

result = asyncio.run(test_playwright())
if not result:
    exit(1)
"

echo "🎉 Playwright installation completed!"