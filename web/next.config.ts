import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === 'production';

const nextConfig: NextConfig = {
  output: 'export',
  basePath: isProd ? '/kopi_sentiment' : '',
  assetPrefix: isProd ? '/kopi_sentiment/' : '',
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
