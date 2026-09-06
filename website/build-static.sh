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

# Say which tool is missing. Without this the deploy reports `rc: 127` and not
# one word of output -- npx's own "command not found" goes to stderr, which the
# esbuild call below discards along with esbuild's summary. 127 is kept as the
# exit code because that is what the shell would have returned anyway.
if ! command -v npx >/dev/null 2>&1; then
  echo "build-static.sh: npx not found; install nodejs and npm" >&2
  exit 127
fi

# Vendored bundles are already minified and are not ours to rebuild; anything
# matching *.min*.js is copied through untouched by collectstatic from the
# source directory, so it is simply skipped here.
mkdir -p "$OUT"
count=0
for path in "$SRC"/*.js; do
  name="$(basename "$path")"
  case "$name" in
    *.min*.js|bundle.js) continue ;;
  esac
  # stdout only. esbuild writes its per-file summary to stderr, which is noise
  # on a good run and the whole diagnosis on a bad one -- and Ansible shows a
  # task's stderr when it fails, not when it succeeds.
  npx --yes esbuild@0.25.5 "$path" --minify --target=es2017 \
    --outfile="$OUT/$name" >/dev/null
  count=$((count + 1))
done

echo "minified $count scripts into $OUT"
du -sh "$OUT"
