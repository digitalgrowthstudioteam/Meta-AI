/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  swcMinify: false,
  webpack: (config) => {
    return config;
  },
};

module.exports = nextConfig;
