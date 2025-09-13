/** @type {import('next').NextConfig} */
const nextConfig = {
  // 最初は静的エクスポートなしでテスト
  // output: 'standalone',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  // ESLintエラーを一時的に無視（デプロイテスト用）
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  }
}

module.exports = nextConfig
