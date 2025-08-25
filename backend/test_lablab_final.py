import asyncio
import sys
import os
sys.path.append(os.getcwd())
from app.core.agent import ScrapingAgent

async def test_lablab():
    print("Testing enhanced pipeline with lablab.ai...")
    agent = ScrapingAgent()
    url = 'https://lablab.ai/event'
    
    try:
        result = await agent.scrape_website(url, 'Extract hackathon event details including name, dates, description, and tech stack')
        print(f'Result type: {type(result)}')
        
        if isinstance(result, dict):
            print(f'Result keys: {list(result.keys())}')
            if 'data' in result:
                data = result['data']
                print(f'Data type: {type(data)}')
                if isinstance(data, list):
                    print(f'Data length: {len(data)}')
                    if len(data) > 0:
                        print(f'First item: {data[0]}')
                        if isinstance(data[0], dict):
                            print(f'First item keys: {list(data[0].keys())}')
            if 'metadata' in result:
                print(f'Metadata: {result["metadata"]}')
        
        print('✅ Test completed successfully!')
        return result
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_lablab())
