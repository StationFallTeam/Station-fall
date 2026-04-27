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

    def test_docs_index_has_hidpi_fix(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")
        self.assertIn("fixCanvas", index_path.read_text())

    def test_docs_index_no_pythonrc(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")
        self.assertNotIn("pythonrc.py", index_path.read_text())

    def test_docs_index_no_100_percent_canvas(self):
        index_path = Path("docs/index.html")
        if not index_path.exists():
            self.skipTest("docs/index.html not built yet")
        self.assertNotIn("width: 100%", index_path.read_text())

if __name__ == "__main__":
    unittest.main()