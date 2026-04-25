import unittest
import pygame
from src.render import draw_pause_menu, draw_shop

class TestRenderUI(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.Surface((800, 600))

    def test_pause_menu_rects(self):
        # Ensure the pause menu returns three button rects
        resume, menu, quit_btn = draw_pause_menu(self.screen, 800, 600)
        self.assertIsInstance(resume, pygame.Rect)
        self.assertIsInstance(menu, pygame.Rect)
        self.assertIsInstance(quit_btn, pygame.Rect)

    def test_shop_item_generation(self):
        shop_items = [
            {"name": "Potion", "price": 10},
            {"name": "Shield", "price": 50}
        ]
        # Ensure it returns a rect for every item provided
        rects = draw_shop(self.screen, 800, 600, 100, shop_items)
        self.assertEqual(len(rects), 2)