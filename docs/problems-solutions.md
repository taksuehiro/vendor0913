# 422エラー問題と解決過程の記録

## 問題の概要

### 発生した問題
- **エラー**: HTTP 422 (Unprocessable Entity)
- **発生箇所**: フロントエンド（Next.js）からバックエンド（FastAPI）へのログインリクエスト
- **症状**: ログイン画面で認証情報を入力しても、422エラーが発生してログインできない

### 影響範囲
- ユーザー認証機能が完全に使用不可能
- ダッシュボードへのアクセスができない
- アプリケーションの核心機能が停止

## 問題の根本原因

### 1. パラメータ形式の不一致

**バックエンドの期待する形式:**
```python
@app.post("/auth/login")
async def login_user(email: str, password: str, db: Session = Depends(get_db)):
```

**フロントエンドが送信する形式:**
```typescript
const response = await fetch(`${this.baseUrl}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: credentials.email, password: credentials.password })
});
```

### 2. データ形式の不一致
- **バックエンド**: 個別のパラメータ（`email: str, password: str`）を期待
- **フロントエンド**: JSONオブジェクト（`{"email": "...", "password": "..."}`）を送信
- **結果**: FastAPIがリクエストボディを正しく解析できず、422エラーを返す

## 解決過程

### 段階1: 問題の切り分け

**422error2プロジェクト**を作成し、段階的デバッグを実施：

#### 1-basic-server: 基本接続テスト
```python
# 最小限のFastAPIサーバー
@app.get("/")
def root():
    return {"message": "Server is running"}

@app.post("/test")
def test_post():
    return {"test": "success", "method": "POST"}
```
**結果**: ✅ FastAPIの基本動作は正常

#### 2-cors-test: CORS設定テスト
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**結果**: ✅ CORS設定は正常

#### 3-pydantic-test: バリデーションテスト
```python
class TestModel(BaseModel):
    email: str
    password: str

@app.post("/validate")
async def validate_data(data: TestModel):
    return {"message": "Validation successful"}
