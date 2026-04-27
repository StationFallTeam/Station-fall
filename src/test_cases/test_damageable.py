import unittest
import pygame
from src.damageable import Damageable

class TestDamageable(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.max_hp = 100
        self.obj = Damageable(self.max_hp)

    def test_initialization(self):
        self.assertEqual(self.obj.health, self.max_hp)
        self.assertFalse(self.obj.is_invincible)

    def test_take_damage(self):
        self.obj.take_damage(20)
        self.assertEqual(self.obj.health, 80)
        self.assertTrue(self.obj.is_invincible)

    def test_invincibility_prevents_damage(self):
        self.obj.take_damage(20) # Health 80, is_invincible True
        self.obj.take_damage(20) # Should be ignored
        self.assertEqual(self.obj.health, 80)

    def test_health_floor_at_zero(self):
        self.obj.take_damage(200)
        self.assertEqual(self.obj.health, 0)

    def test_invincibility_expiry(self):
        self.obj.take_damage(10)
        # Manually force the last_hit_time back into the past to simulate time passing
        self.obj.last_hit_time = pygame.time.get_ticks() - 600 
        self.obj.update()
        self.assertFalse(self.obj.is_invincible)