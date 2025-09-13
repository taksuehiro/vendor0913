import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: 'export', // 静的エクスポートを無効化
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
