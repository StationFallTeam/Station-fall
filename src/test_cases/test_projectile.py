import unittest
from unittest.mock import patch
import pygame
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.player import Player
from src.projectile import Projectile
from src.collision import CollisionSystem

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
        self.collision_system = CollisionSystem()

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

    # Test that projectiles are removed when colliding with walls via collision system
    def test_projectile_wall_collision_via_collision_system(self):
        """Requirement: Projectiles should be removed when hitting walls through collision system."""
        # Initialize player movement deltas (required by collision system)
        self.player._last_dx = 0
        self.player._last_dy = 0
        
        # Create a projectile moving right
        bullet = Projectile((100, 100), (10, 0), radius=6, color=(225, 50, 50), lifetime_ms=1200)
        bullets = [bullet]
        
        # Create a wall that overlaps with the projectile's current position
        wall = pygame.Rect(95, 95, 40, 40)  # Overlaps with projectile at (100,100)
        self.collision_system.update_walls([wall])
        
        # Let collision system handle the collision (should detect overlap)
        self.collision_system.handle_all_collisions(self.player, [], bullets)
        
        # Projectile should be removed from list due to wall collision
        self.assertEqual(len(bullets), 0)


if __name__ == "__main__":
    unittest.main()