import type { NextConfig } from 'next';

export default {
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true
  },

  images: {
    unoptimized: true
    // remotePatterns: []
  },

  experimental: {
    optimizePackageImports: ['@phosphor-icons/react']
  },

  allowedDevOrigins: []
} as NextConfig;
