import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Multi-entry build — each React widget is its own entry point that outputs
 * a self-contained ES module bundle.  Django templates load the appropriate
 * bundle via <script type="module" src="{% static 'js/widgets/schedule.js' %}">
 * and each bundle mounts itself into its designated #*-widget-root div.
 */
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "../backend/static/js/widgets"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        schedule:   path.resolve(__dirname, "src/widgets/Schedule/main.jsx"),
        payment:    path.resolve(__dirname, "src/widgets/Payment/main.jsx"),
        notes:      path.resolve(__dirname, "src/widgets/TherapistNotes/main.jsx"),
        admin:      path.resolve(__dirname, "src/widgets/AdminDashboard/main.jsx"),
      },
      output: {
        // Keep filenames stable so Django {% static %} tags never need changing.
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
  server: {
    // In dev mode proxy API calls to Django running on 8000
    proxy: {
      "/api":      "http://localhost:8000",
      "/ws":       { target: "ws://localhost:8000", ws: true },
      "/payments": "http://localhost:8000",
    },
  },
});
