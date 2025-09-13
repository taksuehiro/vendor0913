# AWS Amplify デプロイ問題 - 現在の状況

## 問題の概要

AWS Amplify HostingでNext.js 15.5.3アプリケーションのデプロイが成功しているが、アクセス時に404エラーが発生している。

## 現在の状況

### デプロイ状況
- ✅ **デプロイ成功**: Amplifyでビルド・デプロイが完了
- ❌ **404エラー**: ルートページ（`/`）にアクセスできない
- 🔄 **自動デプロイ**: GitHubプッシュ時に自動でデプロイが実行される

### エラー詳細
```
HTTP ERROR 404
この main.d15ngbpzg9c7px.amplifyapp.com ページが見つかりません
```

## 技術スタック

- **フロントエンド**: Next.js 15.5.3 (App Router)
- **認証**: NextAuth.js (Credentials Provider)
- **UI**: Tailwind CSS v4 + shadcn/ui
- **デプロイ先**: AWS Amplify Hosting
- **バックエンド**: FastAPI (別途開発中)

## 現在の設定ファイル

### next.config.ts
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: 'export', // 静的エクスポートを無効化
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
```

### amplify.yml
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

### プロジェクト構造
```
vendor0913/
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   │       └── page.tsx
│   │   ├── (app)/
│   │   │   └── dashboard/
│   │   │       └── page.tsx
│   │   ├── api/
│   │   │   └── auth/
│   │   │       └── [...nextauth]/
│   │   │           └── route.ts
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   ├── lib/
│   └── package.json
├── backend/
└── amplify.yml
```

## 試した解決策の履歴

### 1. 初回デプロイ失敗（ESLintエラー）
**問題**: `<a>`タグでページ内ナビゲーション
**解決**: `<Link>`コンポーネントに変更
**結果**: デプロイ成功

### 2. 404エラー（静的ファイル配置問題）
**問題**: デプロイ成功だが404エラー
**原因**: 静的エクスポート設定の不備
**試した解決策**: 
- `next.config.ts`に`output: 'export'`を追加
- `amplify.yml`の`baseDirectory`を`frontend/out`に変更
**結果**: NextAuth.jsのAPIルートでビルドエラー

### 3. NextAuth.js APIルートエラー
**問題**: 静的エクスポートとNextAuth.jsの互換性問題
**エラー**: 
```
Error: export const dynamic = "force-static"/export const revalidate not configured on route "/api/auth/[...nextauth]" with "output: export"
```
**解決策**: SSRに戻す（静的エクスポートを無効化）
**結果**: デプロイ成功、しかし404エラーが継続

## 現在の問題分析

### 考えられる原因

1. **SSR設定の問題**
   - Next.js 15.5.3のSSRがAmplifyで正しく動作していない
   - App Routerの設定に問題がある可能性

2. **Amplify設定の不備**
   - SSR用の設定が不足している
   - `baseDirectory`の設定が正しくない可能性

3. **環境変数の未設定**
   - NextAuth.jsに必要な環境変数が設定されていない
   - `NEXTAUTH_SECRET`、`NEXTAUTH_URL`など

4. **ルーティング問題**
   - App Routerのルーティング設定に問題
   - ルートページ（`/`）が正しく生成されていない

5. **ビルド出力の問題**
   - `.next`ディレクトリの内容が正しくない
   - 静的ファイルが適切に生成されていない

## 確認が必要な項目

### Amplifyコンソールで確認すべき点
1. **ビルドログ**: エラーが出ていないか
2. **環境変数**: 設定されているか
3. **デプロイログ**: デプロイプロセスの詳細
4. **ドメイン設定**: 正しいURLが設定されているか
5. **ビルド成果物**: `.next`ディレクトリの内容

### ローカルで確認すべき点
1. **ローカルビルド**: `npm run build`が正常に動作するか
2. **ローカル起動**: `npm run dev`で正常に動作するか
3. **ビルド出力**: `.next`ディレクトリの内容

## 推奨される次のステップ

1. **Amplifyコンソールでビルドログを詳細確認**
2. **環境変数の設定確認・追加**
3. **ローカルでのビルド・起動テスト**
4. **必要に応じてAmplify設定の調整**

## 参考情報

- **Amplify URL**: `https://main.d15ngbpzg9c7px.amplifyapp.com`
- **GitHubリポジトリ**: `taksuehiro/vendor0913`
- **Next.jsバージョン**: 15.5.3
- **Node.jsバージョン**: 未確認（Amplifyのデフォルト）

## 作成日時

2025年9月13日 16:00 JST

## 作成者

AI Assistant (Claude Sonnet 4)

