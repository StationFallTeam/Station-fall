import unittest
from unittest.mock import patch
import pygame
from player import Player


class FakeKeys:
    def __init__(self, pressed=None):
        self.pressed = pressed or set()

    def __getitem__(self, key):
        return key in self.pressed

class TestPlayerMovement(unittest.TestCase):

    # Set up a test player for testing
    def setUp(self):
        # Pygame must be initialized for player setup
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

        fake_sheet = pygame.Surface((48 * 4, 48 * 4), pygame.SRCALPHA)
        patcher = patch("pygame.image.load", return_value=fake_sheet)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.player = Player(100, 100)

    # Test that the player moves right when no wall blocks movement
    def test_player_moves_right_without_wall(self):
        """Requirement: Player should move right if no wall is in the way."""
        start_x = self.player.rect.x
        keys = FakeKeys({pygame.K_d})

        self.player.update(keys, [])

        self.assertGreater(self.player.rect.x, start_x)

    # Test that the player stops when colliding with a wall on the right
    def test_player_stops_when_hitting_wall(self):
        """Requirement: Player should stop at the wall when moving right into it."""
        wall = pygame.Rect(self.player.rect.right + 1, self.player.rect.y, 40, self.player.height)
        keys = FakeKeys({pygame.K_d})

        self.player.update(keys, [wall])

        self.assertEqual(self.player.rect.right, wall.left)

    # Test that the player stops when colliding with a wall above
    def test_player_stops_when_hitting_top_wall(self):
        """Requirement: Player should stop at the wall when moving upward into it."""
        wall = pygame.Rect(self.player.rect.x, self.player.rect.top - 20, self.player.width, 20)
        keys = FakeKeys({pygame.K_w})

        self.player.update(keys, [wall])

        self.assertEqual(self.player.rect.top, wall.bottom)


if __name__ == "__main__":
    unittest.main()