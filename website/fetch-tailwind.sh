#!/usr/bin/env bash
#
# Fetch the pinned Tailwind + DaisyUI toolchain (tailwind-toolchain.sh) for
# frontend/website.
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

. ./tailwind-toolchain.sh

TW_ASSET="$(tw_asset)" || {
  echo "Unrecognised platform: $(uname -s)-$(uname -m)" >&2
  exit 1
}
TW_URL="https://github.com/tailwindlabs/tailwindcss/releases/download/v$TAILWIND_VERSION"
DAISY_URL="https://github.com/saadeghi/daisyui/releases/download/v$DAISYUI_VERSION"

# fetch <url> <file> <asset>: download, then refuse anything but the pinned bytes.
fetch() {
  curl -fsSLo "$2.part" "$1"
  if [ "$(sha256_of "$2.part")" != "$(pinned_sha "$3")" ]; then
    rm -f "$2.part"
    echo "Checksum mismatch for $3 from $1" >&2
    exit 1
  fi
  mv "$2.part" "$2"
}

echo ">> Tailwind CSS v$TAILWIND_VERSION ($TW_ASSET)"
fetch "$TW_URL/$TW_ASSET" "$CSS_DIR/tailwindcss" "$TW_ASSET"
chmod +x "$CSS_DIR/tailwindcss"

echo ">> daisyUI v$DAISYUI_VERSION"
fetch "$DAISY_URL/daisyui.mjs" "$CSS_DIR/daisyui.mjs" daisyui.mjs
fetch "$DAISY_URL/daisyui-theme.mjs" "$CSS_DIR/daisyui-theme.mjs" daisyui-theme.mjs

echo
echo "Fetched:"
ls -la "$CSS_DIR/tailwindcss" "$CSS_DIR/daisyui.mjs" "$CSS_DIR/daisyui-theme.mjs"
"$CSS_DIR/tailwindcss" --help >/dev/null 2>&1 \
  && echo "Binary runs OK." \
  || echo "WARNING: the binary did not run -- wrong architecture?"

echo
echo "Now build the stylesheet with:"
echo "  ./build-tailwind.sh"
