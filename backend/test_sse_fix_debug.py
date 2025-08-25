#!/usr/bin/env python3
"""
Test script to verify SSE connection behavior after fixes
"""

import asyncio
import json
import aiohttp
import sys
import time

BASE_URL = "http://localhost:8000"

async def test_job_creation_and_sse():
    """Test creating a job and monitoring SSE updates"""
    
    print("🧪 Testing SSE connection behavior after fixes")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a test job
        print("\n📋 Step 1: Creating a test job...")
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/scraping/requests",
                json={
                    "url": "https://news.ycombinator.com",
                    "description": "test job for SSE debugging",
                    "user_id": "test-user-sse-debug"
                }
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    job_id = result['id']
                    print(f"✅ Job created: {job_id}")
                else:
                    print(f"❌ Failed to create job: {response.status}")
                    print(await response.text())
                    return
        except Exception as e:
            print(f"❌ Error creating job: {e}")
            return
        
        # Step 2: Connect to SSE and monitor for disconnections
        print(f"\n📡 Step 2: Connecting to SSE stream for job {job_id}...")
        
        connection_count = 0
        message_count = 0
        last_message_time = time.time()
        
        try:
            while connection_count < 5:  # Test up to 5 connections
                connection_count += 1
                connection_start = time.time()
                
                print(f"\n🔌 Connection attempt #{connection_count} at {time.strftime('%H:%M:%S')}")
                
                try:
                    async with session.get(
                        f"{BASE_URL}/api/v1/scraping/jobs/stream/{job_id}",
                        timeout=aiohttp.ClientTimeout(total=30)  # 30 second timeout
                    ) as response:
                        if response.status != 200:
                            print(f"❌ SSE connection failed: {response.status}")
                            break
                        
                        print(f"✅ SSE connection established (attempt #{connection_count})")
                        
                        connection_duration = 0
                        
                        async for line in response.content:
                            current_time = time.time()
                            connection_duration = current_time - connection_start
                            
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]  # Remove 'data: ' prefix
                                
                                try:
                                    data = json.loads(data_str)
                                    message_count += 1
                                    time_since_last = current_time - last_message_time
                                    last_message_time = current_time
                                    
                                    print(f"📦 Message #{message_count} (+{time_since_last:.1f}s) "
                                          f"[{connection_duration:.1f}s connected]: "
                                          f"{data.get('type', 'job_update')} - "
                                          f"{data.get('status', 'unknown')} "
                                          f"({data.get('progress', 0)}%)")
                                    
                                    # Check for completion
                                    if data.get('final') or data.get('status') in ['ready', 'failed']:
                                        print(f"🏁 Job completed with status: {data.get('status')}")
                                        return
                                    
                                    # Check for connection closing
                                    if data.get('type') == 'connection_closing':
                                        print(f"📡 Server closing connection: {data.get('reason')}")
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    print(f"❌ Failed to parse SSE data: {e}")
                                    print(f"   Raw data: {data_str[:100]}...")
                
                except asyncio.TimeoutError:
                    print(f"⏰ Connection #{connection_count} timed out after {connection_duration:.1f}s")
                    
                except aiohttp.ClientError as e:
                    print(f"❌ Connection #{connection_count} failed after {connection_duration:.1f}s: {e}")
                
                # Brief delay between connection attempts
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
        
        print(f"\n📊 Test Summary:")
        print(f"   Total connections: {connection_count}")
        print(f"   Total messages: {message_count}")
        print(f"   Average messages per connection: {message_count/connection_count if connection_count > 0 else 0:.1f}")

async def test_sse_health():
    """Test SSE system health endpoint"""
    
    print("\n🏥 Testing SSE health endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/api/v1/scraping/jobs/stream-health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ SSE Health: {json.dumps(health, indent=2)}")
                else:
                    print(f"❌ SSE health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Error checking SSE health: {e}")

async def main():
    print("🔧 SSE Connection Fix Testing")
    print(f"📡 Testing against: {BASE_URL}")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/docs") as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print(f"⚠️ Server responded with status: {response.status}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the backend is running on http://localhost:8000")
        return
    
    await test_sse_health()
    await test_job_creation_and_sse()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
