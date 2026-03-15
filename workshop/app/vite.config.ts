import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api/snowflake": {
        target: "https://rnrizgx-demo-temp.snowflakecomputing.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/snowflake/, ""),
      },
    },
  },
});
