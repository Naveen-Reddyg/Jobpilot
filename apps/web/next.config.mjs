/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiBaseUrl = (process.env.API_INTERNAL_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');
    return [{ source: '/api/:path*', destination: `${apiBaseUrl}/api/:path*` }];
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
};

export default nextConfig;
