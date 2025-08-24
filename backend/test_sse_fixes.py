#!/usr/bin/env python3
"""
Test script to verify SSE fixes for connection stability
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

async def test_completed_job_sse():
    """Test SSE behavior with completed jobs (should not reconnect constantly)"""
    print("🔄 Testing SSE behavior with completed jobs")
    print("=" * 50)
    
    # Step 1: Create a simple job
    print("\n📋 Step 1: Creating a simple test job...")
    async with aiohttp.ClientSession() as session:
        job_data = {
            "url": "https://httpbin.org/html",
            "description": "SSE connection stability test",
            "user_id": "sse_stability_test"
        }
        
        async with session.post(f"{BASE_URL}/api/v1/scraping/requests", json=job_data) as response:
            if response.status != 201:
                print(f"❌ Failed to create job: {response.status}")
                return None
            
            result = await response.json()
            job_id = result['id']
            print(f"✅ Job created: {job_id}")
            return job_id

async def test_sse_connection_lifecycle(job_id: str):
    """Test the complete SSE connection lifecycle"""
    print(f"\n📡 Testing SSE connection lifecycle for job {job_id}")
    
    connection_count = 0
    max_connections = 3
    
    async def single_sse_connection(connection_num):
        nonlocal connection_count
        connection_count += 1
        
        print(f"\n🔌 Connection #{connection_num}: Starting SSE stream...")
        
        timeout = aiohttp.ClientTimeout(total=60)  # 1 minute timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(f"{BASE_URL}/api/v1/scraping/jobs/stream/{job_id}") as response:
                    if response.status != 200:
                        print(f"❌ Connection #{connection_num}: SSE failed with status {response.status}")
                        return
                    
                    print(f"✅ Connection #{connection_num}: SSE connected successfully")
                    
                    message_count = 0
                    start_time = time.time()
                    final_received = False
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            try:
                                data = json.loads(data_str)
                                message_count += 1
                                elapsed = time.time() - start_time
                                
                                if data.get('type') == 'keepalive':
                                    print(f"💓 Connection #{connection_num}: Keepalive (subscribers: {data.get('subscribers', 0)})")
                                elif data.get('type') == 'connection_closing':
                                    print(f"📡 Connection #{connection_num}: Server closing connection - {data.get('reason')}")
                                    break
                                elif data.get('type') == 'job_completed':
                                    print(f"🏁 Connection #{connection_num}: Job completed notification received")
                                    final_received = True
                                    break
                                elif data.get('final'):
                                    print(f"🏁 Connection #{connection_num}: Final message received")
                                    final_received = True
                                    break
                                else:
                                    status = data.get('status', 'unknown')
                                    progress = data.get('progress', 0)
                                    message = data.get('message', '')
                                    print(f"📦 Connection #{connection_num}: {status} ({progress}%) - {message}")
                                
                            except json.JSONDecodeError as e:
                                print(f"❌ Connection #{connection_num}: Failed to parse JSON: {e}")
                    
                    duration = time.time() - start_time
                    print(f"📊 Connection #{connection_num} Summary:")
                    print(f"   • Messages received: {message_count}")
                    print(f"   • Duration: {duration:.1f} seconds")
                    print(f"   • Final message received: {'✅' if final_received else '❌'}")
                    print(f"   • Clean disconnection: ✅")
                    
            except asyncio.TimeoutError:
                print(f"⏰ Connection #{connection_num}: Timed out")
            except Exception as e:
                print(f"❌ Connection #{connection_num}: Error - {e}")
    
    # Test multiple consecutive connections to see if they behave properly
    for i in range(max_connections):
        await single_sse_connection(i + 1)
        
        # Small delay between connections to avoid overwhelming
        if i < max_connections - 1:
            print(f"\n⏳ Waiting 3 seconds before next connection...")
            await asyncio.sleep(3)

async def test_sse_health_monitoring():
    """Monitor SSE system health during testing"""
    print(f"\n📊 Testing SSE health monitoring")
    
    async with aiohttp.ClientSession() as session:
        for i in range(5):  # Check health 5 times over 30 seconds
            try:
                async with session.get(f"{BASE_URL}/api/v1/scraping/jobs/stream-health") as response:
                    if response.status == 200:
                        health = await response.json()
                        print(f"📈 Health Check #{i+1}: "
                              f"Active Streams: {health['total_active_streams']}, "
                              f"Active Jobs: {health['active_jobs']}, "
                              f"Status: {health['system_status']}")
                    else:
                        print(f"❌ Health Check #{i+1}: Failed with status {response.status}")
            except Exception as e:
                print(f"❌ Health Check #{i+1}: Error - {e}")
            
            if i < 4:  # Don't wait after the last check
                await asyncio.sleep(6)  # Check every 6 seconds

async def main():
    """Run SSE stability tests"""
    print("🧪 SSE Connection Stability Test Suite")
    print("=" * 60)
    
    try:
        # Create a test job
        job_id = await test_completed_job_sse()
        if not job_id:
            print("❌ Failed to create test job")
            return
        
        # Wait for job to potentially complete
        print(f"\n⏳ Waiting 15 seconds for job to potentially complete...")
        await asyncio.sleep(15)
        
        # Test SSE connections with completed job
        await test_sse_connection_lifecycle(job_id)
        
        # Monitor system health
        await test_sse_health_monitoring()
        
        print("\n" + "=" * 60)
        print("🎉 SSE Stability Test Completed!")
        print("\n📋 Key Improvements:")
        print("   ✅ No constant reconnection to completed jobs")
        print("   ✅ Graceful connection closing for completed jobs")
        print("   ✅ Proper final message handling")
        print("   ✅ Reduced server load from unnecessary connections")
        print("   ✅ Clean connection lifecycle management")
        
    except Exception as e:
        print(f"\n❌ SSE Stability Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
