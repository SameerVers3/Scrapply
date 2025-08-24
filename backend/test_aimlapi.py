#!/usr/bin/env python
"""
Test script to verify AIMLAPI integration
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.agent import UnifiedAgent
from config.settings import settings

async def test_aimlapi():
    """Test AIMLAPI integration"""
    print("🧪 Testing AIMLAPI Integration...")
    print(f"API Key: {settings.OPENAI_API_KEY[:20]}...") 
    print(f"Model: {settings.OPENAI_MODEL}")
    print(f"Base URL: {settings.OPENAI_BASE_URL}")
    
    try:
        async with UnifiedAgent(
            settings.OPENAI_API_KEY, 
            settings.OPENAI_MODEL,
            settings.OPENAI_BASE_URL
        ) as agent:
            print("\n🚀 Making test request...")
            
            # Test a simple analysis request
            result = await agent._make_ai_request(
                messages=[{
                    "role": "user", 
                    "content": "Write a one-sentence story about numbers."
                }],
                temperature=0.1
            )
            
            print("✅ API Response received!")
            print(f"Response: {result.choices[0].message.content}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_aimlapi())
