/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://meta-ai.digitalgrowthstudio.in/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
