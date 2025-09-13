from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# データベースURL（aiosqliteをsqliteに変更）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# エンジン作成
engine = create_engine(DATABASE_URL, echo=True)

# セッションファクトリー
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()

# 依存性注入用の関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()