```
**結果**: ✅ FastAPIは正しく422エラーを返す

#### 4-integration-test: 統合テスト
```python
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    return {"message": "Login successful", "email": credentials.email}
```
**結果**: ✅ 統合テストが成功

### 段階2: 根本原因の特定

段階的テストにより以下が判明：
1. FastAPI自体は正常に動作
2. CORS設定に問題なし
3. Pydanticバリデーションは正常
4. **問題は元のプロジェクトのエンドポイント定義**

### 段階3: 修正の実施

**修正前:**
```python
@app.post("/auth/login")
async def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        # エラーハンドリング
```

**修正後:**
```python
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
async def login_user(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        # エラーハンドリング
```

## 解決結果

### 修正後の動作
- ✅ ログイン機能が正常に動作
- ✅ ダッシュボードにアクセス可能
- ✅ ユーザー認証が完全に機能
- ✅ 422エラーが完全に解消

### 技術的改善点
1. **型安全性の向上**: Pydanticモデルによるリクエスト検証
2. **エラーハンドリングの改善**: より明確なエラーメッセージ
3. **コードの可読性向上**: 構造化されたリクエスト処理

## 学んだ教訓

### 1. 段階的デバッグの重要性
- 複雑な問題を小さな単位に分割して検証
- 各コンポーネントの動作を個別に確認
- 問題の範囲を段階的に絞り込み

### 2. データ形式の整合性
- フロントエンドとバックエンドのデータ形式を一致させる重要性
- API設計時の型定義の重要性
- Pydanticモデルの活用による型安全性の確保

### 3. テスト駆動開発の有効性
- 最小限のテストケースから始める
- 意図的にエラーを発生させて動作確認
- 統合テストによる全体動作の検証

## 今後の対策

### 1. API設計の改善
- すべてのエンドポイントでPydanticモデルを使用
- リクエスト/レスポンスの型定義を明確化
- APIドキュメントの整備

### 2. テスト環境の整備
- 段階的テストの自動化
- CI/CDパイプラインでの継続的テスト
- エラーケースの網羅的テスト

### 3. 開発プロセスの改善
- フロントエンドとバックエンドの連携確認
- コードレビューでの型安全性チェック
- デバッグ用のログ出力の充実

## 関連ファイル

### 修正されたファイル
- `backend/main.py`: ログインエンドポイントの修正

### デバッグ用プロジェクト
- `422error2/`: 段階的デバッグプロジェクト
  - `1-basic-server/`: 基本接続テスト
  - `2-cors-test/`: CORS設定テスト
  - `3-pydantic-test/`: バリデーションテスト
  - `4-integration-test/`: 統合テスト

### 参考資料
- FastAPI公式ドキュメント: https://fastapi.tiangolo.com/
- Pydantic公式ドキュメント: https://pydantic-docs.helpmanual.io/
- Next.js公式ドキュメント: https://nextjs.org/docs

---

# AWS Amplify デプロイ問題と解決過程の記録

## 問題の概要

### 発生した問題
- **エラー**: 404 Not Found / デプロイ失敗
- **発生箇所**: AWS Amplify Hosting でのNext.js 15アプリケーションのデプロイ
- **症状**: デプロイは成功するが、アクセス時に404エラーが発生

### 影響範囲
- 本番環境でのアプリケーションが使用不可能
- ユーザーがアプリケーションにアクセスできない
- ビジネス機能の提供が停止

## 問題の根本原因

### 1. モノレポ設定の不備

**Amplifyの期待する設定:**
- モノレポ構造の正しい認識
- `frontend`ディレクトリの正しい指定
- `package.json`の正しい読み取り

**実際の設定:**
- `amplify.yml`の設定が不適切
- 環境変数の設定が不完全
- ディレクトリ構造の認識エラー

### 2. 設定ファイルの不整合

**問題のあった設定:**
```yaml
# 古い設定（単一アプリ形式）
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - cd frontend
        - npm run build
  artifacts:
    baseDirectory: frontend/.next
```

**エラーメッセージ:**
- `CustomerError: Monorepo spec provided without "applications" key`
- `Cannot read 'next' version in package.json`

## 解決過程

### 段階1: 問題の特定

**エラー分析:**
1. **Monorepo spec provided without "applications" key**
   - Amplifyがモノレポとして認識しているが、`amplify.yml`に`applications`キーがない
   - 環境変数`AMPLIFY_MONOREPO_APP_ROOT`が設定されているが、YAML設定が対応していない

2. **Cannot read 'next' version in package.json**
   - `frontend`ディレクトリに移動する前に`package.json`を読み取ろうとしている
   - モノレポ設定が正しく動作していない

### 段階2: 設定の修正

**修正前の`amplify.yml`:**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - cd frontend
        - npm run build
  artifacts:
    baseDirectory: frontend/.next
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
      - frontend/.next/cache/**/*
```

**修正後の`amplify.yml`:**
```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - nvm install 20
            - nvm use 20
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: .next
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
          - .next/cache/**/*
```

### 段階3: 環境変数の設定

**必要な環境変数:**
- `AMPLIFY_MONOREPO_APP_ROOT: frontend` ✅
- `AMPLIFY_DIFF_DEPLOY: false` ✅

**環境変数の役割:**
- `AMPLIFY_MONOREPO_APP_ROOT`: モノレポのアプリケーションルートを指定
- `AMPLIFY_DIFF_DEPLOY`: 差分デプロイを無効化（安定性向上）

### 段階4: Node.jsバージョンの固定

**追加した設定:**
```yaml
preBuild:
  commands:
    - nvm install 20
    - nvm use 20
    - npm ci
```

**理由:**
- Node.jsバージョンの不一致によるビルドエラーを防止
- 安定したビルド環境の確保
- Next.js 15との互換性確保

## 解決結果

### 修正後の動作
- ✅ デプロイが正常に完了
- ✅ 404エラーが解消
- ✅ アプリケーションが正常にアクセス可能
- ✅ モノレポ設定が正しく動作

### 技術的改善点
1. **モノレポ設定の正規化**: `applications`キーによる適切な設定
2. **環境変数の最適化**: 必要な変数のみを設定
3. **Node.jsバージョンの固定**: 安定したビルド環境の確保
4. **ディレクトリ構造の最適化**: `appRoot`による適切なディレクトリ指定

## 学んだ教訓

### 1. モノレポ設定の重要性
- Amplifyのモノレポ認識とYAML設定の整合性
- 環境変数とYAML設定の連携
- ディレクトリ構造の正しい指定

### 2. 設定ファイルの構造化
- `applications`キーによるモノレポ対応
- `appRoot`によるアプリケーションルートの指定
- 不要な`cd`コマンドの削除

### 3. 環境変数の管理
- 必要な環境変数のみを設定
- 冗長な設定の削除
- 設定の一元管理

## 今後の対策

### 1. デプロイ設定の標準化
- モノレポ設定のテンプレート化
- 環境変数の最小化
- 設定ファイルのバリデーション

### 2. ビルド環境の安定化
- Node.jsバージョンの固定
- 依存関係の管理
- キャッシュの最適化

### 3. エラーハンドリングの改善
- デプロイログの詳細分析
- エラーメッセージの理解
- 段階的な問題解決

## 関連ファイル

### 修正されたファイル
- `amplify.yml`: モノレポ設定の修正
- Amplify Console: 環境変数の設定

### 参考資料
- AWS Amplify公式ドキュメント: https://docs.aws.amazon.com/amplify/
- Next.js公式ドキュメント: https://nextjs.org/docs
- AWS Amplify Monorepo設定: https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html

---

**作成日**: 2025年9月13日  
**問題解決日**: 2025年9月13日  
**解決時間**: 約3時間（設定修正・テスト含む）

