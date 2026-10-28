# The pinned Tailwind + daisyUI toolchain, sourced by fetch-tailwind.sh and
# build-tailwind.sh and read by core/tests/test_stylesheet_build.py.
# Change a version only together with every checksum and a rebuilt, committed
# style.tw.css. See docs/logbook.md.

TAILWIND_VERSION=4.3.3
DAISYUI_VERSION=5.7.50

# The standalone binary's release asset for this machine.
tw_asset() {
  case "$(uname -s)-$(uname -m)" in
    Linux-aarch64|Linux-arm64)  echo "tailwindcss-linux-arm64" ;;
    Linux-x86_64)               echo "tailwindcss-linux-x64" ;;
    Darwin-arm64)               echo "tailwindcss-macos-arm64" ;;
    Darwin-x86_64)              echo "tailwindcss-macos-x64" ;;
    *) return 1 ;;
  esac
}

# SHA-256 of each release asset (tailwind: the release's sha256sums.txt).
pinned_sha() {
  case "$1" in
    tailwindcss-linux-arm64)  echo "55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195" ;;
    tailwindcss-linux-x64)    echo "dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a" ;;
    tailwindcss-macos-arm64)  echo "cdf646702987a743464dff4d9c60fd4480d1c1e73dd819a9a67f1078815dce9d" ;;
    tailwindcss-macos-x64)    echo "7922e0953f2110c05976e3bf58f14e643d90427575e766b7d433f5f80cbee7e1" ;;
    daisyui.mjs)              echo "d69de07c7463bb1f41548e2688f88ee105cdadf9779fce5b3c47b3bfaa6be472" ;;
    daisyui-theme.mjs)        echo "e48a35d8326d650181ca600560e8520cf6b44cf9242bbd9d45825607e641f251" ;;
    *) return 1 ;;
  esac
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

# Print every local toolchain file that is missing or not the pinned one;
# fail if there is any.
check_toolchain() {
  local css_dir="$1" asset bad=0
  asset="$(tw_asset)" || { echo "unrecognised platform $(uname -s)-$(uname -m)"; return 1; }
  for pair in "tailwindcss:$asset" "daisyui.mjs:daisyui.mjs" "daisyui-theme.mjs:daisyui-theme.mjs"; do
    local file="$css_dir/${pair%%:*}" name="${pair#*:}"
    if [ ! -f "$file" ]; then
      echo "missing $file"; bad=1
    elif [ "$(sha256_of "$file")" != "$(pinned_sha "$name")" ]; then
      echo "$file is not the pinned $name"; bad=1
    fi
  done
  return $bad
}

# Drop daisyUI's `:root:has(input.theme-controller[...]:checked),` from each theme
# selector: theme.js sets data-theme, and the :has() makes every style pass re-scan
# the page. Run on every build, test included. See docs/logbook.md.
strip_theme_controller() {
  sed 's/:root:has(input\.theme-controller\[value=[^]]*\]:checked),//g' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
}

# Drop daisyUI's five `:root:has(.modal...){--page-scroll-lock: }` rules: no page
# uses its `.modal` class (our dialogs are native), and they cost every style pass.
# Run on every build, test included. See docs/logbook.md.
strip_modal_scroll_lock() {
  sed 's/:root:has(\.modal[^{]*){--page-scroll-lock: }//g' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
}
