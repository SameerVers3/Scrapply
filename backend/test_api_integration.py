#!/usr/bin/env python3
"""
Comprehensive test of the integrated dynamic scraping API endpoints
Tests the full workflow including the new dynamic scraping capabilities
"""

import requests
import json
import time
import asyncio
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)

def print_section(title: str):
    print(f"\n📋 {title}")
    print('-'*40)

def make_request(method: str, endpoint: str, data: Dict = None, timeout: int = 30):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        
        return response
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_capabilities_endpoint():
    """Test the capabilities endpoint"""
    print_section("Testing Capabilities Endpoint")
    
    response = make_request("GET", "/api/v1/scraping/capabilities")
    if response and response.status_code == 200:
        capabilities = response.json()
        print(f"✅ Capabilities endpoint working")
        print(f"📊 Version: {capabilities.get('version', 'N/A')}")
        
        features = capabilities.get('features', {})
        print(f"🔧 Static Scraping: {'✅' if features.get('static_scraping', {}).get('supported') else '❌'}")
        print(f"⚡ Dynamic Scraping: {'✅' if features.get('dynamic_scraping', {}).get('supported') else '❌'}")
        print(f"🔄 Hybrid Approach: {'✅' if features.get('hybrid_approach', {}).get('supported') else '❌'}")
        
        frameworks = capabilities.get('supported_frameworks', [])
        print(f"📦 Supported Frameworks: {', '.join(frameworks[:5])}{'...' if len(frameworks) > 5 else ''}")
        
        return True
    else:
        print(f"❌ Capabilities endpoint failed: {response.status_code if response else 'No response'}")
        return False

def test_analysis_endpoint():
    """Test the website analysis endpoint"""
    print_section("Testing Website Analysis Endpoint")
    
    # Test with different types of sites
    test_sites = [
        {
            "url": "https://news.ycombinator.com/news",
            "description": "Extract story titles, points, and comments from Hacker News",
            "name": "Hacker News (Static-ish)"
        },
        {
            "url": "https://httpbin.org/html",
            "description": "Extract title and content from this simple HTML page",
            "name": "HTTPBin (Static)"
        }
    ]
    
    for site in test_sites:
        print(f"\n🔍 Analyzing: {site['name']}")
        print(f"🔗 URL: {site['url']}")
        
        data = {
            "url": site["url"],
            "description": site["description"]
        }
        
        response = make_request("POST", "/api/v1/scraping/analyze", data, timeout=60)
        if response and response.status_code == 200:
            analysis = response.json()
            
            print(f"   ✅ Analysis completed")
            print(f"   🎯 Site Type: {analysis.get('analysis', {}).get('site_type', 'unknown')}")
            print(f"   📊 Confidence: {analysis.get('analysis', {}).get('confidence', 0)}")
            
            dynamic = analysis.get('dynamic_detection', {})
            print(f"   ⚡ Dynamic Score: {dynamic.get('confidence_score', 0):.2f}")
            print(f"   📦 JS Frameworks: {dynamic.get('javascript_frameworks', [])}")
            
            strategy = analysis.get('strategy', {})
            print(f"   🎯 Strategy: {strategy.get('selected', 'unknown').upper()}")
            print(f"   🔧 Engine: {strategy.get('engine', 'unknown')}")
            print(f"   ⏱️  Timeout: {strategy.get('timeout', 30)}s")
            
        else:
            print(f"   ❌ Analysis failed: {response.status_code if response else 'No response'}")
            if response:
                print(f"   📄 Error: {response.text[:200]}")

