#!/usr/bin/env python3
"""
Test SSE connection stability after fixes
"""

import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"

async def test_sse_stability():
    print("🧪 Testing SSE stability after fixes...")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a job
        print("\n📋 Step 1: Creating a test job...")
        async with session.post(f"{BASE_URL}/api/v1/scraping/requests", json={
            "url": "https://httpbin.org/delay/30",  # 30 second delay to test connection
            "description": "test connection stability"
        }) as response:
            if response.status == 201:
                result = await response.json()
                job_id = result['id']
                print(f"✅ Job created: {job_id}")
            else:
                print(f"❌ Failed to create job: {response.status}")
                return

        # Step 2: Test SSE connection for 20 seconds
        print(f"\n📡 Step 2: Testing SSE connection stability for 20 seconds...")
        
        connection_start = time.time()
        heartbeat_count = 0
        update_count = 0
        disconnection_count = 0
        
        try:
            async with session.get(f"{BASE_URL}/api/v1/scraping/jobs/stream/{job_id}") as response:
                print(f"✅ SSE connection established (status: {response.status})")
                
                async for line in response.content:
                    if time.time() - connection_start > 20:  # Test for 20 seconds
                        print(f"⏰ 20 second test completed")
                        break
                        
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: '
                            
                            if data.get('type') in ['heartbeat', 'keepalive']:
                                heartbeat_count += 1
                                print(f"💓 Heartbeat #{heartbeat_count} received at {time.time() - connection_start:.1f}s")
                            else:
                                update_count += 1
                                print(f"📦 Update #{update_count}: {data.get('status', 'unknown')} ({data.get('progress', 0)}%)")
                                
                                if data.get('final') or data.get('status') in ['ready', 'failed']:
                                    print(f"🏁 Job completed, connection should close")
                                    break
                                    
                        except json.JSONDecodeError:
                            print(f"⚠️ Could not parse: {line_str}")
                            
        except Exception as e:
            disconnection_count += 1
            print(f"❌ Connection error #{disconnection_count}: {e}")
        
        connection_duration = time.time() - connection_start
        
        print(f"\n📊 Connection Summary:")
        print(f"   Duration: {connection_duration:.1f} seconds")
        print(f"   Heartbeats: {heartbeat_count}")
        print(f"   Updates: {update_count}")
        print(f"   Disconnections: {disconnection_count}")
        
        if connection_duration >= 15 and disconnection_count == 0:
            print(f"✅ SSE connection stability test PASSED")
        else:
            print(f"❌ SSE connection stability test FAILED")

if __name__ == "__main__":
    asyncio.run(test_sse_stability())
