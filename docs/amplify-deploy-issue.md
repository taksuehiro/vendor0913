# AWS Amplify デプロイ問題報告書

## 問題の概要

AWS Amplify HostingでNext.js 15.5.3アプリケーションのデプロイが失敗している。複数の設定パターンを試行したが、いずれも404エラーまたはビルドエラーが発生している。最小構成テストプロジェクトでも同様の問題が発生している。

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

### 3. NextAuth.js APIルートエラー
**エラー内容:**
```
Error: export const dynamic = "force-static"/export const revalidate not configured on route "/api/auth/[...nextauth]" with "output: export". See more info here: https://nextjs.org/docs/advanced-features/static-html-export
```

**解決方法:**
- SSRに戻す（静的エクスポートを無効化）
- `output: 'standalone'`設定を試行

### 4. 現在の問題（最小構成テストでも失敗）
**エラー内容:**
```
npm error The `npm ci` command can only install with an existing package-lock.json or
npm error npm-shrinkwrap.json with lockfileVersion >= 1. Run an install with npm@5 or
npm error later to generate a package-lock.json file, then try again.
```

**詳細ログ:**
```
2025-09-13T07:23:17.032Z [WARNING]: npm error code EUSAGE
2025-09-13T07:23:17.037Z [WARNING]: npm error
2025-09-13T07:23:17.144Z [ERROR]: !!! Build failed
2025-09-13T07:23:17.144Z [ERROR]: !!! Error: Command failed with exit code 1
```

**原因分析:**
- 最小構成テストプロジェクトで`package-lock.json`が存在しない
- Amplifyが`npm ci`を実行しようとして失敗
- `amplify.yml`で`npm install`に変更したが、まだ`npm ci`が実行されている

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

**複数の根本原因が重複している**

1. **package-lock.json問題**: 最小構成テストでも`npm ci`が失敗
2. **Amplify設定の不整合**: `amplify.yml`の変更が反映されていない
3. **NextAuth.jsの互換性問題**: 静的エクスポートとSSRの設定問題
4. **Next.js 15.5.3の新機能**: Amplifyとの互換性問題

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

**段階的アプローチで問題を解決**

### 第1段階: 最小構成テストの修正
1. **package-lock.json生成**: ローカルで`npm install`を実行
2. **amplify.yml確認**: `npm install`が正しく設定されているか確認
3. **Amplify設定更新**: コンソールで設定を再確認

### 第2段階: 元プロジェクトの修正
1. **NextAuth.js削除**: 一時的に認証機能を無効化
2. **静的エクスポート**: `output: 'export'`で基本動作確認
3. **段階的機能追加**: 認証機能を後で追加

### 第3段階: 認証機能の実装
1. **クライアントサイド認証**: NextAuth.jsの代替実装
2. **JWT認証**: バックエンドAPIとの直接連携

## 緊急対応手順

1. **最小構成テストの修正**
   - ローカルで`npm install`を実行して`package-lock.json`を生成
   - `amplify.yml`で`npm install`が確実に設定されているか確認
   - Amplifyコンソールで設定を再確認

2. **元プロジェクトの簡素化**
   - NextAuth.jsを一時的に削除
   - 基本的なNext.jsアプリとして動作確認
   - 認証機能は後で段階的に追加

## 環境変数設定

Amplifyコンソールで以下の環境変数を設定：
- `NEXTAUTH_SECRET`: 認証用シークレット
- `NEXTAUTH_URL`: AmplifyのドメインURL
- `NEXT_PUBLIC_API_BASE`: バックエンドAPIのURL（後で設定）

## 参考資料

- [Next.js Static HTML Export](https://nextjs.org/docs/advanced-features/static-html-export)
- [NextAuth.js Configuration](https://next-auth.js.org/configuration)
- [AWS Amplify Hosting](https://docs.aws.amazon.com/amplify/latest/userguide/getting-started.html)

## 現在の状況（2025年9月13日 16:30 JST更新）

### 最小構成テストプロジェクトの状況
- **プロジェクト**: `taksuehiro/amp0913` (最小構成)
- **問題**: `npm ci`が`package-lock.json`なしで失敗
- **修正試行**: `amplify.yml`で`npm install`に変更
- **結果**: まだ`npm ci`が実行されて失敗

### 次のアクション
1. **ローカルで`npm install`を実行**して`package-lock.json`を生成
2. **Amplifyコンソールで設定を再確認**
3. **元プロジェクトの簡素化**を検討

## 作成日時

2025年9月13日 15:30 JST（16:30 JST更新）

## 作成者

AI Assistant (Claude Sonnet 4)
