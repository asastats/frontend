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
      // A loader: a chunk importing the entry by its unhashed name reruns only this (logbook).
      input: { app: "src/app/entry.ts" },
      output: {
        entryFileNames: "js/app.js",
        chunkFileNames: "dist/app-[name]-[hash].js",
        // Out of the entry, so no chunk imports js/app.js (a mutable, cached URL; logbook).
        manualChunks: (id: string) => (id.includes("preload-helper") ? "preload-helper" : undefined),
      },
    },
  },
});
