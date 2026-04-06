#!/usr/bin/env bash
set -euo pipefail

echo "==> Starting web build using run_web.sh..."

cd "$(dirname "$0")"

echo "==> Cleaning old build..."
rm -rf build docs build/web-cache

mkdir -p build/web build/web-cache

echo "==> Running pygbag..."
python3 -m pygbag \
  --cdn https://pygame-web.github.io/archives/0.9/ \
  --version 0.9 \
  --build \
  --disable-sound-format-error \
  .

if [[ ! -f "build/web/index.html" ]]; then
  echo "ERROR: build/web/index.html not found!"
  exit 1
fi

echo "==> Patching autorun..."
if grep -q 'autorun : 0' build/web/index.html; then
  sed -i '' 's/autorun : 0/autorun : 1/' build/web/index.html
fi

echo "==> Current autorun line:"
grep -n "autorun" build/web/index.html || true

echo "==> Copying to docs..."
mkdir -p docs
cp -R build/web/* docs/
touch docs/.nojekyll

echo "==> Build complete. Ready for GitHub Pages."

read -r -p "Serve docs locally on http://localhost:8000? [y/N] " serve_choice
if [[ "$serve_choice" == "y" || "$serve_choice" == "Y" ]]; then
  cd docs
  python3 -m http.server 8000
fi