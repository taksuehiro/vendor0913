import requests
import json

def test_basic_connection():
    try:
        response = requests.get("http://127.0.0.1:8000/")
        print(f"GET /: {response.status_code} - {response.json()}")
        
        response = requests.post("http://127.0.0.1:8000/test")
        print(f"POST /test: {response.status_code} - {response.json()}")
        
        return True
    except Exception as e:
        print(f"Basic connection failed: {e}")
        return False

if __name__ == "__main__":
    test_basic_connection()

