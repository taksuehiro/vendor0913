import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // SSRモード（output: 'export'は削除済み）
  trailingSlash: false, // Amplifyでは通常falseが推奨
  images: {
    unoptimized: true
  },
  // Amplify対応の設定を追加
  experimental: {
    serverComponentsExternalPackages: [],
  },
  // 環境変数の設定
  env: {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
  }
};

export default nextConfig;
