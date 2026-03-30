import unittest
from unittest.mock import patch
import pygame
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.player import Player
from src.projectile import Projectile

class TestProjectile(unittest.TestCase):

    # Set up a test player for projectile testing
    def setUp(self):
        # Pygame must be initialized for player setup
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

        fake_sheet = pygame.Surface((48 * 4, 48 * 4), pygame.SRCALPHA)
        patcher = patch("pygame.image.load", return_value=fake_sheet)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.player = Player(100, 100)

    # Test that player.shoot returns a Projectile object for a valid target
    def test_player_shoot_returns_projectile(self):
        """Requirement: Shooting at a valid target should return a Projectile."""
        target = (300, 300)
        bullet = self.player.shoot(target)

        self.assertIsNotNone(bullet)
        self.assertIsInstance(bullet, Projectile)

    # Test that player.shoot returns None when target is the player's center
    def test_player_shoot_returns_none_if_target_is_player_center(self):
        """Requirement: Shooting at the player's exact center should return None."""
        target = self.player.rect.center
        bullet = self.player.shoot(target)

        self.assertIsNone(bullet)

    # Test that a projectile moves after update is called
    def test_projectile_moves_after_update(self):
        """Requirement: Projectile position should change after update."""
        bullet = Projectile((100, 100), (10, 0), radius=6, color=(225, 50, 50), lifetime_ms=1200)
        start_x = bullet.pos.x

        bullet.update()

        self.assertGreater(bullet.pos.x, start_x)

    # Test that a projectile expires after its lifetime passes
    def test_projectile_expires_after_lifetime(self):
        """Requirement: Projectile should be dead after its lifetime expires."""
        bullet = Projectile((100, 100), (10, 0), radius=6, color=(225, 50, 50), lifetime_ms=1)

        pygame.time.delay(5)

        self.assertTrue(bullet.is_dead())


if __name__ == "__main__":
    unittest.main()