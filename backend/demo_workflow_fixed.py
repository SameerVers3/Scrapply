#!/usr/bin/env python3
"""
Nexus Platform - Workflow Demonstration
========================================
This script demonstrates the complete workflow of the Nexus Platform,
from health checking to API generation and testing.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def make_request(method, endpoint, data=None):
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"Unsupported method: {method}")
            return None
            
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def demo_workflow():
    """Run complete workflow demonstration"""
    print("=" * 60)
    print("🚀 NEXUS PLATFORM - WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Health Check
    print("\n📋 Step 1: Health Check")
    print("-" * 40)
    response = make_request("GET", "/health")
    if response and response.status_code == 200:
        health_data = response.json()
        print(f"✅ Server Status: {health_data['status']}")
        print(f"🕐 Timestamp: {health_data['timestamp']}")
        print(f"📝 Version: {health_data['version']}")
    else:
        print("❌ Health check failed!")
        return
    
    # Step 2: List Jobs
    print("\n📋 Step 2: List All Jobs (Seed Data)")
    print("-" * 40)
    response = make_request("GET", "/api/v1/jobs/")
    if response and response.status_code == 200:
        jobs = response.json()
        print(f"📊 Found {len(jobs)} jobs:")
        
        ready_jobs = []
        for i, job in enumerate(jobs, 1):
            status_emoji = {"ready": "✅", "analyzing": "🔍", "failed": "❌", "pending": "⏳"}.get(job['status'], "❓")
            print(f"\n{i}. {status_emoji} {job['url']}")
            print(f"   📋 Status: {job['status']}")
            print(f"   👤 User: {job.get('user_id', 'N/A')}")
            print(f"   🆔 ID: {job['id']}")
            
            if job['status'] == 'ready' and job.get('api_endpoint_path'):
                print(f"   🌐 API: {job['api_endpoint_path']}")
                ready_jobs.append(job)
        
        # Step 3: Test Generated APIs
        print("\n📋 Step 3: Testing Generated APIs")
        print("-" * 40)
        for job in ready_jobs:
            # Use the correct generated API endpoint format
            api_endpoint = f"/generated/{job['id']}"
            test_generated_api(api_endpoint, job['url'])
        
        # Step 4: Get Job Details
        if ready_jobs:
            print("\n📋 Step 4: Get Job Details")
            print("-" * 40)
            first_job = ready_jobs[0]
            response = make_request("GET", f"/api/v1/jobs/{first_job['id']}")
            if response and response.status_code == 200:
                job_detail = response.json()
                print(f"📄 Job Details for: {job_detail['url']}")
                print(f"   📅 Created: {job_detail['created_at']}")
                print(f"   📊 Progress: {job_detail['progress']}%")
                print(f"   💬 Message: {job_detail['message']}")
                print(f"   📦 Sample Data Available: {'Yes' if job_detail.get('sample_data') else 'No'}")
                print(f"   🔍 Analysis Available: {'Yes' if job_detail.get('analysis') else 'No'}")
        
        # Step 5: Submit New Job
        print("\n📋 Step 5: Submit New Scraping Job")
        print("-" * 40)
        new_job_data = {
            "url": "https://httpbin.org/uuid",
            "description": "Extract UUID data from httpbin test endpoint"
        }
        
        response = make_request("POST", "/api/v1/scraping/requests", new_job_data)
        if response and response.status_code == 201:
            new_job = response.json()
            print(f"✅ New job created successfully!")
            print(f"   🆔 Job ID: {new_job['id']}")
            print(f"   📋 Status: {new_job['status']}")
            print(f"   💬 Message: {new_job['message']}")
        else:
            print(f"❌ Failed to submit job: {response.status_code if response else 'No response'}")
            if response:
                print(f"   Error: {response.text}")
    else:
        print(f"❌ Failed to get jobs: {response.status_code if response else 'No response'}")

def test_generated_api(api_path, source_url):
    """Test a generated API endpoint"""
    print(f"\n🧪 Testing API: {api_path}")
    print(f"   🔗 Source: {source_url}")
    
    try:
        # Test GET request to the generated API
        response = make_request("GET", api_path)
        if response and response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Response: {len(data)} items" if isinstance(data, list) else "   ✅ API Response: Success")
            if isinstance(data, list) and data:
                print(f"   📋 Sample item: {list(data[0].keys())[:3]}..." if isinstance(data[0], dict) else f"   📋 First item: {data[0]}")
            elif isinstance(data, dict):
                print(f"   📋 Keys: {list(data.keys())[:3]}...")
        else:
            print(f"   ❌ Failed: Status {response.status_code if response else 'No response'}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        
    return response

if __name__ == "__main__":
    demo_workflow()
    
    print("\n" + "=" * 60)
    print("🚀 DEMO COMPLETE")
    print("=" * 60)
    print("🎉 All workflow steps demonstrated!")
    print("🌐 API Documentation: http://127.0.0.1:8000/docs")
    print("📚 ReDoc: http://127.0.0.1:8000/redoc")
    print("🏥 Health: http://127.0.0.1:8000/health")
