import { defineConfig } from "vite";
import { nodePolyfills } from "vite-plugin-node-polyfills";

// Builds a single wallet-connect bundle into the Django static tree as
// js/bundle.js, loaded by the authorize page. Unlike the Rewards Suite,
// emptyOutDir is false: asastats ships hand-authored files in static/ that must
// not be wiped by the build.
export default defineConfig({
  base: "/static/",
  plugins: [
    nodePolyfills({
      include: ["buffer", "crypto", "stream"],
      exclude: ["vm", "fs", "path"],
      globals: { Buffer: true, global: true, process: true },
    }),
  ],
  build: {
    outDir: "../asastats/static",
    emptyOutDir: false,
    manifest: false,
    minify: "esbuild",
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        entryFileNames: "js/bundle.js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name].[ext]",
        manualChunks: undefined,
      },
    },
  },
});
