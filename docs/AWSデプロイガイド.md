# AWS デプロイガイド

## 概要
このプロジェクトをAWSにデプロイするための詳細手順です。

## 前提条件
- AWS CLI が設定済み
- 適切なIAM権限を持っている
- 会社のAWSアカウントにアクセス可能

## デプロイ手順

### 1. フロントエンド (Amplify Hosting)

#### 1.1 GitHubリポジトリ作成
```bash
# プロジェクトをGitリポジトリに変換
git init
git add .
git commit -m "Initial commit"

# GitHubにプッシュ（会社のリポジトリに）
git remote add origin <会社のGitHubリポジトリURL>
git push -u origin main
```

#### 1.2 Amplify Hosting設定
1. AWS Amplify コンソールにアクセス
2. 「新しいアプリをホスト」を選択
3. GitHub を選択し、リポジトリを接続
4. ビルド設定を確認：
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
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

#### 1.3 環境変数設定
Amplify コンソールで以下の環境変数を設定：
- `NEXT_PUBLIC_API_BASE`: API Gateway のエンドポイントURL
- `NEXTAUTH_SECRET`: 認証用シークレット
- `NEXTAUTH_URL`: Amplify のドメインURL

### 2. バックエンド (Lambda + API Gateway)

#### 2.1 Lambda関数準備
```bash
# バックエンドディレクトリで
cd backend
pip install -r requirements.txt -t .
zip -r lambda-deployment.zip .
```

#### 2.2 Lambda関数作成
1. AWS Lambda コンソールにアクセス
2. 「関数の作成」を選択
3. ランタイム: Python 3.9
4. 関数コードをアップロード（lambda-deployment.zip）
5. 環境変数設定：
   - `DATABASE_URL`: RDS接続文字列
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `NEXTAUTH_SECRET`: 認証用シークレット

#### 2.3 API Gateway設定
1. API Gateway コンソールにアクセス
2. 「HTTP API」を作成
3. Lambda統合を設定
4. CORS設定：
   ```json
   {
     "allowCredentials": true,
     "allowHeaders": ["*"],
     "allowMethods": ["*"],
     "allowOrigins": ["https://<amplify-domain>"]
   }
   ```

### 3. データベース (RDS PostgreSQL + pgvector)

#### 3.1 RDSインスタンス作成
1. RDS コンソールにアクセス
2. 「データベースの作成」
3. エンジン: PostgreSQL
4. インスタンスクラス: db.t3.micro（開発用）
5. ストレージ: 20GB
6. セキュリティグループでLambdaからのアクセスを許可

#### 3.2 pgvector拡張有効化
```sql
-- RDSに接続後
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 3.3 テーブル作成
```sql
-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ドキュメントテーブル
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    source_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- チャンクテーブル（ベクトル埋め込み）
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. ストレージ (S3)

#### 4.1 S3バケット作成
1. S3 コンソールにアクセス
2. バケットを作成（会社の命名規則に従う）
3. バージョニングを有効化
4. 適切なアクセス権限を設定

### 5. セキュリティ設定

#### 5.1 Secrets Manager
機密情報をSecrets Managerに保存：
- データベース認証情報
- APIキー
- 認証シークレット

#### 5.2 IAMロール
Lambda実行ロールに以下の権限を付与：
- RDS接続権限
- S3読み取り権限
- Secrets Manager読み取り権限

### 6. 監視・ログ

#### 6.1 CloudWatch
- Lambda関数のログ
- API Gatewayのアクセスログ
- RDSのパフォーマンスインサイト

#### 6.2 アラート設定
- エラー率の監視
- レスポンス時間の監視
- データベース接続数の監視

## デプロイ後の確認事項

### 1. 動作確認
- [ ] フロントエンドが正常に表示される
- [ ] ログイン機能が動作する
- [ ] APIエンドポイントが応答する
- [ ] データベース接続が正常
- [ ] 検索機能が動作する

### 2. セキュリティ確認
- [ ] HTTPSが有効
- [ ] CORS設定が適切
- [ ] 認証が正常に動作
- [ ] 機密情報が適切に管理されている

### 3. パフォーマンス確認
- [ ] レスポンス時間が許容範囲内
- [ ] データベースクエリが最適化されている
- [ ] キャッシュが適切に設定されている

## トラブルシューティング

### よくある問題
1. **CORS エラー**: API GatewayのCORS設定を確認
2. **データベース接続エラー**: セキュリティグループとIAMロールを確認
3. **環境変数エラー**: Lambda関数の環境変数設定を確認
4. **ビルドエラー**: Amplifyのビルドログを確認

### ログの確認方法
```bash
# Lambdaログ
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# API Gatewayログ
aws logs describe-log-groups --log-group-name-prefix /aws/apigateway/
```

## コスト最適化
- RDSインスタンスの適切なサイジング
- Lambda関数のメモリ設定最適化
- S3のライフサイクルポリシー設定
- CloudWatchログの保持期間設定

## 今後の拡張計画
- 独自ドメインの設定
- CDN（CloudFront）の導入
- 自動スケーリングの設定
- CI/CDパイプラインの構築
