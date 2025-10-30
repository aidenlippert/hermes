/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable production source maps for better stack traces on Vercel
  productionBrowserSourceMaps: true,
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
