# Render Deployment Guide - Fixing Playwright Issues

## Problem
When deploying to Render, you may encounter this error:
```
Failed to detect dynamic content for https://www.imdb.com/search/title/?groups=top_100&sort=user_rating,desc: 
BrowserType.launch: Executable doesn't exist at /opt/render/.cache/ms-playwright/chromium_headless_shell-1181/chrome-linux/headless_shell
```

## Root Cause
Playwright requires browser binaries to be installed separately from the Python package. On Render, these binaries are not automatically installed during deployment.

## Solutions

### Solution 1: Using render.yaml (Recommended)

1. **Create `render.yaml` in your project root:**
```yaml
services:
  - type: web
    name: nexus-platform-backend
    env: python
    plan: starter
    buildCommand: |
      cd backend
      pip install -r requirements.txt
      playwright install chromium
      playwright install --with-deps
    startCommand: |
      cd backend
      uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
```

2. **Deploy using the render.yaml file:**
   - Connect your repository to Render
   - Render will automatically detect and use the `render.yaml` configuration

### Solution 2: Manual Render Dashboard Configuration

1. **In your Render dashboard, set the build command to:**
```bash
cd backend && pip install -r requirements.txt && playwright install chromium
```

2. **Set the start command to:**
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Solution 3: Using a Build Script

1. **Create `backend/install_playwright_minimal.sh`:**
```bash
#!/bin/bash
echo "🔧 Installing Playwright with minimal approach..."
pip install -r requirements.txt
playwright install chromium
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
export DISPLAY=:99
echo "✅ Playwright installation completed!"
```

2. **Make it executable:**
```bash
chmod +x backend/install_playwright_minimal.sh
```

3. **Set the build command in Render to:**
```bash
cd backend && ./install_playwright_minimal.sh
```

## Environment Variables

Make sure to set these environment variables in your Render dashboard:

- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - Your database connection string
- `ANTHROPIC_API_KEY` - Your Anthropic API key (if using Claude)
- `PYTHON_VERSION` - Set to 3.11.0 for best compatibility

## Verification

After deployment, you can verify that Playwright is working by:

1. **Checking the build logs** - You should see:
   ```
   playwright install chromium
   ✅ Playwright installation completed!
   ```

2. **Testing the API endpoint** - Make a request to your dynamic scraping endpoint

## Troubleshooting

### If you still get the error:

1. **Check the build logs** in Render dashboard
2. **Verify the build command** includes `playwright install chromium`
3. **Ensure you're using Python 3.11** (not 3.13, which may have compatibility issues)
4. **Check that the start command** is correct and points to the right directory

### Common Issues:

1. **Wrong working directory** - Make sure to `cd backend` before running commands
2. **Missing dependencies** - Ensure `playwright install chromium` is included (avoid `--with-deps`)
3. **Python version** - Use Python 3.11 for best compatibility

## Alternative: Disable Dynamic Scraping

If you don't need dynamic content scraping, you can modify the code to fall back to static scraping:

```python
# In your scraping logic, add a fallback
try:
    # Try dynamic scraping with Playwright
    content = await dynamic_scraper.get_content(url)
except Exception as e:
    logger.warning(f"Dynamic scraping failed: {e}")
    # Fall back to static scraping
    content = await static_scraper.get_content(url)
```

## Files Modified

- `render.yaml` - Render configuration file
- `backend/install_playwright_minimal.sh` - Minimal Playwright installation script
- `backend/app/core/dynamic_scraper.py` - Added error handling and auto-installation
- `RENDER_DEPLOYMENT_GUIDE.md` - This guide

## Next Steps

1. Choose one of the solutions above
2. Deploy to Render using the chosen method
3. Monitor the build logs to ensure Playwright browsers are installed
4. Test your dynamic scraping functionality

The key is ensuring that `playwright install chromium` runs during the build process on Render.