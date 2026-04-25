import unittest
import pygame
import math
from src.ranged_enemy import RangedEnemy, INNER_DEADZONE, OUTER_DEADZONE

class TestRangedEnemy(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Mocking display for sprite loading if necessary, though Surface works
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        self.enemy = RangedEnemy(100, 100)

    def test_movement_fleeing(self):
        # Place player very close to enemy
        player_rect = pygame.Rect(110, 110, 32, 32)
        initial_x, initial_y = self.enemy.x, self.enemy.y
        self.enemy.update(player_rect)
        # Distance is < INNER_DEADZONE, enemy should move away
        self.assertTrue(self.enemy.x < initial_x or self.enemy.y < initial_y)

    def test_movement_approach(self):
        # Place player far away
        player_rect = pygame.Rect(500, 500, 32, 32)
        initial_x, initial_y = self.enemy.x, self.enemy.y
        self.enemy.update(player_rect)
        # Distance is > OUTER_DEADZONE, enemy should move closer
        self.assertTrue(self.enemy.x > initial_x or self.enemy.y > initial_y)

    def test_projectile_generation(self):
        # Force a state where the enemy can shoot
        player_rect = pygame.Rect(250, 100, 32, 32) # Within shooting range
        self.enemy._shoot_timer = 0 # Reset cooldown
        self.enemy.update(player_rect)
        
        projectiles = self.enemy.pop_projectiles()
        self.assertEqual(len(projectiles), 1)
        # Ensure the list was cleared after popping
        self.assertEqual(len(self.enemy._pending_projectiles), 0)