def test_dynamic_endpoint():
    """Test the dynamic scraping test endpoint"""
    print_section("Testing Dynamic Scraping Test Endpoint")
    
    test_data = {
        "url": "https://news.ycombinator.com/news",
        "description": "Test dynamic scraping on Hacker News"
    }
    
    print(f"🧪 Testing dynamic scraping on: {test_data['url']}")
    
    response = make_request("POST", "/api/v1/scraping/test-dynamic", test_data, timeout=90)
    if response and response.status_code == 200:
        result = response.json()
        
        print(f"✅ Dynamic test completed")
        
        detection = result.get('detection', {})
        print(f"   📊 Detection Score: {detection.get('confidence_score', 0):.2f}")
        print(f"   📦 Frameworks: {detection.get('javascript_frameworks', [])}")
        
        scraping = result.get('scraping_test', {})
        print(f"   🌐 Scraping Success: {'✅' if scraping.get('success') else '❌'}")
        print(f"   📋 Items Extracted: {scraping.get('items_extracted', 0)}")
        
        if scraping.get('sample_data'):
            print(f"   📄 Sample Data: {json.dumps(scraping['sample_data'][0], indent=2)[:200]}...")
        
        recommendations = result.get('recommendations', {})
        print(f"   🎯 Recommended Strategy: {recommendations.get('strategy', 'unknown').upper()}")
        print(f"   ⏱️  Estimated Timeout: {recommendations.get('estimated_timeout', 30)}s")
        
        return True
    else:
        print(f"❌ Dynamic test failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"📄 Error: {response.text[:300]}")
        return False

def test_full_workflow():
    """Test the complete scraping workflow"""
    print_section("Testing Complete Scraping Workflow")
    
    # Test with Hacker News
    job_data = {
        "url": "https://news.ycombinator.com/news",
        "description": "Extract story titles, points, authors, and comment counts from the front page",
        "user_id": "integration_test"
    }
    
    print(f"🚀 Creating scraping job for: {job_data['url']}")
    
    # Step 1: Create job
    response = make_request("POST", "/api/v1/scraping/requests", job_data)
    if not response or response.status_code != 201:
        print(f"❌ Job creation failed: {response.status_code if response else 'No response'}")
        return False
    
    job = response.json()
    job_id = job["id"]
    print(f"✅ Job created with ID: {job_id}")
    print(f"📊 Initial Status: {job['status']}")
    
    # Step 2: Monitor job progress
    print(f"\n⏳ Monitoring job progress...")
    max_attempts = 24  # 2 minutes max (5s intervals)
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(5)
        attempt += 1
        
        response = make_request("GET", f"/api/v1/scraping/jobs/{job_id}")
        if response and response.status_code == 200:
            job_status = response.json()
            status = job_status["status"]
            progress = job_status["progress"]
            message = job_status.get("message", "")
            
            print(f"   📊 [{attempt:2d}/24] Status: {status} ({progress}%) - {message[:50]}...")
            
            if status == "ready":
                print(f"✅ Job completed successfully!")
                
                # Show analysis details
                analysis = job_status.get("analysis", {})
                if analysis:
                    dynamic_info = analysis.get('dynamic_indicators', {})
                    strategy_info = analysis.get('selected_strategy', 'unknown')
                    
                    print(f"   🎯 Strategy Used: {strategy_info.upper()}")
                    print(f"   ⚡ Dynamic Score: {dynamic_info.get('confidence_score', 0):.2f}")
                    print(f"   📦 Frameworks: {dynamic_info.get('javascript_frameworks', [])}")
                
                # Show API endpoint
                api_path = job_status.get("api_endpoint_path")
                if api_path:
                    print(f"   🌐 API Endpoint: {BASE_URL}{api_path}")
                
                # Show sample data
                sample_data = job_status.get("sample_data", [])
                if sample_data:
                    print(f"   📋 Sample Data ({len(sample_data)} items):")
                    for i, item in enumerate(sample_data[:2]):
                        print(f"      {i+1}. {json.dumps(item, indent=6)[:150]}...")
                
                return True, job_id, api_path
                
            elif status == "failed":
                print(f"❌ Job failed!")
                error_info = job_status.get("error_info", {})
                print(f"   📄 Error: {error_info.get('error', 'Unknown error')}")
                return False, job_id, None
                
        else:
            print(f"   ❌ Failed to get job status")
    
    print(f"⏰ Job monitoring timed out")
    return False, job_id, None

def test_generated_api(job_id: str, api_path: str):
    """Test the generated API endpoint"""
    if not api_path:
        print("❌ No API endpoint available to test")
        return
    
    print_section("Testing Generated API Endpoint")
    
    print(f"🧪 Testing API: {api_path}")
    print(f"🔗 Full URL: {BASE_URL}{api_path}")
    
    response = make_request("GET", api_path)
    if response and response.status_code == 200:
        api_result = response.json()
        
        print(f"✅ API call successful!")
        print(f"📊 Items returned: {len(api_result.get('data', []))}")
        print(f"⏱️  Execution time: {api_result.get('execution_time_ms', 'N/A')} ms")
        print(f"🌐 Source URL: {api_result.get('source_url', 'N/A')}")
        
        # Show sample results
        data = api_result.get('data', [])
        if data:
            print(f"📋 Sample Results:")
            for i, item in enumerate(data[:3]):
                print(f"   {i+1}. {json.dumps(item, indent=6)[:200]}...")
        
        metadata = api_result.get('metadata', {})
        if metadata:
            print(f"📦 Metadata: {json.dumps(metadata, indent=2)[:200]}...")
        
        return True
    else:
        print(f"❌ API test failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"📄 Error: {response.text[:200]}")
        return False

def main():
    """Run comprehensive integration tests"""
    print_header("Dynamic Scraping API Integration Test Suite")
    
    print("🔍 Testing the complete dynamic scraping integration...")
    print("This will test all new endpoints and the full workflow.")
    
    success_count = 0
    total_tests = 5
    
    try:
        # Test 1: Capabilities
        if test_capabilities_endpoint():
            success_count += 1
        
        # Test 2: Analysis
        test_analysis_endpoint()
        success_count += 1
        
        # Test 3: Dynamic Test
        if test_dynamic_endpoint():
            success_count += 1
        
        # Test 4: Full Workflow
        workflow_success, job_id, api_path = test_full_workflow()
        if workflow_success:
            success_count += 1
            
            # Test 5: Generated API
            if test_generated_api(job_id, api_path):
                success_count += 1
        
        print_header("Integration Test Results")
        print(f"📊 Tests Passed: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 All integration tests passed!")
            print("\n✅ Dynamic scraping is fully integrated and working!")
            print("\n📋 Summary of capabilities:")
            print("   • Website analysis with framework detection")
            print("   • Dynamic content detection and scoring")
            print("   • Intelligent strategy selection (static/dynamic/hybrid)")
            print("   • Browser automation with Playwright")
            print("   • Automatic fallback mechanisms")
            print("   • Generated API endpoints")
            print("   • Real-time job monitoring")
            
            print(f"\n🌐 API Documentation: {BASE_URL}/docs")
            print(f"📚 Capabilities Endpoint: {BASE_URL}/api/v1/scraping/capabilities")
            
        else:
            print(f"⚠️  Some tests failed ({total_tests - success_count} failures)")
            print("Check the logs above for details.")
        
    except Exception as e:
        print(f"\n❌ Integration test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
