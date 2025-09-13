import requests
import json

def test_valid_requests():
    base_url = "http://127.0.0.1:8002"
    
    # 正常なリクエスト
    valid_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    print("Testing valid request...")
    response = requests.post(f"{base_url}/validate", json=valid_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_valid_requests()

