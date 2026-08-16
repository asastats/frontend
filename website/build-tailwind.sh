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

# Attribution has to be re-applied after the build. The vendored theme files
# each carry a `/*! ... */` banner, but Lightning CSS -- which Tailwind uses to
# minify -- strips even preserve-comments, so the banner does not survive into
# style.tw.css. That matters: the themes are CC BY 4.0 and crediting the author
# is a licence condition, not a courtesy. Prepending it here means the served
# stylesheet always carries it, however it was built.
#
# This is one of three places the credit appears; see THEMES.md for the others.
BANNER='/*! Includes DaisyUI themes by Dachi (https://github.com/dachinat/daisyui-themes), licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). See THEMES.md. */'
printf '%s\n' "$BANNER" | cat - "$CSS_DIR/style.tw.css" > "$CSS_DIR/style.tw.css.tmp"
mv "$CSS_DIR/style.tw.css.tmp" "$CSS_DIR/style.tw.css"

echo
ls -la "$CSS_DIR/style.tw.css"
