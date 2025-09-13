/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  trailingSlash: false,
  images: {
    unoptimized: true
  },
  experimental: {
    outputFileTracingRoot: undefined,
  }
}

module.exports = nextConfig
