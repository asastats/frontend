#!/usr/bin/env bash
#
# Fetch the missing `regular` weight for the families that only have a bold.
#
#   ./fetch-regular.sh              all of them
#   ./fetch-regular.sh inter        just the ones whose slug matches
#
# Why this was needed: google-webfonts-helper names the 400 weight `regular`,
# not `400`. The earlier script asked for `variants=400,700`, and the API
# quietly delivered the 700 alone rather than reporting the unknown name --
# which is how 64 families ended up bold-only with nothing to show for it.
#
# Only `regular` is requested here: every family below already has its bold.
#
set -euo pipefail

cd "$(dirname "$0")"

BASE="https://gwfh.mranftl.com/api/fonts"
FILTER="${1:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

FAMILIES=(
  "alegreya"
  "alegreya-sans"
  "archivo"
  "baloo-2"
  "barlow"
  "be-vietnam-pro"
  "bitter"
  "bricolage-grotesque"
  "cabin"
  "chakra-petch"
  "comfortaa"
  "cormorant-garamond"
  "dm-sans"
  "epilogue"
  "familjen-grotesk"
  "fira-code"
  "fira-sans"
  "fraunces"
  "ibm-plex-mono"
  "ibm-plex-sans"
  "ibm-plex-serif"
  "inter"
  "inter-tight"
  "jetbrains-mono"
  "jost"
  "karla"
  "lato"
  "lexend"
  "literata"
  "lora"
  "m-plus-1-code"
  "m-plus-2"
  "manrope"
  "merriweather"
  "newsreader"
  "nunito"
  "nunito-sans"
  "open-sans"
  "outfit"
  "playfair-display"
  "plus-jakarta-sans"
  "poppins"
  "quicksand"
  "rajdhani"
  "raleway"
  "red-hat-display"
  "red-hat-mono"
  "red-hat-text"
  "rokkitt"
  "rubik"
  "sora"
  "source-code-pro"
  "source-sans-3"
  "source-serif-4"
  "space-grotesk"
  "space-mono"
  "spectral"
  "syne"
  "unbounded"
  "vollkorn"
  "work-sans"
  "zen-kaku-gothic-new"
  "zen-old-mincho"
  "zilla-slab"
)

ok=0
failed=()
for slug in "${FAMILIES[@]}"; do
  if [ -n "$FILTER" ] && [[ "$slug" != *"$FILTER"* ]]; then
    continue
  fi

  printf '  %-24s ' "$slug"

  # Skip if a regular is already on disk, so re-running is cheap and safe.
  if ls "$slug"-v*-*-regular.woff2 >/dev/null 2>&1; then
    echo "already have it"
    ok=$((ok + 1))
    continue
  fi

  url="$BASE/$slug?download=zip&subsets=latin&formats=woff2&variants=regular"
  if curl -fsSL --max-time 60 -o "$TMP/$slug.zip" "$url" 2>/dev/null \
     && unzip -joq "$TMP/$slug.zip" -d . 2>/dev/null; then
    # The API returns a zip even when it matched nothing, so confirm a file
    # actually arrived rather than trusting the exit status.
    if ls "$slug"-v*-*-regular.woff2 >/dev/null 2>&1; then
      echo "ok"
      ok=$((ok + 1))
    else
      echo "zip had no regular"
      failed+=("$slug")
    fi
  else
    echo "FAILED"
    failed+=("$slug")
  fi
done

echo
echo "$ok of ${#FAMILIES[@]} families now have a regular"

if [ ${#failed[@]} -gt 0 ]; then
  echo
  echo "still missing -- fetch these by hand at"
  echo "  https://gwfh.mranftl.com/fonts/<slug>?subsets=latin"
  for f in "${failed[@]}"; do echo "  $f"; done
fi

echo
echo "woff2 files: $(ls -1 *.woff2 2>/dev/null | wc -l)"
du -sh . | awk '{print "  total: " $1}'
