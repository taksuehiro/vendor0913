from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# より寛容なCORS設定（デバッグ用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
async def root():
    return {"message": "FastAPI server is running", "status": "ok"}

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy", "service": "auth-api", "port": 8001}

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    logger.info(f"Login attempt for email: {credentials.email}")
    
    # デバッグ用：受信したデータをログ出力
    logger.info(f"Received credentials: email={credentials.email}, password={'*' * len(credentials.password)}")
    
    return {
        "message": "Login successful", 
        "email": credentials.email,
        "status": "success"
    }

# OPTIONS リクエストを明示的に処理
@app.options("/auth/login")
async def login_options():
    logger.info("OPTIONS request received for /auth/login")
    return {"message": "CORS preflight successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)