#!/usr/bin/env bash
#
# Minify this project's own JavaScript into static/build/.
#
#   ./build-static.sh
#
# Templates name sources -- `{% static 'js/site.js' %}` -- and never build
# outputs. In production static/build is placed FIRST in STATICFILES_DIRS, so
# collectstatic finds the minified copy under the same name; in development the
# directory is absent and the readable source is served instead. Nothing in a
# template changes between the two.
#
# This replaces the old `site.min021.js` -> `site.min022.js` convention. That
# scheme made the filename carry the cache-busting, which meant every change
# needed a rename plus an edit in each referring template, and a missed one
# silently served a stale script. Content hashing does that job now
# (ManifestStaticFilesStorage), leaving this script responsible only for size.
#
set -euo pipefail

cd "$(dirname "$0")"

SRC="static/js"
OUT="static/build/js"

# Vendored bundles are already minified and are not ours to rebuild; anything
# matching *.min*.js is copied through untouched by collectstatic from the
# source directory, so it is simply skipped here.
mkdir -p "$OUT"
count=0
for path in "$SRC"/*.js; do
  name="$(basename "$path")"
  case "$name" in
    *.min*.js|bundle.js|websocketbridge.js) continue ;;
  esac
  npx --yes esbuild@0.25.5 "$path" --minify --target=es2017 \
    --outfile="$OUT/$name" >/dev/null 2>&1
  count=$((count + 1))
done

echo "minified $count scripts into $OUT"
du -sh "$OUT"
