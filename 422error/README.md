このプロジェクト構成のポイントは：
段階的な問題切り分け

基本接続: FastAPIが正常に動作するか
CORS単体: CORS設定が正しく動作するか
バリデーション: Pydanticで422エラーが正しく発生するか
統合: 全体が連携して動作するか

重要なデバッグポイント

詳細ログ: すべてのリクエスト/レスポンスをログ出力
生データ確認: JSONパース前のリクエストボディを確認
段階的テスト: Python → curl → ブラウザの順でテスト
意図的な422エラー: 正常に422エラーが発生することを確認

実際の調査アプローチ

まず 1-basic-server で基本的なFastAPI動作を確認
3-pydantic-test で意図的に422エラーを発生させて、正常に動作することを確認
2-cors-test でCORSが正しく設定されているか確認
最後に 4-integration-test で全体統合

この方法なら、どの段階で問題が発生しているかを確実に特定できます。特に 3-pydantic-test/test-invalid.py では意図的に422エラーを発生させるので、FastAPIが正しく422エラーを返すかどうかを確認できます。
Cursorに投げる際は、「この段階的テスト構成で、どの段階で失敗するかを確認したい」と伝えてください。






422エラー段階的デバッグプロジェクト
プロジェクト構成
debug-422/
├── 1-basic-server/
│   ├── server.py           # 最小限のFastAPI
│   └── test.py            # Pythonクライアント
├── 2-cors-test/
│   ├── server.py           # CORS設定付きFastAPI
│   ├── index.html          # 静的HTML
│   └── test-cors.js        # CORS専用テスト
├── 3-pydantic-test/
│   ├── server.py           # Pydanticバリデーション
│   ├── test-valid.py       # 正常なリクエスト
│   └── test-invalid.py     # 422エラーを意図的に発生
├── 4-integration-test/
│   ├── server.py           # 完全版FastAPI
│   ├── index.html          # 完全版フロントエンド
│   └── debug.js           # 詳細ログ付きJS
└── run-tests.py           # 全テスト実行スクリプト
1. 基本サーバーテスト (1-basic-server/)
server.py
pythonfrom fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Server is running"}

@app.get("/test")
def test():
    return {"test": "success", "method": "GET"}

