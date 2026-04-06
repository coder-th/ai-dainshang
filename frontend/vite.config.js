import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  // 构建输出到 backend 可读取的位置
  build: {
    outDir: "../frontend/dist",
    emptyOutDir: true,
  },
  // 开发时代理 API 请求到 Django
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:9527",
        changeOrigin: true,
      },
    },
  },
});
