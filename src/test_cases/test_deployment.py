import unittest
from pathlib import Path
import re

class TestDeployment(unittest.TestCase):

    def test_no_sys_exit_in_game(self):
        source = Path("src/game.py").read_text()
        self.assertNotIn("sys.exit()", source)

    def test_no_bare_asyncio_imports(self):
        for path in Path("src").glob("*.py"):
            source = path.read_text()
            self.assertNotIn("from asyncio import", source,
                f"Illegal asyncio import in {path.name}")

    def test_resolve_asset_path_used_for_sounds(self):
        source = Path("src/game.py").read_text()
        calls = re.findall(r'pygame\.mixer\.Sound\((.*?)\)', source)
        for call in calls:
            self.assertIn("resolve_asset_path", call,
                f"Sound loaded without resolve_asset_path: {call}")

    def test_docs_index_no_pythonrc(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")

        html = index_path.read_text(encoding="utf-8", errors="ignore")
        self.assertNotIn("pythonrc.py", html)

    def test_docs_index_has_canvas_sizing(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")

        html = index_path.read_text(encoding="utf-8", errors="ignore")

        self.assertIn("canvas.emscripten", html)
        self.assertIn("width:", html)
        self.assertIn("height:", html)
    
    def _load_html(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")
        return index_path.read_text(encoding="utf-8", errors="ignore")

    def test_canvas_exists(self):
        html = self._load_html()
        self.assertIn("<canvas", html)
        self.assertIn("emscripten", html)

    def test_canvas_not_fixed_size(self):
        html = self._load_html()

        self.assertNotIn("width: 920px", html)
        self.assertNotIn("height: 920px", html)

    def test_canvas_is_responsive(self):
        html = self._load_html()

        self.assertTrue(
            "width: 100%" in html or
            "width:100%" in html or
            "max-width" in html,
            "Canvas is not responsive"
        )

    def test_no_pythonrc(self):
        html = self._load_html()
        self.assertNotIn("pythonrc.py", html)

    def test_no_legacy_hidpi_fix(self):
        html = self._load_html()

        self.assertNotIn("fixCanvas", html)

if __name__ == "__main__":
    unittest.main()