@app.post("/test")
def test_post():
    return {"test": "success", "method": "POST"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
test.py
pythonimport requests
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
2. CORS専用テスト (2-cors-test/)
server.py
pythonfrom fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# 段階的なCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 最初は全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/cors-test")
def cors_test():
    return {"cors": "enabled", "origin": "allowed"}

@app.post("/cors-test")
def cors_test_post():
    return {"cors": "POST enabled", "origin": "allowed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
index.html
html<!DOCTYPE html>
<html>
<head>
    <title>CORS Test</title>
</head>
<body>
    <h1>CORS Test</h1>
    <button onclick="testCors()">Test CORS</button>
    <div id="result"></div>
    <script src="test-cors.js"></script>
</body>
</html>
test-cors.js
javascriptasync function testCors() {
    const result = document.getElementById('result');
    result.innerHTML = '';
    
    const tests = [
        { method: 'GET', url: 'http://127.0.0.1:8001/cors-test' },
        { method: 'POST', url: 'http://127.0.0.1:8001/cors-test' }
    ];
    
    for (const test of tests) {
        try {
            console.log(`Testing ${test.method} ${test.url}`);
            
            const response = await fetch(test.url, {
                method: test.method,
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            result.innerHTML += `<p style="color:green">${test.method}: SUCCESS - ${JSON.stringify(data)}</p>`;
            
        } catch (error) {
            result.innerHTML += `<p style="color:red">${test.method}: FAILED - ${error.message}</p>`;
            console.error(`${test.method} failed:`, error);
        }
    }
}
3. Pydanticバリデーションテスト (3-pydantic-test/)
server.py
pythonfrom fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
import uvicorn
import json

app = FastAPI()

class TestModel(BaseModel):
    email: str
    password: str
    optional_field: str = "default"

@app.post("/validate")
async def validate_data(request: Request, data: TestModel):
    # リクエストボディの生ログを確認
    body = await request.body()
    print(f"Raw body: {body}")
    
    return {
        "message": "Validation successful",
        "received": data.dict(),
        "raw_body_length": len(body)
    }

@app.post("/validate-manual")
async def validate_manual(request: Request):
    try:
        body = await request.body()
        print(f"Raw body: {body}")
        
        # JSON解析を手動で試行
        try:
            json_data = json.loads(body)
            print(f"Parsed JSON: {json_data}")
        except json.JSONDecodeError as e:
            return {"error": "Invalid JSON", "details": str(e)}
        
        # Pydanticバリデーションを手動で試行
        try:
            model = TestModel(**json_data)
            return {"message": "Manual validation successful", "data": model.dict()}
        except ValidationError as e:
            return {"error": "Validation error", "details": e.errors()}
            
    except Exception as e:
        return {"error": "Unexpected error", "details": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
test-valid.py
pythonimport requests
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
test-invalid.py
pythonimport requests
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
4. 統合テスト (4-integration-test/)
server.py
pythonfrom fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import logging

# 詳細なログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # リクエストボディを読む（一度だけ）
    body = await request.body()
    logger.info(f"Body length: {len(body)}")
    logger.info(f"Body content: {body}")
    
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    
    return response

@app.post("/auth/login")
async def login(request: Request, credentials: LoginRequest):
    logger.info(f"Login attempt: {credentials.email}")
    return {
        "message": "Login successful",
        "email": credentials.email
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="debug")
debug.js
javascriptasync function debugLogin() {
    console.clear();
    console.log('=== Starting debug login test ===');
    
    const testData = {
        email: 'test@example.com',
        password: 'password123'
    };
    
    console.log('Test data:', testData);
    console.log('JSON string:', JSON.stringify(testData));
    console.log('JSON string length:', JSON.stringify(testData).length);
    
    try {
        const response = await fetch('http://127.0.0.1:8003/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        console.log('Response received');
        console.log('Status:', response.status);
        console.log('Status text:', response.statusText);
        console.log('Headers:', Object.fromEntries(response.headers.entries()));
        
        const responseText = await response.text();
        console.log('Response text:', responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log('Parsed response:', data);
            document.getElementById('result').innerHTML = 
                `<div style="color:green">SUCCESS: ${JSON.stringify(data, null, 2)}</div>`;
        } else {
            console.error('Request failed with status:', response.status);
            document.getElementById('result').innerHTML = 
                `<div style="color:red">FAILED (${response.status}): ${responseText}</div>`;
        }
        
    } catch (error) {
        console.error('Network error:', error);
        document.getElementById('result').innerHTML = 
            `<div style="color:red">NETWORK ERROR: ${error.message}</div>`;
    }
}
5. 全テスト実行スクリプト (run-tests.py)
pythonimport subprocess
import time
import requests
import os

def run_test_sequence():
    tests = [
        {
            "name": "Basic Server Test",
            "server": "1-basic-server/server.py",
            "test": "1-basic-server/test.py",
            "port": 8000
        },
        {
            "name": "CORS Test", 
            "server": "2-cors-test/server.py",
            "test": None,  # ブラウザテスト
            "port": 8001
        },
        {
            "name": "Pydantic Validation Test",
            "server": "3-pydantic-test/server.py", 
            "test": "3-pydantic-test/test-valid.py",
            "port": 8002
        }
    ]
    
    for test in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test['name']}")
        print(f"{'='*50}")
        
        # サーバー起動
        server_process = subprocess.Popen(
            ["python", test["server"]], 
            cwd=os.path.dirname(test["server"]) or "."
        )
        
        # サーバー起動待ち
        time.sleep(2)
        
        # ヘルスチェック
        try:
            requests.get(f"http://127.0.0.1:{test['port']}/", timeout=5)
            print("✓ Server started successfully")
        except:
            print("✗ Server failed to start")
            server_process.terminate()
            continue
        
        # テスト実行
        if test["test"]:
            subprocess.run(["python", test["test"]])
        
        # サーバー終了
        server_process.terminate()
        time.sleep(1)

if __name__ == "__main__":
    run_test_sequence()
実行順序

基本接続テスト: python 1-basic-server/server.py → python 1-basic-server/test.py
CORS単体テスト: python 2-cors-test/server.py → ブラウザで 2-cors-test/index.html
バリデーションテスト: python 3-pydantic-test/server.py → python 3-pydantic-test/test-invalid.py
統合テスト: python 4-integration-test/server.py → ブラウザで 4-integration-test/index.html

この構成により、問題がサーバー起動、CORS、Pydanticバリデーション、フロントエンド統合のどの段階で発生しているかを特定できます。
