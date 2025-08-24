#!/usr/bin/env python3
"""
Demo script showing dynamic scraping in action
Tests against real dynamic websites
"""

import asyncio
import json
from app.core.dynamic_scraper import DynamicScraperEngine

async def demo_dynamic_scraping():
    """Demo dynamic scraping with real examples"""
    print("🚀 Dynamic Scraping Demo")
    print("=" * 50)
    
    # Test cases with different types of dynamic content
    test_cases = [
        {
            "name": "Simple HTML Page",
            "url": "https://httpbin.org/html",
            "selectors": {
                "container": "body",
                "title": "h1", 
                "content": "p"
            },
            "expected_dynamic": False
        },
        {
            "name": "JSON Placeholder (API-driven)",
            "url": "https://jsonplaceholder.typicode.com/",
            "selectors": {
                "container": "body",
                "title": "h1,h2",
                "links": "a"
            },
            "expected_dynamic": True
        }
    ]
    
    async with DynamicScraperEngine(timeout=30) as scraper:
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 Test {i}: {case['name']}")
            print(f"🔗 URL: {case['url']}")
            
            try:
                # Step 1: Detect dynamic content
                print("   🔍 Detecting dynamic content...")
                detection = await scraper.detect_dynamic_content(case['url'])
                
                confidence = detection['confidence_score']
                frameworks = detection['javascript_frameworks']
                
                print(f"   📊 Confidence Score: {confidence:.2f}")
                print(f"   ⚡ JS Frameworks: {frameworks}")
                print(f"   🎯 Expected Dynamic: {case['expected_dynamic']}")
                
                # Step 2: Scrape with browser
                print("   🌐 Scraping with browser automation...")
                result = await scraper.scrape_with_browser(
                    case['url'], 
                    case['selectors'],
                    {"wait_strategy": "networkidle", "handle_scroll": False}
                )
                
                if result.get('success'):
                    data = result.get('data', [])
                    print(f"   ✅ Success! Extracted {len(data)} items")
                    
                    # Show sample data
                    if data:
                        print(f"   📋 Sample: {json.dumps(data[0], indent=4)[:200]}...")
                    else:
                        print("   📋 No items extracted (might need better selectors)")
                        
                    print(f"   ⏱️  Page Title: {result.get('metadata', {}).get('title', 'N/A')}")
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
            print("   " + "-" * 40)

async def demo_strategy_selection():
    """Demo the strategy selection logic"""
    print("\n🎯 Strategy Selection Demo")
    print("=" * 50)
    
    from app.core.strategy_selector import ScrapingStrategySelector
    
    selector = ScrapingStrategySelector()
    
    # Simulate different website analysis results
    scenarios = [
        {
            "name": "Modern React SPA",
            "analysis": {
                "dynamic_indicators": {
                    "confidence_score": 0.9,
                    "javascript_frameworks": ["React", "Next.js"],
                    "spa_patterns": ["react-root", "app-root"],
                    "dynamic_loading": ["infinite-scroll", "loading-element"]
                }
            }
        },
        {
            "name": "jQuery Enhanced Site",
            "analysis": {
                "dynamic_indicators": {
                    "confidence_score": 0.5,
                    "javascript_frameworks": ["jQuery"],
                    "spa_patterns": [],
                    "dynamic_loading": ["loading-element"]
                }
            }
        },
        {
            "name": "Traditional Static Site",
            "analysis": {
                "dynamic_indicators": {
                    "confidence_score": 0.1,
                    "javascript_frameworks": [],
                    "spa_patterns": [],
                    "dynamic_loading": []
                }
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        
        analysis = scenario['analysis']
        indicators = analysis['dynamic_indicators']
        
        print(f"   📊 Confidence: {indicators['confidence_score']}")
        print(f"   ⚡ Frameworks: {indicators['javascript_frameworks']}")
        
        # Get strategy recommendation
        strategy = selector.select_strategy(analysis)
        config = selector.get_strategy_config(strategy, analysis)
        
        print(f"   🎯 Recommended Strategy: {strategy.upper()}")
        print(f"   🔧 Engine: {config.get('engine', 'hybrid')}")
        print(f"   ⏱️  Timeout: {config.get('timeout')}s")
        
        # Explain the decision
        if strategy == "dynamic":
            print("   💡 Reason: High JS confidence, use browser automation")
        elif strategy == "hybrid":
            print("   💡 Reason: Medium confidence, try static first then fallback")
        else:
            print("   💡 Reason: Low JS usage, static scraping sufficient")

async def main():
    """Run the complete demo"""
    print("🎮 Dynamic Scraping Implementation Demo")
    print("=" * 60)
    
    try:
        # Demo 1: Actual dynamic scraping
        await demo_dynamic_scraping()
        
        # Demo 2: Strategy selection
        await demo_strategy_selection()
        
        print("\n" + "=" * 60)
        print("🎉 Demo completed successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("   ✅ Dynamic content detection")
        print("   ✅ Browser automation with Playwright")
        print("   ✅ Intelligent strategy selection")
        print("   ✅ Confidence-based decision making")
        print("   ✅ Robust error handling")
        
        print("\n💡 Your scraper now supports:")
        print("   • Static websites (traditional)")
        print("   • Dynamic websites (React, Vue, Angular)")
        print("   • Hybrid approach (best of both)")
        print("   • Automatic fallback mechanisms")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
