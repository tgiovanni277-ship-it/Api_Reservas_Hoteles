import { defineConfig } from "vite";

const apiTarget = process.env.VITE_DEV_API_PROXY_TARGET || "http://127.0.0.1:5000";

export default defineConfig({
  server: {
    proxy: {
      "/reservas": { target: apiTarget, changeOrigin: true },
      "/habitaciones": { target: apiTarget, changeOrigin: true },
      "/login": { target: apiTarget, changeOrigin: true },
      "/register": { target: apiTarget, changeOrigin: true }
    }
  }
});
