import unittest
import pygame
from src.world import World

class TestWorld(unittest.TestCase):
    def setUp(self):
        self.width = 1000
        self.height = 1000
        self.world = World(self.width, self.height)

    def test_border_creation(self):
        """Requirement: Should create exactly 4 boundary walls."""
        self.assertEqual(len(self.world.walls), 4)
        for wall in self.world.walls:
            self.assertIsInstance(wall, pygame.Rect)

    def test_wall_positions(self):
        """Verify walls are placed at the edges of the specified dimensions."""
        # Top wall
        self.assertEqual(self.world.walls[0].top, 0)
        # Bottom wall
        self.assertEqual(self.world.walls[1].bottom, self.height)
        # Left wall
        self.assertEqual(self.world.walls[2].left, 0)
        # Right wall
        self.assertEqual(self.world.walls[3].right, self.width)

    def test_wall_thickness(self):
        """Verify walls have the defined thickness (8.8 rounded for Rect)."""
        # Rect converts floats to ints, so 8.8 becomes 8
        self.assertEqual(self.world.walls[0].height, 8)