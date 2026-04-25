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
 
echo "==> Patching index.html..."
 
# 1) Fix autorun
if grep -q 'autorun : 0' build/web/index.html; then
  sed -i '' 's/autorun : 0/autorun : 1/' build/web/index.html
  echo "    [OK] autorun set to 1"
fi
 
# 2) Remove broken pythonrc.py prefetch (404 on pygbag 0.9 CDN)
if grep -q 'pythonrc\.py' build/web/index.html; then
  sed -i '' '/pythonrc\.py/d' build/web/index.html
  echo "    [OK] removed pythonrc.py prefetch (was causing 404)"
fi
 
# 3) Fix canvas CSS for Retina/HiDPI displays
if grep -q 'width: 100%;' build/web/index.html; then
  sed -i '' 's/width: 100%;/width: 920px;/' build/web/index.html
  echo "    [OK] canvas width fixed for HiDPI"
fi
if grep -q 'height: 100%;' build/web/index.html; then
  sed -i '' 's/height: 100%;/height: 920px;/' build/web/index.html
  echo "    [OK] canvas height fixed for HiDPI"
fi
 
# 4) Inject MutationObserver using Python (avoids Mac sed multiline issues)
python3 - <<'PYEOF'
with open("build/web/index.html", "r") as f:
    html = f.read()
 
if "fixCanvas" not in html:
    observer_script = """    <script>
        // Fix for Retina/HiDPI displays - pygbag overrides canvas size repeatedly
        function fixCanvas() {
            var canvas = document.getElementById("canvas");
            if (canvas) {
                canvas.style.width = "920px";
                canvas.style.height = "920px";
                canvas.style.imageRendering = "pixelated";
            }
        }
        fixCanvas();
        window.addEventListener("load", function() {
            var canvas = document.getElementById("canvas");
            if (canvas) {
                var observer = new MutationObserver(fixCanvas);
                observer.observe(canvas, { attributes: true, attributeFilter: ["style", "width", "height"] });
            }
            fixCanvas();
        });
    </script>"""
    html = html.replace("</body>", observer_script + "\n</body>")
    with open("build/web/index.html", "w") as f:
        f.write(html)
    print("    [OK] HiDPI MutationObserver script injected")
else:
    print("    [OK] MutationObserver already present, skipping")
PYEOF
 
echo "==> Verifying patches..."
grep -n "autorun" build/web/index.html || true
grep -n "pythonrc" build/web/index.html && echo "    [WARN] pythonrc line still present!" || echo "    [OK] pythonrc removed"
grep -n "fixCanvas" build/web/index.html > /dev/null && echo "    [OK] MutationObserver present" || echo "    [WARN] MutationObserver missing!"
 
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