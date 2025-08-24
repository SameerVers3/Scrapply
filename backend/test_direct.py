#!/usr/bin/env python
"""
Simple standalone test for AIMLAPI
"""
import requests

def test_aimlapi_direct():
    """Test AIMLAPI with direct requests"""
    print("🧪 Testing AIMLAPI with direct requests...")
    
    api_key = "cf5b23a7188e408ab4861bcee0feb053"
    base_url = "https://api.aimlapi.com/v1"
    model = "chatgpt-4o-latest"
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Write a one-sentence story about numbers."
                    }
                ],
                "temperature": 0.1
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AIMLAPI working!")
            print(f"Response: {data['choices'][0]['message']['content']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_aimlapi_direct()
