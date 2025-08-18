#!/usr/bin/env python3
"""
Nexus Platform Demo Script
Demonstrates the complete workflow with seed data
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)

def print_section(title):
    print(f"\n📋 {title}")
    print('-'*40)

def make_request(method, endpoint, data=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        return response
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def demo_workflow():
    print_header("NEXUS PLATFORM - WORKFLOW DEMONSTRATION")
    
    # Step 1: Health Check
    print_section("Step 1: Health Check")
    response = make_request("GET", "/health")
    if response and response.status_code == 200:
        health = response.json()
        print(f"✅ Server Status: {health['status']}")
        print(f"🕐 Timestamp: {health['timestamp']}")
        print(f"📝 Version: {health['version']}")
    else:
        print("❌ Server not accessible")
        return
    
    # Step 2: List All Jobs
    print_section("Step 2: List All Jobs (Seed Data)")
    response = make_request("GET", "/api/v1/jobs/")
    if response and response.status_code == 200:
        jobs = response.json()
        print(f"📊 Found {len(jobs)} jobs:")
        
        ready_jobs = []
        for i, job in enumerate(jobs, 1):
            status_emoji = {
                'ready': '✅',
                'pending': '⏳',
                'analyzing': '🔍', 
                'generating': '⚡',
                'testing': '🧪',
                'failed': '❌'
            }.get(job['status'], '❓')
            
            print(f"\n{i}. {status_emoji} {job['url']}")
            print(f"   📋 Status: {job['status']}")
            print(f"   👤 User: {job.get('user_id', 'N/A')}")
            print(f"   🆔 ID: {job['id']}")
            
            if job['status'] == 'ready' and job.get('api_endpoint_path'):
                print(f"   🌐 API: {job['api_endpoint_path']}")
                ready_jobs.append(job)
        
        # Step 3: Test Ready APIs
        if ready_jobs:
            print_section("Step 3: Testing Generated APIs")
            for job in ready_jobs[:3]:  # Test first 3 ready jobs
                test_generated_api(job)
        
        # Step 4: Get Job Details
        print_section("Step 4: Get Job Details")
        if jobs:
            first_job = jobs[0]
            response = make_request("GET", f"/api/v1/jobs/{first_job['id']}")
            if response and response.status_code == 200:
                job_details = response.json()
                print(f"📄 Job Details for: {job_details['url']}")
                print(f"   📅 Created: {job_details['created_at']}")
                print(f"   📊 Progress: {job_details['progress']}%")
                print(f"   💬 Message: {job_details['message']}")
                
                if job_details.get('sample_data'):
                    print(f"   📦 Sample Data Available: Yes")
                if job_details.get('analysis'):
                    print(f"   🔍 Analysis Available: Yes")
        
        # Step 5: Submit New Job
        print_section("Step 5: Submit New Scraping Job")
        new_job_data = {
            "url": "https://httpbin.org/uuid",
            "description": "Extract UUID data from httpbin test endpoint",
            "user_id": "demo_user"
        }
        
        response = make_request("POST", "/api/v1/scraping/requests", new_job_data)
        if response:
            if response.status_code == 200:
                result = response.json()
                print(f"✅ New job submitted successfully!")
                print(f"   🆔 Job ID: {result.get('job_id', 'N/A')}")
                print(f"   📋 Status: {result.get('status', 'N/A')}")
                print(f"   💬 Message: {result.get('message', 'N/A')}")
            else:
                print(f"❌ Failed to submit job: {response.status_code}")
                print(f"   Error: {response.text}")
    else:
        print(f"❌ Failed to get jobs: {response.status_code if response else 'No response'}")

def test_generated_api(api_path, source_url):
    """Test a generated API endpoint"""
    print(f"
🧪 Testing API: {api_path}")
    print(f"   🔗 Source: {source_url}")
    
    try:
        # Test GET request to the generated API
        response = make_request("GET", api_path)
        if response and response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Response: {len(data)} items" if isinstance(data, list) else "   ✅ API Response: Success")
            if isinstance(data, list) and data:
                print(f"   📋 Sample item: {list(data[0].keys())[:3]}..." if isinstance(data[0], dict) else f"   � First item: {data[0]}")
            elif isinstance(data, dict):
                print(f"   📋 Keys: {list(data.keys())[:3]}...")
        else:
            print(f"   ❌ Failed: Status {response.status_code if response else 'No response'}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        
    return response

if __name__ == "__main__":
    demo_workflow()
    
    print_header("DEMO COMPLETE")
    print("🎉 All workflow steps demonstrated!")
    print(f"🌐 API Documentation: {BASE_URL}/docs")
    print(f"📚 ReDoc: {BASE_URL}/redoc")
    print(f"🏥 Health: {BASE_URL}/health")
