const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "sixdo.vn",
        pathname: "/modules/uniform/assets/image/**",
      },
    ],
  },
};

export default nextConfig;

