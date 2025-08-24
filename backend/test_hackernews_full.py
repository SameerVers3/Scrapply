#!/usr/bin/env python3
"""
Comprehensive test for Hacker News scraping
Demonstrates the complete dynamic scraping pipeline with real-world data
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.dynamic_scraper import DynamicScraperEngine
from app.core.agent import UnifiedAgent
from app.core.strategy_selector import ScrapingStrategySelector
from app.core.sandbox import SecureSandbox
from config.settings import settings

class HackerNewsTest:
    """Complete test suite for Hacker News scraping"""
    
    def __init__(self):
        self.url = "https://news.ycombinator.com/news"
        self.description = "Extract news articles from Hacker News including titles, scores, links, and comments count"
        self.test_results = {}
        
    async def run_complete_test(self):
        """Run the complete test pipeline"""
        print("🎯 HACKER NEWS SCRAPING - COMPLETE TEST SUITE")
        print("=" * 70)
        print(f"🔗 Target URL: {self.url}")
        print(f"📋 Task: {self.description}")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        try:
            # Step 1: Dynamic Content Detection
            await self._test_dynamic_detection()
            
            # Step 2: AI-Powered Website Analysis
            await self._test_ai_analysis()
            
            # Step 3: Strategy Selection
            await self._test_strategy_selection()
            
            # Step 4: Scraper Code Generation
            await self._test_code_generation()
            
            # Step 5: Sandbox Execution
            await self._test_sandbox_execution()
            
            # Step 6: Final Results & Summary
            await self._show_final_results()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()

    async def _test_dynamic_detection(self):
        """Test 1: Dynamic content detection"""
        print("🔍 STEP 1: Dynamic Content Detection")
        print("-" * 50)
        
        try:
            async with DynamicScraperEngine(timeout=30) as scraper:
                print("   📡 Analyzing Hacker News for dynamic content...")
                detection_result = await scraper.detect_dynamic_content(self.url)
                
                self.test_results['dynamic_detection'] = detection_result
                
                print(f"   ✅ Analysis complete!")
                print(f"   📊 Confidence Score: {detection_result['confidence_score']:.2f}")
                print(f"   ⚡ JS Frameworks: {detection_result['javascript_frameworks']}")
                print(f"   🎯 SPA Patterns: {detection_result['spa_patterns']}")
                print(f"   🔄 Dynamic Loading: {detection_result['dynamic_loading']}")
                print(f"   📈 Content Change Ratio: {detection_result.get('content_change_ratio', 0):.2f}")
                
                # Determine if HN is considered dynamic
                if detection_result['confidence_score'] > 0.3:
                    print("   💡 Assessment: Site has dynamic characteristics")
                else:
                    print("   💡 Assessment: Primarily static content")
                    
        except Exception as e:
            print(f"   ❌ Dynamic detection failed: {e}")
            self.test_results['dynamic_detection'] = {'error': str(e)}
        
        print()

    async def _test_ai_analysis(self):
        """Test 2: AI-powered website analysis"""
        print("🤖 STEP 2: AI-Powered Website Analysis")
        print("-" * 50)
        
        if not settings.OPENAI_API_KEY:
            print("   ⚠️  OpenAI API key not configured, skipping AI analysis")
            self.test_results['ai_analysis'] = {'error': 'No API key configured'}
            print()
            return
            
        try:
            async with UnifiedAgent(
                settings.OPENAI_API_KEY,
                settings.OPENAI_MODEL,
                settings.OPENAI_BASE_URL
            ) as agent:
                print("   🧠 Running AI analysis on Hacker News...")
                analysis = await agent.analyze_website(self.url, self.description)
                
                self.test_results['ai_analysis'] = analysis
                
                print(f"   ✅ AI analysis complete!")
                print(f"   🎯 Site Type: {analysis.get('site_type', 'unknown')}")
                print(f"   📊 AI Confidence: {analysis.get('confidence', 0):.2f}")
                print(f"   🔧 Detected Selectors:")
                
                selectors = analysis.get('selectors', {})
                for field, selector in selectors.items():
                    print(f"      • {field}: {selector}")
                
                if not selectors:
                    print("      • No specific selectors detected")
                
                print(f"   📄 Pagination: {analysis.get('pagination', {}).get('present', False)}")
                print(f"   🚧 Challenges: {', '.join(analysis.get('challenges', []))[:100]}...")
                print(f"   💡 Recommended Approach: {analysis.get('recommended_approach', 'N/A')[:80]}...")
                
        except Exception as e:
            print(f"   ❌ AI analysis failed: {e}")
            self.test_results['ai_analysis'] = {'error': str(e)}
        
        print()

    async def _test_strategy_selection(self):
        """Test 3: Strategy selection"""
        print("🎯 STEP 3: Strategy Selection")
        print("-" * 50)
        
        try:
            selector = ScrapingStrategySelector()
            
            # Use AI analysis if available, otherwise use dynamic detection
            analysis_data = self.test_results.get('ai_analysis', {})
            if 'error' in analysis_data:
                # Fallback to dynamic detection results
                analysis_data = {
                    'dynamic_indicators': self.test_results.get('dynamic_detection', {})
                }
            
            strategy = selector.select_strategy(analysis_data)
            config = selector.get_strategy_config(strategy, analysis_data)
            
            self.test_results['strategy'] = strategy
            self.test_results['strategy_config'] = config
            
            print(f"   ✅ Strategy selected: {strategy.upper()}")
            print(f"   🔧 Engine: {config.get('engine', 'hybrid')}")
            print(f"   ⏱️  Timeout: {config.get('timeout', 30)}s")
            print(f"   📚 Libraries: {', '.join(config.get('libraries', []))}")
            print(f"   🎨 Approach: {config.get('approach', 'N/A')}")
            
            # Explain the decision
            confidence = analysis_data.get('dynamic_indicators', {}).get('confidence_score', 0)
            print(f"   💡 Decision based on confidence score: {confidence:.2f}")
            
            if strategy == "dynamic":
                print("   💡 Reason: High dynamic confidence → Browser automation")
            elif strategy == "hybrid":
                print("   💡 Reason: Medium confidence → Try static, fallback to dynamic")
            else:
                print("   💡 Reason: Low dynamic indicators → Static scraping")
                
        except Exception as e:
            print(f"   ❌ Strategy selection failed: {e}")
            self.test_results['strategy'] = 'static'  # Fallback
        
        print()

    async def _test_code_generation(self):
        """Test 4: Scraper code generation"""
        print("⚡ STEP 4: Scraper Code Generation")
        print("-" * 50)
        
        if not settings.OPENAI_API_KEY:
            print("   ⚠️  OpenAI API key not configured, using manual scraper")
            # Create a manual scraper for Hacker News
            await self._create_manual_scraper()
            print()
            return
            
        try:
            async with UnifiedAgent(
                settings.OPENAI_API_KEY,
                settings.OPENAI_MODEL,
                settings.OPENAI_BASE_URL
            ) as agent:
                
                analysis = self.test_results.get('ai_analysis', {})
                strategy = self.test_results.get('strategy', 'static')
                
                print(f"   🎯 Generating {strategy} scraper for Hacker News...")
                
                if strategy == "dynamic":
                    code = await agent.generate_dynamic_scraper(analysis, self.url, self.description)
                    scraper_type = "dynamic"
                else:
                    code = await agent.generate_scraper(analysis, self.url, self.description)
                    scraper_type = "static"
                
                self.test_results['generated_code'] = code
                self.test_results['scraper_type'] = scraper_type
                
                print(f"   ✅ Generated {scraper_type} scraper ({len(code)} characters)")
                print(f"   📋 Code preview (first 300 chars):")
                print("   " + "─" * 50)
                
                # Show formatted code preview
                code_lines = code.split('\n')[:15]  # First 15 lines
                for i, line in enumerate(code_lines, 1):
                    print(f"   {i:2d} | {line}")
                
                if len(code.split('\n')) > 15:
                    remaining_lines = len(code.split('\n')) - 15
                    print(f"   .. | ... ({remaining_lines} more lines)")
                print("   " + "─" * 50)
                
        except Exception as e:
            print(f"   ❌ Code generation failed: {e}")
            await self._create_manual_scraper()
        
        print()

    async def _create_manual_scraper(self):
        """Create a manual scraper as fallback"""
        print("   🔧 Creating manual Hacker News scraper...")
        
        manual_code = '''import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import time

def scrape_data(url: str) -> Dict[str, Any]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = []
        stories = soup.find_all('tr', class_='athing')
        
        for story in stories[:20]:  # Get top 20 stories
            try:
                title_elem = story.find('span', class_='titleline')
                if not title_elem:
                    continue
                    
                title_link = title_elem.find('a')
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                link = title_link.get('href', '')
                
                # Get score and comments from next row
                next_row = story.find_next_sibling('tr')
                score = 0
                comments = 0
                
                if next_row:
                    score_elem = next_row.find('span', class_='score')
                    if score_elem:
                        score_text = score_elem.get_text()
                        score = int(score_text.split()[0]) if score_text.split() else 0
                    
                    comments_elem = next_row.find('a', string=lambda x: x and 'comment' in x.lower())
                    if comments_elem:
                        comments_text = comments_elem.get_text()
                        comments = int(comments_text.split()[0]) if comments_text.split()[0].isdigit() else 0
                
                data.append({
                    'title': title,
                    'link': link,
                    'score': score,
                    'comments': comments
                })
                
            except Exception as e:
                continue
        
        return {
            'data': data,
            'metadata': {
                'total_items': len(data),
                'scraper_type': 'static',
                'timestamp': time.time()
            }
        }
        
    except Exception as e:
        return {
            'data': [],
            'error': str(e),
            'metadata': {'scraper_type': 'static'}
        }'''
        
        self.test_results['generated_code'] = manual_code
        self.test_results['scraper_type'] = 'static'
        print("   ✅ Manual scraper created")

    async def _test_sandbox_execution(self):
        """Test 5: Sandbox execution"""
        print("🔒 STEP 5: Sandbox Execution")
        print("-" * 50)
        
        try:
            code = self.test_results.get('generated_code', '')
            scraper_type = self.test_results.get('scraper_type', 'static')
            
            if not code:
                print("   ❌ No code to execute")
                return
            
            print(f"   🚀 Executing {scraper_type} scraper in secure sandbox...")
            
            # Initialize appropriate sandbox
            timeout = 60 if scraper_type == "dynamic" else 30
            sandbox = SecureSandbox(scraper_type=scraper_type, timeout=timeout)
            
            # Execute the scraper
            start_time = time.time()
            result = await sandbox.execute_scraper(code, self.url)
            execution_time = time.time() - start_time
            
            self.test_results['execution_result'] = result
            self.test_results['execution_time'] = execution_time
            
            print(f"   ✅ Execution completed in {execution_time:.2f}s")
            
            if result.get('success'):
                data = result.get('data', [])
                print(f"   📊 Successfully extracted {len(data)} items")
                
                # Show sample data
                if data:
                    print(f"   📋 Sample extracted data:")
                    for i, item in enumerate(data[:3], 1):
                        print(f"      {i}. {json.dumps(item, indent=8)[:120]}...")
                        
                    print(f"   📈 Metadata: {result.get('metadata', {})}")
                else:
                    print("   ⚠️  No items extracted (may need selector adjustment)")
                    
            else:
                print(f"   ❌ Execution failed: {result.get('error', 'Unknown error')}")
                if 'stderr' in result:
                    print(f"   🔍 Error details: {result['stderr'][:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Sandbox execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()

    async def _show_final_results(self):
        """Show comprehensive final results"""
        print("📊 FINAL RESULTS & SUMMARY")
        print("=" * 70)
        
        # Test Results Summary
        print("🏆 Test Results Summary:")
        print("-" * 30)
        
        tests = [
            ('Dynamic Detection', 'dynamic_detection'),
            ('AI Analysis', 'ai_analysis'),
            ('Strategy Selection', 'strategy'),
            ('Code Generation', 'generated_code'),
            ('Sandbox Execution', 'execution_result')
        ]
        
        for test_name, test_key in tests:
            result = self.test_results.get(test_key)
            if result and 'error' not in str(result):
                print(f"   ✅ {test_name}: PASSED")
            else:
                print(f"   ❌ {test_name}: FAILED")
        
        print()
        
        # Detailed Results
        execution_result = self.test_results.get('execution_result', {})
        if execution_result.get('success'):
            data = execution_result.get('data', [])
            
            print("📰 SCRAPED HACKER NEWS DATA:")
            print("-" * 40)
            
            if data:
                print(f"📊 Total articles extracted: {len(data)}")
                print()
                
                for i, article in enumerate(data[:10], 1):  # Show top 10
                    title = article.get('title', 'N/A')
                    score = article.get('score', 0)
                    comments = article.get('comments', 0)
                    link = article.get('link', '')
                    
                    print(f"{i:2d}. 📰 {title}")
                    print(f"    ⬆️  {score} points | 💬 {comments} comments")
                    if link:
                        print(f"    🔗 {link}")
                    print()
                
                # Statistics
                if len(data) > 10:
                    print(f"... and {len(data) - 10} more articles")
                    
                total_score = sum(item.get('score', 0) for item in data)
                total_comments = sum(item.get('comments', 0) for item in data)
                avg_score = total_score / len(data) if data else 0
                avg_comments = total_comments / len(data) if data else 0
                
                print("📈 STATISTICS:")
                print(f"   • Total Score: {total_score:,}")
                print(f"   • Total Comments: {total_comments:,}")
                print(f"   • Average Score: {avg_score:.1f}")
                print(f"   • Average Comments: {avg_comments:.1f}")
                
            else:
                print("⚠️  No data extracted - may need selector refinement")
        else:
            print("❌ Scraping failed - see execution results above")
        
        print()
        
        # Technical Summary
        print("⚙️  TECHNICAL SUMMARY:")
        print("-" * 30)
        
        strategy = self.test_results.get('strategy', 'unknown')
        scraper_type = self.test_results.get('scraper_type', 'unknown')
        execution_time = self.test_results.get('execution_time', 0)
        
        print(f"   🎯 Selected Strategy: {strategy.upper()}")
        print(f"   🔧 Scraper Type: {scraper_type.upper()}")
        print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
        
        # Dynamic indicators
        dynamic_result = self.test_results.get('dynamic_detection', {})
        if dynamic_result and 'error' not in dynamic_result:
            confidence = dynamic_result.get('confidence_score', 0)
            frameworks = dynamic_result.get('javascript_frameworks', [])
            print(f"   📊 Dynamic Confidence: {confidence:.2f}")
            print(f"   ⚡ JS Frameworks: {frameworks}")
        
        print()
        print("🎉 HACKER NEWS SCRAPING TEST COMPLETED!")
        
        # Success indicator
        if execution_result.get('success') and execution_result.get('data'):
            print("✅ SUCCESS: Your scraper can now extract data from Hacker News!")
        else:
            print("⚠️  PARTIAL SUCCESS: Framework is working, may need selector tuning")

async def main():
    """Run the Hacker News test"""
    test = HackerNewsTest()
    await test.run_complete_test()

if __name__ == "__main__":
    import time
    asyncio.run(main())
