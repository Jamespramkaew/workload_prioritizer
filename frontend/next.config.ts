import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Output standalone สำหรับ Docker
  output: 'standalone',
  
  // API rewrites (optional - สำหรับ proxy API calls)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
