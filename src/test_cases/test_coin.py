import unittest
from unittest.mock import patch
import pygame
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.coin import Coin
from src.player import Player


class FakeCamera:
    def apply(self, rect):
        return rect


class TestCoin(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

        fake_sheet = pygame.Surface((48 * 4, 48 * 4), pygame.SRCALPHA)
        patcher = patch("pygame.image.load", return_value=fake_sheet)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.player = Player(100, 100)
        if not hasattr(self.player, "money"):
            self.player.money = 0


    def test_coin_initialization(self):
        coin = Coin(100, 150)

        self.assertEqual(coin.value, 1)
        self.assertEqual(coin.radius, 8)
        self.assertEqual(coin.pos.x, 100)
        self.assertEqual(coin.pos.y, 150)

    def test_coin_custom_value(self):
        coin = Coin(0, 0, value=5)
        self.assertEqual(coin.value, 5)

    def test_coin_rect_center(self):
        coin = Coin(120, 180)
        self.assertEqual(coin.rect.center, (120, 180))

    def test_coin_position_is_vector(self):
        coin = Coin(0, 0)
        self.assertIsInstance(coin.pos, pygame.Vector2)

    def test_coin_update_sync(self):
        coin = Coin(100, 100)

        coin.pos.x = 200
        coin.pos.y = 300
        coin.update()

        self.assertEqual(coin.rect.center, (200, 300))

    def test_coin_update_float_position(self):
        coin = Coin(0, 0)

        coin.pos.x = 99.7
        coin.pos.y = 120.3
        coin.update()

        self.assertEqual(coin.rect.center, (99, 120))

    def test_coin_draw_runs(self):
        coin = Coin(100, 100)
        screen = pygame.Surface((300, 300))
        camera = FakeCamera()

        try:
            coin.draw(screen, camera)
        except Exception as e:
            self.fail(f"draw crashed: {e}")

    def test_coin_draw_center_color(self):
        coin = Coin(100, 100)
        screen = pygame.Surface((300, 300))
        screen.fill((0, 0, 0))
        camera = FakeCamera()

        coin.draw(screen, camera)

        self.assertEqual(screen.get_at((100, 100))[:3], (255, 240, 120))

    def test_coin_draw_does_not_affect_far_pixels(self):
        coin = Coin(100, 100)
        screen = pygame.Surface((300, 300))
        screen.fill((0, 0, 0))
        camera = FakeCamera()

        coin.draw(screen, camera)

        self.assertEqual(screen.get_at((10, 10))[:3], (0, 0, 0))

    def test_player_collects_coin(self):
        coin = Coin(100, 100, value=2)
        coins = [coin]

        # simulate logic from game.py
        for c in coins[:]:
            c.update()
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)

        self.assertEqual(len(coins), 0)
        self.assertEqual(self.player.money, 2)

    def test_player_does_not_collect_far_coin(self):
        coin = Coin(300, 300, value=2)
        coins = [coin]

        for c in coins[:]:
            c.update()
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)

        self.assertEqual(len(coins), 1)
        self.assertEqual(self.player.money, 0)

    def test_player_collects_multiple_coins(self):
        coins = [
            Coin(100, 100, value=1),
            Coin(100, 100, value=2),
            Coin(100, 100, value=3),
        ]

        for c in coins[:]:
            c.update()
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)

        self.assertEqual(len(coins), 0)
        self.assertEqual(self.player.money, 6)

    def test_only_overlapping_coin_collected(self):
        coins = [
            Coin(100, 100, value=2),
            Coin(300, 300, value=4),
        ]

        for c in coins[:]:
            c.update()
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)

        self.assertEqual(len(coins), 1)
        self.assertEqual(self.player.money, 2)

    def test_coin_rect_center_matches_position(self):
        coin = Coin(80, 60)
        self.assertEqual(coin.rect.center,(80,60))

    def test_coin_rect_topleft_correct(self):
        coin = Coin(100, 100)
        expected_x = 100 - coin.radius
        expected_y = 100 - coin.radius
        self.assertEqual(coin.rect.topleft, (expected_x, expected_y))

    def test_coin_update_no_movement(self):
        coin = Coin(50, 50)
        before = coin.rect.center
        coin.update()
        self.assertEqual(before, coin.rect.center)

    def test_coin_color_is_rgb_tuple(self):
        coin = Coin(0, 0)
        self.assertEqual(len(coin.color), 3)

    def test_coin_radius_used(self):
        coin = Coin(0, 0)
        self.assertEqual(coin.radius, 8)

    def test_coin_draw_multiple_times(self):
        coin = Coin(100, 100)
        screen = pygame.Surface((300, 300))
        camera = FakeCamera()

        coin.draw(screen, camera)
        coin.draw(screen, camera)
    
    def test_coin_draw_after_update(self):
        coin = Coin(100, 100)
        coin.pos.x += 20
        coin.update()

        screen = pygame.Surface((300, 300))
        camera = FakeCamera()

        coin.draw(screen, camera)

    def test_coin_update_does_not_change_radius(self):
        coin = Coin(0, 0)
        coin.update()
        self.assertEqual(coin.radius, 8)

    def test_player_collects_coin_on_edge_touch(self):
        coin = Coin(100, 100)
        coin.update()
        self.player.rect.center = (100 + coin.radius, 100)
        coins = [coin]
        for c in coins[:]:
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)
        self.assertEqual(self.player.money, 1)

    def test_player_collects_large_value_coin(self):
        coin = Coin(100, 100, value=999)
        coins = [coin]
        for c in coins[:]:
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)
        self.assertEqual(self.player.money, 999)

    def test_player_money_accumulates(self):
        coins = [Coin(100, 100, 2), Coin(100, 100, 3)]
        for c in coins[:]:
            if self.player.rect.colliderect(c.rect):
                self.player.money += c.value
                coins.remove(c)
        self.assertEqual(self.player.money, 5)

    def test_coin_removed_reduces_list_size(self):
        coins = [Coin(100, 100), Coin(200, 200)]
        for c in coins[:]:
            if self.player.rect.colliderect(c.rect):
                coins.remove(c)
        self.assertEqual(len(coins), 1)

    def test_empty_coin_list_no_crash(self):
        coins = []
        for c in coins[:]:
            if self.player.rect.colliderect(c.rect):
                coins.remove(c)
        self.assertEqual(len(coins), 0)

    def test_coin_rect_is_integer(self):
        coin = Coin(0, 0)
        coin.pos.x = 55.9
        coin.pos.y = 88.1
        coin.update()

        self.assertIsInstance(coin.rect.center[0], int)
        self.assertIsInstance(coin.rect.center[1], int)

    def test_draw_does_not_modify_coin_state(self):
        coin = Coin(100, 100)
        original_pos = (coin.pos.x, coin.pos.y)
        screen = pygame.Surface((300, 300))
        camera = FakeCamera()
        coin.draw(screen, camera)
        self.assertEqual((coin.pos.x, coin.pos.y), original_pos)

if __name__ == "__main__":
    unittest.main()