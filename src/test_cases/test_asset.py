import unittest
import os
from pathlib import Path
from src.assets import resolve_asset_path

class TestAssets(unittest.TestCase):
    def test_resolve_existing_asset(self):
        """Should return a valid path string for an existing file."""
        # Create a temporary dummy file to test resolution
        test_file = "test_asset.txt"
        Path(test_file).touch()
        
        try:
            resolved = resolve_asset_path(test_file)
            self.assertTrue(os.path.exists(resolved))
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_resolve_nonexistent_asset(self):
        """Should raise FileNotFoundError for missing assets."""
        with self.assertRaises(FileNotFoundError):
            resolve_asset_path("fake_sprite_12345.png")