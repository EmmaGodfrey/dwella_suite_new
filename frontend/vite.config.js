import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";

const rootEnvPath = path.resolve(__dirname, "../.env");

if (fs.existsSync(rootEnvPath)) {
  fs.readFileSync(rootEnvPath, "utf8")
    .split(/\r?\n/)
    .forEach((rawLine) => {
      const line = rawLine.trim();

      if (!line || line.startsWith("#") || !line.includes("=")) {
        return;
      }

      const [key, ...valueParts] = line.split("=");
      process.env[key] ??= valueParts.join("=").replace(/^["']|["']$/g, "");
    });
}

export default defineConfig({
  plugins: [react()],
  define: {
    global: "window",
    "import.meta.env.VITE_APP_NAME": JSON.stringify(process.env.VITE_APP_NAME || "Dwella Suite"),
    "import.meta.env.VITE_API_BASE_URL": JSON.stringify(
      process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
    ),
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
