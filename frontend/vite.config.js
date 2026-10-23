import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "node:url";

const configDirectory = path.dirname(fileURLToPath(import.meta.url));

const rootEnvPath = path.resolve(configDirectory, "../.env");

const normaliseBasePath = (value) => {
  const pathValue = value || "/";
  return `/${pathValue.replace(/^\/+|\/+$/g, "")}/`.replace("//", "/");
};

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
  base: normaliseBasePath(process.env.VITE_BASE_PATH),
  plugins: [react()],
  define: {
    global: "window",
    "import.meta.env.VITE_APP_NAME": JSON.stringify(process.env.VITE_APP_NAME || "Dwella Suite"),
    "import.meta.env.VITE_BASE_PATH": JSON.stringify(
      normaliseBasePath(process.env.VITE_BASE_PATH)
    ),
    "import.meta.env.VITE_API_BASE_URL": JSON.stringify(
      process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
    ),
  },
  resolve: {
    alias: {
      "@": path.resolve(configDirectory, "./src"),
    },
  },
});
