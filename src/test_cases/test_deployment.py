import pytest
from pathlib import Path
import re

def test_no_sys_exit_in_game():
    source = Path("src/game.py").read_text()
    assert "sys.exit()" not in source

def test_no_bare_asyncio_imports():
    """Catch stray 'from asyncio import X' in src files"""
    for path in Path("src").glob("*.py"):
        source = path.read_text()
        assert "from asyncio import" not in source, \
            f"Illegal asyncio import in {path.name}"

def test_resolve_asset_path_used_for_sounds():
    source = Path("src/game.py").read_text()
    # All pygame.mixer.Sound calls should use resolve_asset_path
    calls = re.findall(r'pygame\.mixer\.Sound\((.*?)\)', source)
    for call in calls:
        assert "resolve_asset_path" in call, \
            f"Sound loaded without resolve_asset_path: {call}"

def test_docs_index_has_hidpi_fix():
    index = Path("docs/index.html").read_text()
    assert "fixCanvas" in index

def test_docs_index_no_pythonrc():
    index = Path("docs/index.html").read_text()
    assert "pythonrc.py" not in index

def test_docs_index_no_100_percent_canvas():
    index = Path("docs/index.html").read_text()
    assert "width: 100%" not in index