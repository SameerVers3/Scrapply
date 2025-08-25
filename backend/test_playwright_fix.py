#!/usr/bin/env python3
"""
Test script to verify Playwright is working correctly
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.dynamic_scraper import DynamicScraperEngine

async def test_playwright():
    """Test Playwright functionality"""
    print("Testing Playwright installation...")
    
    try:
        async with DynamicScraperEngine(timeout=30) as scraper:
            print("✅ DynamicScraperEngine initialized successfully")
            
            # Test with a simple URL
            test_url = "https://httpbin.org/html"
            content = await scraper.get_page_content(test_url)
            
            if content:
                print(f"✅ Successfully retrieved content from {test_url}")
                print(f"   Content length: {len(content)} characters")
                print(f"   First 200 chars: {content[:200]}...")
            else:
                print(f"❌ Failed to retrieve content from {test_url}")
                
    except Exception as e:
        print(f"❌ Error testing Playwright: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_dynamic_content_detection():
    """Test dynamic content detection"""
    print("\nTesting dynamic content detection...")
    
    try:
        async with DynamicScraperEngine(timeout=30) as scraper:
            # Test with a dynamic website
            test_url = "https://www.imdb.com/search/title/?groups=top_100&sort=user_rating,desc"
            dynamic_indicators = await scraper.detect_dynamic_content(test_url)
            
            print(f"✅ Dynamic content detection completed")
            print(f"   JavaScript frameworks: {dynamic_indicators.get('javascript_frameworks', [])}")
            print(f"   SPA patterns: {dynamic_indicators.get('spa_patterns', [])}")
            print(f"   Dynamic loading: {dynamic_indicators.get('dynamic_loading', [])}")
            print(f"   Requires interaction: {dynamic_indicators.get('requires_interaction', False)}")
            print(f"   Confidence score: {dynamic_indicators.get('confidence_score', 0)}")
            
    except Exception as e:
        print(f"❌ Error testing dynamic content detection: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Playwright tests...")
    
    # Test basic Playwright functionality
    basic_test = await test_playwright()
    
    # Test dynamic content detection
    dynamic_test = await test_dynamic_content_detection()
    
    if basic_test and dynamic_test:
        print("\n🎉 All tests passed! Playwright is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)