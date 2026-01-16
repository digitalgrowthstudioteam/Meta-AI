/** @type {import('next').NextConfig} */
const nextConfig = {
reactStrictMode: false,

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

api: {
externalResolver: true,
},

experimental: {
serverActions: false,
},
};

module.exports = nextConfig;
