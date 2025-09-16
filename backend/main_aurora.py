from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import logging
import json

# Aurora Data API接続
from aurora_database import get_db, execute_sql
from models import User, Vendor
from schemas import UserCreate, UserResponse, VendorCreate, VendorResponse
from auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AIベンダー調査API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ヘルスチェック
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}

# ユーザー登録
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db = Depends(get_db)):
    # 既存ユーザー確認
    result = execute_sql(
        "SELECT id, email FROM users WHERE email = %s",
        [{"name": "email", "value": {"stringValue": user.email}}]
    )
    
    if result.get('records'):
        raise HTTPException(
            status_code=400,
            detail="このメールアドレスは既に登録されています"
        )

    # ユーザー作成
    hashed_password = get_password_hash(user.password)
    result = execute_sql(
        "INSERT INTO users (email, name, hashed_password) VALUES (%s, %s, %s) RETURNING id, email, name, created_at",
        [
            {"name": "email", "value": {"stringValue": user.email}},
            {"name": "name", "value": {"stringValue": user.name}},
            {"name": "hashed_password", "value": {"stringValue": hashed_password}}
        ]
    )
    
    if result.get('records'):
        record = result['records'][0]
        return UserResponse(
            id=record[0]['longValue'],
            email=record[1]['stringValue'],
            name=record[2]['stringValue'],
            created_at=record[3]['stringValue']
        )
    
    raise HTTPException(status_code=500, detail="ユーザー作成に失敗しました")

# ログイン
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
async def login_user(credentials: LoginRequest, db = Depends(get_db)):
    result = execute_sql(
        "SELECT id, email, name, hashed_password FROM users WHERE email = %s",
        [{"name": "email", "value": {"stringValue": credentials.email}}]
    )
    
    if not result.get('records'):
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが間違っています"
        )
    
    record = result['records'][0]
    user_id = record[0]['longValue']
    email = record[1]['stringValue']
    name = record[2]['stringValue']
    hashed_password = record[3]['stringValue']
    
    if not verify_password(credentials.password, hashed_password):
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが間違っています"
        )

    access_token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=30)
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ベンダー一覧
@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(db = Depends(get_db)):
    result = execute_sql("SELECT id, name, category, description, website_url, is_active FROM vendors WHERE is_active = true")
    
    vendors = []
    if result.get('records'):
        for record in result['records']:
            vendors.append(VendorResponse(
                id=record[0]['longValue'],
                name=record[1]['stringValue'],
                category=record[2]['stringValue'],
                description=record[3]['stringValue'] if record[3] else None,
                website_url=record[4]['stringValue'] if record[4] else None,
                is_active=record[5]['booleanValue']
            ))
    
    return vendors

# ベンダー作成
@app.post("/vendors", response_model=VendorResponse)
async def create_vendor(vendor: VendorCreate, db = Depends(get_db)):
    result = execute_sql(
        "INSERT INTO vendors (name, category, description, website_url, is_active) VALUES (%s, %s, %s, %s, %s) RETURNING id, name, category, description, website_url, is_active",
        [
            {"name": "name", "value": {"stringValue": vendor.name}},
            {"name": "category", "value": {"stringValue": vendor.category}},
            {"name": "description", "value": {"stringValue": vendor.description or ""}},
            {"name": "website_url", "value": {"stringValue": vendor.website_url or ""}},
            {"name": "is_active", "value": {"booleanValue": vendor.is_active}}
        ]
    )
    
    if result.get('records'):
        record = result['records'][0]
        return VendorResponse(
            id=record[0]['longValue'],
            name=record[1]['stringValue'],
            category=record[2]['stringValue'],
            description=record[3]['stringValue'],
            website_url=record[4]['stringValue'],
            is_active=record[5]['booleanValue']
        )
    
    raise HTTPException(status_code=500, detail="ベンダー作成に失敗しました")

# RAG検索機能
class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

class SearchResult(BaseModel):
    vendor_name: str
    category: str
    description: str
    score: float
    website_url: str = None

@app.post("/search/vendors", response_model=List[SearchResult])
async def search_vendors(search_request: SearchRequest, db = Depends(get_db)):
    """
    AIベンダー検索機能（RAGシステム）
    """
    try:
        # 現在は簡単な検索
        # 将来的なRAGシステムは後で実装
        query = search_request.query.lower()

        # ベンダー検索
        result = execute_sql("SELECT name, category, description, website_url FROM vendors WHERE is_active = true")
        
        results = []
        if result.get('records'):
            for record in result['records']:
                vendor_name = record[0]['stringValue']
                category = record[1]['stringValue']
                description = record[2]['stringValue'] if record[2] else ""
                website_url = record[3]['stringValue'] if record[3] else None
                
                score = 0.0
                
                # 簡単なスコアリング
                if query in vendor_name.lower():
                    score += 0.8
                if query in category.lower():
                    score += 0.6
                if description and query in description.lower():
                    score += 0.4

                if score > 0:
                    results.append(SearchResult(
                        vendor_name=vendor_name,
                        category=category,
                        description=description or "説明なし",
                        score=min(score, 1.0),
                        website_url=website_url
                    ))

        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)

        # 最大結果数で制限
        return results[:search_request.max_results]

    except Exception as e:
        logger.error(f"検索エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="検索処理でエラーが発生しました"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
