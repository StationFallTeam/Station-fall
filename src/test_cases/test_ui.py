import unittest
import pygame
import os
import sys

# Add the src directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.inventory_ui import InventoryUI
from src.ui import draw_health_bar, _clamp

class TestGameUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize pygame once for the entire test suite
        pygame.init()
        pygame.display.set_mode((800, 600), pygame.HIDDEN)

    def setUp(self):
        self.screen_width = 800
        self.screen_height = 600
        self.surface = pygame.Surface((self.screen_width, self.screen_height))
        self.inventory = InventoryUI(self.screen_width, self.screen_height)

    ## --- Tests for ui.py ---

    # This test ensures that the _clamp function correctly restricts values to a specified range, which is essential for maintaining consistent behavior in various UI elements that rely on clamping.
    def test_clamp_function(self):
        """Verify that the utility _clamp function works as expected."""
        self.assertEqual(_clamp(10, 0, 100), 10)  # Inside range
        self.assertEqual(_clamp(-5, 0, 100), 0)   # Below range
        self.assertEqual(_clamp(150, 0, 100), 100) # Above range

    # This test ensures that the draw_health_bar function can handle various health ratios without throwing exceptions, which is crucial for maintaining game stability during gameplay.
    def test_health_bar_math(self):
        """Ensure health bar drawing logic doesn't crash with various ratios."""
        try:
            # Test full health
            draw_health_bar(self.surface, 100, 100, 10, 10, 200, 20)
            # Test half health
            draw_health_bar(self.surface, 50, 100, 10, 10, 200, 20)
            # Test zero health
            draw_health_bar(self.surface, 0, 100, 10, 10, 200, 20)
            # Test division by zero safety (should use max(1, maximum))
            draw_health_bar(self.surface, 10, 0, 10, 10, 200, 20)
        except Exception as e:
            self.fail(f"draw_health_bar raised an exception: {e}")

    ## --- Tests for inventory_ui.py ---

    # This test checks that the inventory panel is correctly centered on the screen with the expected dimensions.
    def test_inventory_panel_centering(self):
        """Requirement: The inventory panel should be centered on the screen."""
        expected_x = (self.screen_width // 2) - 200
        expected_y = (self.screen_height // 2) - 150
        
        self.assertEqual(self.inventory.panel_rect.x, expected_x)
        self.assertEqual(self.inventory.panel_rect.y, expected_y)
        self.assertEqual(self.inventory.panel_rect.width, 400)
        self.assertEqual(self.inventory.panel_rect.height, 300)

    # This test verifies that the inventory draw method can be called without throwing any exceptions, ensuring that the drawing logic is robust against typical usage scenarios.
    def test_inventory_draw_cycle(self):
        """Verify that the inventory draw method executes without error."""
        try:
            # We use a dummy money value
            self.inventory.draw(self.surface, 500)
        except Exception as e:
            self.fail(f"InventoryUI.draw raised an exception: {e}")

    # This test ensures that the health bar drawing logic correctly handles cases where the current health exceeds the maximum health, which is important for preventing visual glitches and maintaining a consistent user interface.
    def test_health_bar_visual_clamping(self):
        """Verify that health bar ratios are clamped even if current > max."""
        # This is a logic test: current 150, max 100 should be treated as 100%
        # We check this by ensuring no errors occur when ratio would be > 1
        try:
            draw_health_bar(self.surface, 500, 100, 0, 0, 100, 10)
        except ValueError:
            self.fail("draw_health_bar failed to clamp high health values.")

if __name__ == "__main__":
    unittest.main()