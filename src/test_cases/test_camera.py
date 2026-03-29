import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock
import pygame
from camera import Camera

class TestCamera(unittest.TestCase):
    # Set up a test camera and a mock target for testing
    def setUp(self):
        # Initialize a 800x600 camera
        self.camera = Camera(800, 600)
        # Create a mock target (player)
        self.mock_target = Mock() # Use Mock directly
        self.mock_target.rect = pygame.Rect(1000, 1000, 50, 50)


    # Test that the camera initializes at the correct position
    def test_camera_initial_position(self):
        """Requirement: Camera should start at (0,0)."""
        self.assertEqual(self.camera.camera.topleft, (0, 0))

    # Test that the camera correctly translates world coordinates to screen coordinates
    def test_apply_rect(self):
        """Requirement: Translates world coordinates based on camera offset."""
        # Move camera to (-500, -500)
        self.camera.camera.topleft = (-500, -500)
        world_rect = pygame.Rect(600, 600, 50, 50)
        # Screen rect should be 600 - 500 = 100
        screen_rect = self.camera.apply(world_rect)
        self.assertEqual(screen_rect.topleft, (100, 100))
    
    # Test that the camera correctly follows the target
    def test_screen_to_world(self):
        """Requirement: Correctly reverse screen pos back to world pos."""
        self.camera.camera.x = -200
        self.camera.camera.y = -200
        # If camera is at -200, screen (0,0) is world (200, 200)
        world_pos = self.camera.screen_to_world((0, 0))
        self.assertEqual(world_pos, (200, 200))