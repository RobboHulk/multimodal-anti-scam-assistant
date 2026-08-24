import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  base: "/",
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:8889",
        changeOrigin: true,
      },
      "/uploads": {
        target: "http://localhost:8889",
        changeOrigin: true,
      },
      "/ml": {
        target: "http://localhost:18000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ml/, "/api"),
      },
    },
  },
}));
