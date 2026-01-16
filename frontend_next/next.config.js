/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,

  // 🔒 REQUIRED — fixes missing chunks / 404 JS
  output: "standalone",

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.fbcdn.net" },
      { protocol: "https", hostname: "**.facebook.com" },
      { protocol: "https", hostname: "platform-lookaside.fbsbx.com" },
    ],
  },

  typescript: {
    ignoreBuildErrors: true,
  },

  eslint: {
    ignoreDuringBuilds: true,
  },

  // ⛔ prevents Next internal API handling in production
  api: {
    externalResolver: true,
  },

  experimental: {
    serverActions: false,
  },
};

module.exports = nextConfig;
