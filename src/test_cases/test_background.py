import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import unittest
import pygame
from src.background import SpaceBackground

class TestBackground(unittest.TestCase):

    # Set up a test background for testing
    def setUp(self):
        # Pygame must be initialized for draw calls
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        self.bg = SpaceBackground(800, 600)

    # Test that the background initializes with the correct number of layers and stars
    def test_layer_generation(self):
        """Requirement: Should have 3 layers with specific star counts."""
        self.assertEqual(len(self.bg.layers), 3)
        # Layer 1 (Farthest) should have 50 stars
        self.assertEqual(len(self.bg.layers[0]["stars"]), 50)

    # Test that each star has the required attributes and that size is within expected range
    def test_star_attributes(self):
        """Requirement: Each star must have X, Y, Size, and Color (RGBA/RGB)."""
        first_star = self.bg.layers[0]["stars"][0]
        # [x, y, size, color]
        self.assertEqual(len(first_star), 4)
        # Check that size is within (1, 2) for layer 0
        self.assertTrue(1 <= first_star[2] <= 2)

    # Test that the background correctly fills the surface with the background color
    def test_background_fill(self):
        """Requirement: Surface is filled with bg_color during update."""
        surface = pygame.Surface((800, 600))
        self.bg.update_and_draw(surface, (100, 100))
        # Check the color of a pixel that likely has no star (0,0)
        self.assertEqual(surface.get_at((0, 0))[:3], (5, 5, 15))