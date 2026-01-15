/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,

  // ✅ REQUIRED for App Router + Node server
  output: "standalone",

  experimental: {
    appDir: true,
  },

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.fbcdn.net" },
      { protocol: "https", hostname: "**.facebook.com" },
      { protocol: "https", hostname: "platform-lookaside.fbsbx.com" },
    ],
  },

  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
};

module.exports = nextConfig;
