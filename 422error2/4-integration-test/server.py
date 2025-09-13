from fastapi import FastAPI, HTTPException, Request
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
    allow_origins=["*"],  # デバッグ用に全許可
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
