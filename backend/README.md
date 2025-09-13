# AIベンダー調査API

## 概要
LangChainを使用したAIベンダー調査システムのバックエンドAPI

## 技術スタック
- **FastAPI**: Webフレームワーク
- **Uvicorn**: ASGIサーバー
- **Pydantic**: データバリデーション
- **Python 3.9+**: プログラミング言語

## 起動手順

### 1. 仮想環境有効化
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. サーバー起動
```bash
# 開発モード（自動リロード）
uvicorn main:app --reload --port 8000

# 本番モード
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 確認URL

### ヘルスチェック
- **URL**: http://127.0.0.1:8000/health
- **レスポンス**: `{"status":"ok"}`

### API仕様書（Swagger UI）
- **URL**: http://127.0.0.1:8000/docs
- **説明**: インタラクティブなAPI仕様書

### ReDoc
- **URL**: http://127.0.0.1:8000/redoc
- **説明**: 別形式のAPI仕様書

## プロジェクト構造

```
backend/
├── main.py              # FastAPIアプリケーション
├── requirements.txt     # 依存関係
├── README.md           # このファイル
└── .venv/              # Python仮想環境
```

## 開発環境

### 必要な環境
- Python 3.9以上
- pip（パッケージマネージャー）

### 推奨環境
- Visual Studio Code
- Python拡張機能
- REST Client拡張機能

## API仕様

### エンドポイント一覧

#### GET /health
- **説明**: ヘルスチェック
- **レスポンス**: `{"status":"ok"}`

## トラブルシューティング

### よくある問題

#### 1. ポートが使用中
```bash
# エラー: Address already in use
# 解決: 別のポートを使用
uvicorn main:app --reload --port 8001
```

#### 2. 仮想環境が有効にならない
```bash
# PowerShell実行ポリシーエラーの場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. 依存関係のインストールエラー
```bash
# pipを最新版に更新
python -m pip install --upgrade pip
```

## 今後の拡張予定

- [ ] データベース連携（SQLite → PostgreSQL）
- [ ] 認証システム（JWT）
- [ ] RAGシステム（LangChain）
- [ ] ベンダー検索API
- [ ] ログ機能強化

## ライセンス

© 2024 AIベンダー調査システム. All rights reserved.


