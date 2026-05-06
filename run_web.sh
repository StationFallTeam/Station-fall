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

# 3) Fix canvas CSS — use 100vmin so it fills the screen responsively
if grep -q 'width: 100%;' build/web/index.html; then
  sed -i '' 's/width: 100%;/width: 100vmin;/' build/web/index.html
  echo "    [OK] canvas width set to 100vmin (responsive)"
fi
if grep -q 'height: 100%;' build/web/index.html; then
  sed -i '' 's/height: 100%;/height: 100vmin;/' build/web/index.html
  echo "    [OK] canvas height set to 100vmin (responsive)"
fi

# 4) All remaining patches via Python (avoids Mac sed multiline issues)
python3 - <<'PYEOF'
with open("build/web/index.html", "r") as f:
    html = f.read()

# 4a) Fix html element background to eliminate gray on wide screens
if "html {" not in html and "html{" not in html:
    html = html.replace(
        "<style>",
        "<style>\n        html { margin: 0; padding: 0; background-color: #05050F; width: 100%; height: 100%; }"
    )
    print("    [OK] html element background fixed")
else:
    print("    [OK] html background already patched, skipping")

# 4b) Fix body background and centering
old_body = """        body {
            font-family: arial;
            margin: 0;
            padding: none;
            background-color:powderblue;
        }"""
new_body = """        body {
            font-family: arial;
            margin: 0;
            padding: 0;
            background-color: #05050F;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }"""
if "background-color:powderblue" in html:
    html = html.replace(old_body, new_body)
    print("    [OK] body background fixed (dark space color, centered)")
elif "background-color: #05050F" in html:
    print("    [OK] body background already patched, skipping")
else:
    print("    [WARN] body background pattern not found - may need manual check")

# 4c) Inject responsive canvas scaling with !important to override pygbag
if "fixCanvas" not in html:
    observer_script = """    <script>
        // Responsive canvas - scales to fill browser window while keeping square aspect ratio
        // Uses !important via setProperty to override pygbag's window_canvas_adjust
        function fixCanvas() {
            var canvas = document.getElementById("canvas");
            if (canvas) {
                var size = Math.min(window.innerWidth, window.innerHeight);
                canvas.style.setProperty("width", size + "px", "important");
                canvas.style.setProperty("height", size + "px", "important");
                canvas.style.setProperty("image-rendering", "pixelated", "important");
                canvas.style.setProperty("position", "fixed", "important");
                canvas.style.setProperty("top", "50%", "important");
                canvas.style.setProperty("left", "50%", "important");
                canvas.style.setProperty("transform", "translate(-50%, -50%)", "important");
                canvas.style.setProperty("margin", "0", "important");
            }
        }
        fixCanvas();
        setInterval(fixCanvas, 100);
        window.addEventListener("resize", fixCanvas);
    </script>"""
    html = html.replace("</body>", observer_script + "\n</body>")
    print("    [OK] Responsive fullscreen canvas script injected")
else:
    print("    [OK] Canvas script already present, skipping")

with open("build/web/index.html", "w") as f:
    f.write(html)
PYEOF

echo "==> Verifying patches..."
grep -n "autorun" build/web/index.html || true
grep -n "pythonrc" build/web/index.html && echo "    [WARN] pythonrc line still present!" || echo "    [OK] pythonrc removed"
grep -n "fixCanvas" build/web/index.html > /dev/null && echo "    [OK] Canvas script present" || echo "    [WARN] Canvas script missing!"
grep -n "05050F" build/web/index.html > /dev/null && echo "    [OK] body background patched" || echo "    [WARN] body background not patched!"
grep -n "100vmin" build/web/index.html > /dev/null && echo "    [OK] canvas responsive sizing patched" || echo "    [WARN] canvas sizing not patched!"

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