#!/usr/bin/env python
"""
Test with shorter timeout and error handling
"""
import requests
import json

def test_aimlapi_with_timeout():
    """Test AIMLAPI with timeout and detailed error handling"""
    print("🧪 Testing AIMLAPI with timeout...")
    
    api_key = "cf5b23a7188e408ab4861bcee0feb053"
    base_url = "https://api.aimlapi.com/v1"
    
    # Try simpler model first
    models_to_try = ["gpt-4o", "gpt-3.5-turbo", "chatgpt-4o-latest"]
    
    for model in models_to_try:
        print(f"\n🔄 Trying model: {model}")
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
                            "content": "Hi"
                        }
                    ],
                    "max_tokens": 50
                },
                timeout=10  # 10 second timeout
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS with {model}!")
                print(f"Response: {data['choices'][0]['message']['content']}")
                return True
            else:
                print(f"❌ Error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout with {model}")
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error with {model}: {e}")
        except Exception as e:
            print(f"❌ Exception with {model}: {e}")
    
    return False

if __name__ == "__main__":
    success = test_aimlapi_with_timeout()
    if not success:
        print("\n❌ All models failed. Possible issues:")
        print("1. Invalid API key")
        print("2. Network connectivity")
        print("3. API service down")
        print("4. Rate limiting")
