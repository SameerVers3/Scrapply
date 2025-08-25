#!/usr/bin/env python3
"""
Simple test script to verify Playwright is working correctly
"""

import asyncio
from playwright.async_api import async_playwright

async def test_playwright_basic():
    """Test basic Playwright functionality"""
    print("Testing basic Playwright installation...")
    
    try:
        async with async_playwright() as p:
            print("✅ Playwright initialized successfully")
            
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            print("✅ Browser launched successfully")
            
            # Create page
            page = await browser.new_page()
            print("✅ Page created successfully")
            
            # Navigate to a simple page
            await page.goto("https://httpbin.org/html")
            print("✅ Navigation successful")
            
            # Get content
            content = await page.content()
            print(f"✅ Content retrieved successfully (length: {len(content)})")
            
            # Close browser
            await browser.close()
            print("✅ Browser closed successfully")
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing Playwright: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dynamic_content():
    """Test dynamic content detection"""
    print("\nTesting dynamic content detection...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to a dynamic website
            await page.goto("https://www.imdb.com/search/title/?groups=top_100&sort=user_rating,desc", wait_until="networkidle")
            print("✅ Navigated to IMDB successfully")
            
            # Wait for content to load
            await page.wait_for_timeout(3000)
            
            # Check for dynamic content indicators
            js_frameworks = await page.evaluate("""
                () => {
                    const frameworks = [];
                    if (window.React) frameworks.push('React');
                    if (window.Vue) frameworks.push('Vue');
                    if (window.angular) frameworks.push('Angular');
                    if (window.jQuery) frameworks.push('jQuery');
                    return frameworks;
                }
            """)
            
            # Check for dynamic loading patterns
            dynamic_loading = await page.evaluate("""
                () => {
                    const indicators = [];
                    if (document.querySelector('[data-testid="results-section"]')) {
                        indicators.push('data-testid selectors');
                    }
                    if (document.querySelector('.lister-list')) {
                        indicators.push('lister-list container');
                    }
                    return indicators;
                }
            """)
            
            print(f"✅ JavaScript frameworks detected: {js_frameworks}")
            print(f"✅ Dynamic loading patterns: {dynamic_loading}")
            
            # Get page title to verify content loaded
            title = await page.title()
            print(f"✅ Page title: {title}")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Error testing dynamic content: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Playwright tests...")
    
    # Test basic Playwright functionality
    basic_test = await test_playwright_basic()
    
    # Test dynamic content detection
    dynamic_test = await test_dynamic_content()
    
    if basic_test and dynamic_test:
        print("\n🎉 All tests passed! Playwright is working correctly.")
        print("✅ The original error should now be resolved.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    import sys
    sys.exit(0 if success else 1)