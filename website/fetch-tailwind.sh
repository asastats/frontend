#!/usr/bin/env bash
#
# Fetch the Tailwind + DaisyUI toolchain for frontend/website.
#
# All three files are gitignored and fetched per machine; only the built
# stylesheet (static/css/style.tw.css) is committed, mirroring how
# static/css/style.min0NN.css already works.
#
# Run from anywhere:   ./fetch-tailwind.sh
#
set -euo pipefail

cd "$(dirname "$0")"
CSS_DIR="static/css"

# The standalone binary is per-platform. aarch64 (Raspberry Pi 5) -> linux-arm64.
case "$(uname -s)-$(uname -m)" in
  Linux-aarch64|Linux-arm64)  TW_ASSET="tailwindcss-linux-arm64" ;;
  Linux-x86_64)               TW_ASSET="tailwindcss-linux-x64" ;;
  Darwin-arm64)               TW_ASSET="tailwindcss-macos-arm64" ;;
  Darwin-x86_64)              TW_ASSET="tailwindcss-macos-x64" ;;
  *)
    echo "Unrecognised platform: $(uname -s)-$(uname -m)" >&2
    echo "Pick an asset from https://github.com/tailwindlabs/tailwindcss/releases/latest" >&2
    exit 1
    ;;
esac

echo ">> Tailwind CSS standalone ($TW_ASSET)"
curl -fsSLo "$CSS_DIR/tailwindcss" \
  "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/$TW_ASSET"
chmod +x "$CSS_DIR/tailwindcss"

echo ">> daisyui.mjs"
curl -fsSLo "$CSS_DIR/daisyui.mjs" \
  "https://github.com/saadeghi/daisyui/releases/latest/download/daisyui.mjs"

echo ">> daisyui-theme.mjs"
curl -fsSLo "$CSS_DIR/daisyui-theme.mjs" \
  "https://github.com/saadeghi/daisyui/releases/latest/download/daisyui-theme.mjs"

echo
echo "Fetched:"
ls -la "$CSS_DIR/tailwindcss" "$CSS_DIR/daisyui.mjs" "$CSS_DIR/daisyui-theme.mjs"
"$CSS_DIR/tailwindcss" --help >/dev/null 2>&1 \
  && echo "Binary runs OK." \
  || echo "WARNING: the binary did not run -- wrong architecture?"

echo
echo "Now build the stylesheet with:"
echo "  ./build-tailwind.sh"
