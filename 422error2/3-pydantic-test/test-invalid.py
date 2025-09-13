import requests
import json

def test_invalid_requests():
    base_url = "http://127.0.0.1:8002"
    
    # 422エラーを発生させるテストケース
    test_cases = [
        {"name": "Missing email", "data": {"password": "test"}},
        {"name": "Missing password", "data": {"email": "test@example.com"}},
        {"name": "Empty data", "data": {}},
        {"name": "Wrong type", "data": {"email": 123, "password": "test"}},
        {"name": "Invalid JSON", "raw": "{'invalid': json}"},
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        
        try:
            if 'raw' in case:
                # 生のテキストを送信
                response = requests.post(
                    f"{base_url}/validate-manual",
                    data=case['raw'],
                    headers={'Content-Type': 'application/json'}
                )
            else:
                response = requests.post(f"{base_url}/validate", json=case['data'])
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_invalid_requests()

