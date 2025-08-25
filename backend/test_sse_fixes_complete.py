#!/usr/bin/env python3
"""
Complete SSE Fix Test - Test the SSE connection behavior after fixes
"""
import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"

async def test_sse_fixes():
    """Test SSE connections with the new fixes"""
    print("🧪 Testing SSE fixes for connection stability and job ID corruption...")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a new job
        print("\n📋 Step 1: Creating a test job...")
        job_data = {
            "url": "https://example.com",
            "description": "Test job for SSE fixes",
            "user_id": "test-user"
        }
        
        async with session.post(f"{BASE_URL}/api/v1/scraping/requests", json=job_data) as response:
            if response.status == 201:
                result = await response.json()
                job_id = result['id']
                print(f"✅ Job created: {job_id}")
            else:
                print(f"❌ Failed to create job: {response.status}")
                return
        
        # Step 2: Connect to SSE stream and monitor for connection stability
        print(f"\n📡 Step 2: Testing SSE connection stability for job {job_id}...")
        
        connection_count = 0
        message_count = 0
        start_time = time.time()
        test_duration = 60  # Test for 60 seconds
        
        try:
            while time.time() - start_time < test_duration:
                connection_count += 1
                print(f"\n🔌 Connection attempt #{connection_count}")
                
                try:
                    async with session.get(f"{BASE_URL}/api/v1/scraping/jobs/stream/{job_id}") as response:
                        if response.status != 200:
                            print(f"❌ SSE connection failed: {response.status}")
                            await asyncio.sleep(2)
                            continue
                        
                        print(f"✅ SSE connection established (#{connection_count})")
                        connection_start = time.time()
                        
                        async for line in response.content:
                            if not line:
                                continue
                                
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    data = json.loads(line_str[6:])
                                    message_count += 1
                                    connection_duration = time.time() - connection_start
                                    
                                    print(f"📦 Message #{message_count} (after {connection_duration:.1f}s): {data.get('type', 'job_update')} - {data.get('status', 'N/A')} ({data.get('progress', 0)}%)")
                                    
                                    # Check for job ID corruption
                                    received_id = data.get('id')
                                    if received_id and received_id != job_id:
                                        print(f"🚨 JOB ID CORRUPTION DETECTED!")
                                        print(f"   Expected: {job_id}")
                                        print(f"   Received: {received_id}")
                                    
                                    # Check if job completed
                                    if data.get('final') or data.get('status') in ['ready', 'failed']:
                                        print(f"🏁 Job completed with status: {data.get('status')}")
                                        return
                                        
                                except json.JSONDecodeError as e:
                                    print(f"❌ Failed to parse SSE data: {e}")
                                except Exception as e:
                                    print(f"❌ Error processing SSE message: {e}")
                        
                        # If we get here, the connection was closed
                        connection_duration = time.time() - connection_start
                        print(f"📡 Connection #{connection_count} closed after {connection_duration:.1f}s")
                        
                        # If connection lasted less than 10 seconds, there might be an issue
                        if connection_duration < 10:
                            print(f"⚠️ Short connection duration detected: {connection_duration:.1f}s")
                            await asyncio.sleep(1)  # Brief pause before reconnect
                        
                except asyncio.TimeoutError:
                    print(f"⏰ Connection #{connection_count} timed out")
                    await asyncio.sleep(2)
                except aiohttp.ClientError as e:
                    print(f"❌ Connection #{connection_count} failed: {e}")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❌ Unexpected error in connection #{connection_count}: {e}")
                    await asyncio.sleep(2)
        
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n📊 Test Summary:")
        print(f"   ⏱️ Total test time: {total_time:.1f}s")
        print(f"   🔌 Total connections: {connection_count}")
        print(f"   📦 Total messages: {message_count}")
        print(f"   📈 Avg connection duration: {total_time/connection_count:.1f}s")
        print(f"   💬 Messages per connection: {message_count/connection_count:.1f}")
        
        # Assessment
        if connection_count > 10:
            print("⚠️ High number of reconnections detected - SSE stability issue may persist")
        elif connection_count <= 3:
            print("✅ Good connection stability - SSE fixes appear to be working")
        else:
            print("📊 Moderate connection stability - some improvement needed")

if __name__ == "__main__":
    asyncio.run(test_sse_fixes())
