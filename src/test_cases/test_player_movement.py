import unittest
from unittest.mock import patch
import pygame
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.player import Player
from src.collision import CollisionSystem

class FakeKeys:
    def __init__(self, pressed=None):
        self.pressed = pressed or set()

    def __getitem__(self, key):
        return key in self.pressed

class TestPlayerMovement(unittest.TestCase):

    # Set up a test player for testing
    def setUp(self):
        # Pygame must be initialized for player setup
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

        fake_sheet = pygame.Surface((48 * 4, 48 * 4), pygame.SRCALPHA)
        patcher = patch("pygame.image.load", return_value=fake_sheet)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.player = Player(100, 100)
        # Initialize movement deltas required by collision system
        self.player._last_dx = 0
        self.player._last_dy = 0
        self.collision_system = CollisionSystem()

    # Test that the player moves right when no wall blocks movement
    def test_player_moves_right_without_wall(self):
        """Requirement: Player should move right if no wall is in the way."""
        start_x = self.player.rect.x
        keys = FakeKeys({pygame.K_d})

        # Update player movement (no walls in collision system)
        self.player.update(keys)

        self.assertGreater(self.player.rect.x, start_x)

    # Test that the collision system stops player when hitting a wall
    def test_player_stops_when_hitting_wall_via_collision_system(self):
        """Requirement: Player should stop at the wall when collision system resolves collision."""
        # Position player and create wall to the right
        self.player.x = 100
        self.player.y = 100
        self.player.rect.topleft = (self.player.x, self.player.y)
        
        wall = pygame.Rect(self.player.rect.right + 5, self.player.rect.y, 40, self.player.rect.height)
        self.collision_system.update_walls([wall])
        
        keys = FakeKeys({pygame.K_d})

        # Move player towards wall 
        self.player.update(keys)
        
        # Now let collision system resolve the movement
        self.collision_system.handle_all_collisions(self.player, [], [])
        
        # Player should be stopped at the wall
        self.assertLessEqual(self.player.rect.right, wall.left)

    # Test trigger detection in the new collision system
    def test_player_trigger_detection(self):
        """Requirement: Collision system should detect when player is in trigger areas."""
        # Position player
        self.player.x = 100
        self.player.y = 100
        self.player.rect.topleft = (self.player.x, self.player.y)
        
        # Create trigger area that overlaps with player
        trigger_rect = pygame.Rect(95, 95, 20, 20)
        self.collision_system.add_triggers({"test_trigger": [trigger_rect]})
        
        # Check if player is in trigger
        in_trigger = self.collision_system.is_in_trigger(self.player, "test_trigger")
        self.assertTrue(in_trigger)
        
        # Move player away and check again
        self.player.x = 200
        self.player.rect.topleft = (self.player.x, self.player.y)
        in_trigger = self.collision_system.is_in_trigger(self.player, "test_trigger")
        self.assertFalse(in_trigger)

    # Test that the collision system stops player when hitting a wall above
    def test_player_stops_when_hitting_top_wall(self):
        """Requirement: Player should stop at the wall when moving upward via collision system."""
        # Position player and create wall above
        self.player.x = 100
        self.player.y = 100
        self.player.rect.topleft = (self.player.x, self.player.y)
        
        wall = pygame.Rect(self.player.rect.x, self.player.rect.top - 10, self.player.rect.width, 10)
        self.collision_system.update_walls([wall])
        
        keys = FakeKeys({pygame.K_w})

        # Move player towards wall
        self.player.update(keys)
        
        # Let collision system resolve the collision
        self.collision_system.handle_all_collisions(self.player, [], [])

        # Player should be stopped at the wall
        self.assertGreaterEqual(self.player.rect.top, wall.bottom)


if __name__ == "__main__":
    unittest.main()