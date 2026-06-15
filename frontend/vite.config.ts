import { defineConfig } from "vite";
import { nodePolyfills } from "vite-plugin-node-polyfills";

// Builds a single wallet-connect bundle into the Django static tree as
// js/bundle.js, loaded by the authorize page. emptyOutDir is false:
// asastats ships hand-authored files in static/ that must not be wiped by the build.
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
    // bundle.js (~1.2 MB) is the Algorand wallet stack (algosdk + use-wallet +
    // Pera/Defly/Lute, which themselves bundle WalletConnect). The EVM provider
    // and viem are dynamically imported, so they land in lazy dist/ chunks that
    // load only when a user actually picks an EVM / WalletConnect wallet.
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      // Vite 8's Rolldown engine is far stricter than Rollup about a handful of
      // third-party patterns. Every warning silenced below originates in
      // node_modules pulled in by WalletConnect/Reown (ox, lottie-web, asn1.js);
      // none touch our code or affect runtime. Warnings from our own sources
      // still pass through to the default handler.
      onwarn(warning, defaultHandler) {
        const code = warning.code ?? "";
        const message = warning.message ?? "";
        if (
          // Misplaced /*#__PURE__*/ annotations in `ox` (viem/WalletConnect dep).
          code === "INVALID_ANNOTATION" ||
          // Direct eval() in lottie-web (bundled by the WalletConnect QR modal).
          code === "EVAL" ||
          code === "CIRCULAR_DEPENDENCY" ||
          // asn1.js (via elliptic) references Node's "vm"; never run in browser.
          message.includes("externalized for browser compatibility")
        ) {
          return;
        }
        defaultHandler(warning);
      },
      output: {
        entryFileNames: "js/bundle.js",
        chunkFileNames: "dist/[name]-[hash].js",
        assetFileNames: "dist/[name].[ext]",
        manualChunks: undefined,
      },
    },
  },
});
