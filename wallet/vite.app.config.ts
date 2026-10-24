import { defineConfig } from "vite";

// js/app.js for the ASA Stats app, built apart from bundle.js so the two never
// share a chunk (a shared one would rewrite bundle.js). See docs/logbook.md.
export default defineConfig({
  base: "/static/",
  build: {
    outDir: "../website/static",
    emptyOutDir: false,
    manifest: false,
    minify: "esbuild",
    rollupOptions: {
      input: { app: "src/app/main.ts" },
      output: {
        entryFileNames: "js/app.js",
        chunkFileNames: "dist/app-[name]-[hash].js",
      },
    },
  },
});
