from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import logging
import json
import boto3
import os
from datetime import datetime
from openai import OpenAI
from typing import List

# Aurora Data API接続
from aurora_database import get_db, execute_sql
from models import User, Vendor
from schemas import UserCreate, UserResponse, VendorCreate, VendorResponse
from auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta

# S3設定
S3_BUCKET_NAME = "vendor0913-documents"
S3_REGION = "ap-northeast-1"
s3_client = boto3.client('s3', region_name=S3_REGION)

# OpenAI設定
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AIベンダー調査API", version="1.0.0")

# 埋め込み機能
def create_embedding(text: str) -> List[float]:
    """テキストをベクトル化"""
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured"
        )
    
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"埋め込み作成エラー: {str(e)}"
        )

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

# ドキュメントアップロード
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """ドキュメントをS3にアップロード"""
    try:
        # ファイル名の生成（タイムスタンプ付き）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
        s3_key = f"vendor0913-folder/{timestamp}_{file.filename}"
        
        # ファイルをS3にアップロード
        file_content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type or 'application/octet-stream'
        )
        
        logger.info(f"File uploaded to S3: {s3_key}")
        
        return {
            "message": "ファイルが正常にアップロードされました",
            "s3_key": s3_key,
            "filename": file.filename,
            "size": len(file_content)
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ファイルアップロードエラー: {str(e)}"
        )

# ドキュメント処理・埋め込み・保存
@app.post("/ingest")
async def ingest_document(s3_key: str):
    """S3のドキュメントを処理してAuroraに保存"""
    try:
        # S3からファイルを取得
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        file_content = response['Body'].read()
        
        # ファイルタイプに応じて処理
        if s3_key.endswith('.pdf'):
            # PDF処理（将来実装）
            content = f"PDF content from {s3_key}"
        elif s3_key.endswith('.txt'):
            content = file_content.decode('utf-8')
        else:
            content = file_content.decode('utf-8', errors='ignore')
        
        # ドキュメントを分割（簡易版）
        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
        
        # 各チャンクをデータベースに保存
        for i, chunk in enumerate(chunks):
            metadata = {
                "s3_key": s3_key,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "uploaded_at": datetime.now().isoformat()
            }
            
            # 埋め込みベクトルを作成
            try:
                embedding = create_embedding(chunk)
                embedding_str = json.dumps(embedding)
            except Exception as e:
                logger.warning(f"Embedding creation failed for chunk {i}: {e}")
                embedding_str = None
            
            execute_sql(
                "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s, %s)",
                [
                    {"name": "content", "value": {"stringValue": chunk}},
                    {"name": "embedding", "value": {"stringValue": embedding_str}} if embedding_str else {"name": "embedding", "value": {"isNull": True}},
                    {"name": "metadata", "value": {"stringValue": json.dumps(metadata)}}
                ]
            )
        
        logger.info(f"Document ingested: {s3_key}, {len(chunks)} chunks")
        
        return {
            "message": "ドキュメントが正常に処理されました",
            "s3_key": s3_key,
            "chunks_created": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメント処理エラー: {str(e)}"
        )

# RAG検索機能
@app.post("/search/documents")
async def search_documents(query: str, limit: int = 5):
    """ベクトル検索でドキュメントを検索"""
    try:
        # クエリをベクトル化
        query_embedding = create_embedding(query)
        query_embedding_str = json.dumps(query_embedding)
        
        # ベクトル検索を実行
        result = execute_sql(
            """
            SELECT content, metadata, 
                   (embedding <=> %s::vector) as distance
            FROM documents 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            [
                {"name": "query_embedding1", "value": {"stringValue": query_embedding_str}},
                {"name": "query_embedding2", "value": {"stringValue": query_embedding_str}},
                {"name": "limit", "value": {"longValue": limit}}
            ]
        )
        
        # 結果を整形
        documents = []
        if result.get('records'):
            for record in result['records']:
                content = record[0]['stringValue']
                metadata = json.loads(record[1]['stringValue'])
                distance = float(record[2]['doubleValue'])
                
                documents.append({
                    "content": content,
                    "metadata": metadata,
                    "similarity_score": 1 - distance  # 距離を類似度に変換
                })
        
        return {
            "query": query,
            "documents": documents,
            "total_found": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメント検索エラー: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
