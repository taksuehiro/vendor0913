from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import logging
import json

# 既存のインポート
from database import get_db, engine
from models import Base, User, Vendor
from schemas import UserCreate, UserResponse, VendorCreate, VendorResponse
from auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta

# データベーステーブル作成
Base.metadata.create_all(bind=engine)

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

# 既存のヘルスチェック
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}

# ユーザー登録
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # 既存ユーザーチェック
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="このメールアドレスは既に登録されています"
        )
    
    # 新規ユーザー作成
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# ログイン
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
async def login_user(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ベンダー一覧取得
@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    return vendors

# ベンダー作成
@app.post("/vendors", response_model=VendorResponse)
async def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    db_vendor = Vendor(**vendor.dict())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

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
async def search_vendors(search_request: SearchRequest, db: Session = Depends(get_db)):
    """
    AIベンダー検索機能（RAGシステム）
    """
    try:
        # 現在は簡易的な検索を実装
        # 実際のRAGシステムは後で実装予定
        query = search_request.query.lower()
        
        # ベンダーを検索
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        
        # 簡易的なスコアリング（実際のRAGでは類似度計算）
        results = []
        for vendor in vendors:
            score = 0.0
            
            # 名前でのマッチング
            if query in vendor.name.lower():
                score += 0.8
            if query in vendor.category.lower():
                score += 0.6
            if vendor.description and query in vendor.description.lower():
                score += 0.4
                
            if score > 0:
                results.append(SearchResult(
                    vendor_name=vendor.name,
                    category=vendor.category,
                    description=vendor.description or "説明なし",
                    score=min(score, 1.0),
                    website_url=vendor.website_url
                ))
        
        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 最大結果数で制限
        return results[:search_request.max_results]
        
    except Exception as e:
        logger.error(f"検索エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="検索処理中にエラーが発生しました"
        )

# テストユーザーを作成
def create_test_user():
    from database import SessionLocal
    from auth import get_password_hash
    
    db = SessionLocal()
    try:
        # 既存ユーザーをチェック
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if not existing_user:
            # テストユーザーを作成
            hashed_password = get_password_hash("password")
            test_user = User(
                email="test@example.com",
                hashed_password=hashed_password,
                name="テストユーザー"
            )
            db.add(test_user)
            db.commit()
            print("テストユーザーを作成しました: test@example.com")
        else:
            print("テストユーザーは既に存在します")
    except Exception as e:
        print(f"テストユーザー作成エラー: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # テストユーザーを作成
    create_test_user()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)