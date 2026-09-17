import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  // Emits a self-contained server under .next/standalone for the Docker image.
  output: "standalone",
};

export default config;
