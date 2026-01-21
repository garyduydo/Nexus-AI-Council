"""
import os
import requests

api_key = os.getenv('OPENROUTER_API_KEY')

if not api_key:
    print("❌ No API key found!")
    exit(1)

# Test each model individually
models_to_test = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

print("Testing OpenRouter models...")
print("="*70)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

for model in models_to_test:
    print(f"\nTesting: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                print(f"  ✅ WORKS - Response: {data['choices'][0]['message']['content'][:50]}")
        elif response.status_code == 404:
            print(f"  ❌ 404 ERROR - Model not available")
            error = response.json()
            if 'error' in error:
                print(f"     Reason: {error['error'].get('message', 'Unknown')}")
        elif response.status_code == 429:
            print(f"  ⚠️  RATE LIMITED - Try again later")
        else:
            print(f"  ❌ Error {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"  ❌ Connection error: {e}")

print("\n" + "="*70)
print("If all models show 404, check your privacy settings!")
"""