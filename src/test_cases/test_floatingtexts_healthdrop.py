import unittest
import pygame
from src.floating_texts import FloatingText
from src.health_drop import HealthDrop

class TestVFXAndPickups(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def test_floating_text_lifecycle(self):
        ft = FloatingText(100, 100, "Damage!", duration_ms=100)
        initial_y = ft.y
        
        # Simulate update
        is_alive = ft.update()
        self.assertTrue(is_alive)
        self.assertTrue(ft.y < initial_y) # Should float up
        
        # Simulate death
        pygame.time.delay(110)
        is_alive = ft.update()
        self.assertFalse(is_alive)

    def test_health_drop_rect(self):
        drop = HealthDrop(50, 50, 20)
        drop.update()
        self.assertEqual(drop.rect.center, (50, 50))
        player = type("PlayerStub", (), {"max_health": 100})()
        self.assertAlmostEqual(drop.heal_fraction, 0.2)
        self.assertEqual(drop.heal_for(player), 20)