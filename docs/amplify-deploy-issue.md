# AWS Amplify デプロイ問題報告書

## 問題の概要

AWS Amplify HostingでNext.js 15.5.3アプリケーションのデプロイが失敗している。静的エクスポート（`output: 'export'`）設定時に、NextAuth.jsのAPIルートでビルドエラーが発生している。

## プロジェクト構成

### 技術スタック
- **フロントエンド**: Next.js 15.5.3 (App Router)
- **認証**: NextAuth.js (Credentials Provider)
- **UI**: Tailwind CSS v4 + shadcn/ui
- **デプロイ先**: AWS Amplify Hosting

### ディレクトリ構造
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
│   ├── next.config.ts
│   └── package.json
├── backend/
│   └── main.py (FastAPI)
└── amplify.yml
```

## 発生した問題

### 1. 初回デプロイ失敗（ESLintエラー）
**エラー内容:**
```
./app/layout.tsx
42:21  Error: Do not use an `<a>` element to navigate to `/`. Use `<Link />` from `next/link` instead.
```

**解決方法:**
- `<a>`タグを`<Link>`コンポーネントに変更
- 修正完了、デプロイ成功

### 2. 404エラー（静的ファイル配置問題）
**症状:**
- デプロイは成功するが、アクセス時に404エラー
- ルートページ（`/`）が見つからない

**原因分析:**
- `amplify.yml`の`baseDirectory`が`frontend/.next`に設定
- Next.jsの静的エクスポート設定が不足

**解決方法:**
- `next.config.ts`に`output: 'export'`を追加
- `amplify.yml`の`baseDirectory`を`frontend/out`に変更

### 3. 現在の問題（NextAuth.js APIルートエラー）
**エラー内容:**
```
Error: export const dynamic = "force-static"/export const revalidate not configured on route "/api/auth/[...nextauth]" with "output: export". See more info here: https://nextjs.org/docs/advanced-features/static-html-export
```

**詳細ログ:**
```
2025-09-13T06:22:51.914Z [WARNING]: Error: export const dynamic = "force-static"/export const revalidate not configured on route "/api/auth/[...nextauth]" with "output: export".
2025-09-13T06:22:51.920Z [WARNING]: > Build error occurred
2025-09-13T06:22:51.925Z [WARNING]: [Error: Failed to collect page data for /api/auth/[...nextauth]] {
                                    type: 'Error'
                                    }
2025-09-13T06:22:51.946Z [ERROR]: !!! Build failed
2025-09-13T06:22:51.946Z [ERROR]: !!! Error: Command failed with exit code 1
```

## 現在の設定ファイル

### next.config.ts
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
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
    baseDirectory: frontend/out
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
      - frontend/.next/cache/**/*
```

### NextAuth.js APIルート (app/api/auth/[...nextauth]/route.ts)
```typescript
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // ダミー認証
        if (credentials?.email === "test@example.com" && 
            credentials?.password === "password") {
          return {
            id: "1",
            email: "test@example.com",
            name: "テストユーザー"
          };
        }
        return null;
      }
    })
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async redirect({ url, baseUrl }) {
      if (url.includes('/api/auth/error')) {
        return `${baseUrl}/login`;
      }
      return `${baseUrl}/dashboard`;
    }
  },
  session: {
    strategy: "jwt",
  },
});

export { handler as GET, handler as POST };
```

## 問題の根本原因

**NextAuth.jsのAPIルートが静的エクスポート（`output: 'export'`）と互換性がない**

NextAuth.jsはサーバーサイドのAPIルート（`/api/auth/[...nextauth]`）を使用するが、静的エクスポートでは：
1. サーバーサイドのAPIルートが利用できない
2. 動的ルート（`[...nextauth]`）が静的生成できない
3. `dynamic`や`revalidate`の設定が必要

## 解決策の選択肢

### 選択肢1: 静的エクスポートを諦めてSSRを使用
- `next.config.ts`から`output: 'export'`を削除
- Amplifyの設定を元の`frontend/.next`に戻す
- NextAuth.jsをそのまま使用可能

### 選択肢2: NextAuth.jsをクライアントサイド認証に変更
- NextAuth.jsを削除
- フロントエンドでJWT認証を実装
- バックエンドAPI（FastAPI）と直接連携

### 選択肢3: ハイブリッド構成
- 静的ページは静的エクスポート
- 認証が必要なページはSSR
- 複雑な設定が必要

## 推奨解決策

**選択肢1（SSR使用）を推奨**

理由：
1. NextAuth.jsをそのまま使用可能
2. 設定変更が最小限
3. 認証機能が完全に動作
4. Amplify HostingでSSRはサポートされている

## 実装手順

1. `next.config.ts`から`output: 'export'`を削除
2. `amplify.yml`の`baseDirectory`を`frontend/.next`に戻す
3. 必要に応じて環境変数をAmplifyコンソールで設定
4. デプロイを再実行

## 環境変数設定

Amplifyコンソールで以下の環境変数を設定：
- `NEXTAUTH_SECRET`: 認証用シークレット
- `NEXTAUTH_URL`: AmplifyのドメインURL
- `NEXT_PUBLIC_API_BASE`: バックエンドAPIのURL（後で設定）

## 参考資料

- [Next.js Static HTML Export](https://nextjs.org/docs/advanced-features/static-html-export)
- [NextAuth.js Configuration](https://next-auth.js.org/configuration)
- [AWS Amplify Hosting](https://docs.aws.amazon.com/amplify/latest/userguide/getting-started.html)

## 作成日時

2025年9月13日 15:30 JST

## 作成者

AI Assistant (Claude Sonnet 4)
