#!/usr/bin/env bash
#
# Build static/css/style.tw.css from static/css/input.css.
#
#   ./build-tailwind.sh          one-shot, minified
#   ./build-tailwind.sh --watch  rebuild on change (Ctrl-C to stop)
#
# Requires the toolchain: run ./fetch-tailwind.sh first.
#
set -euo pipefail

cd "$(dirname "$0")"
CSS_DIR="static/css"

if [ ! -x "$CSS_DIR/tailwindcss" ]; then
  echo "Missing $CSS_DIR/tailwindcss -- run ./fetch-tailwind.sh first." >&2
  exit 1
fi
for plugin in daisyui.mjs daisyui-theme.mjs; do
  if [ ! -f "$CSS_DIR/$plugin" ]; then
    echo "Missing $CSS_DIR/$plugin -- run ./fetch-tailwind.sh first." >&2
    exit 1
  fi
done

if [ "${1:-}" = "--watch" ]; then
  exec "$CSS_DIR/tailwindcss" -i "$CSS_DIR/input.css" -o "$CSS_DIR/style.tw.css" --watch
fi

"$CSS_DIR/tailwindcss" -i "$CSS_DIR/input.css" -o "$CSS_DIR/style.tw.css" --minify
echo
ls -la "$CSS_DIR/style.tw.css"
