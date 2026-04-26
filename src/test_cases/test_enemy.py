import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import pygame
from enemy import Enemy

def make_enemy(x=100, y=100):
    with patch("enemy.pygame.image.load") as mock_load:
        mock_surface = MagicMock()
        mock_surface.convert_alpha.return_value = pygame.Surface((192, 192), pygame.SRCALPHA)
        mock_load.return_value = mock_surface
        return Enemy(x, y)


class TestEnemyInit(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.enemy = make_enemy(100, 200)

    def tearDown(self):
        pygame.quit()

    def test_position(self):
        self.assertEqual(self.enemy.x, 100)
        self.assertEqual(self.enemy.y, 200)

    def test_speed(self):
        self.assertEqual(self.enemy.speed, 1.5)

    def test_default_direction(self):
        self.assertEqual(self.enemy.direction, "down")

    def test_default_frame_index(self):
        self.assertEqual(self.enemy.frame_index, 0.0)

    def test_rect_size(self):
        self.assertEqual(self.enemy.rect.width, 32)
        self.assertEqual(self.enemy.rect.height, 32)

    def test_draw_rect_size(self):
        self.assertEqual(self.enemy.drawRect.width, 48)
        self.assertEqual(self.enemy.drawRect.height, 48)

    def test_animations_loaded(self):
        for direction in ["down", "left", "right", "up"]:
            self.assertEqual(len(self.enemy.animations[direction]), 4)

    def test_initial_health(self):
        self.assertEqual(self.enemy.health, 15)

    def test_moving_starts_true(self):
        self.assertTrue(self.enemy.moving)


class TestEnemyUpdate(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.enemy = make_enemy(100, 100)

    def tearDown(self):
        pygame.quit()

    def _make_player_rect(self, x, y):
        r = pygame.Rect(x, y, 32, 32)
        return r

    def test_moves_right_when_player_is_to_the_right(self):
        player_rect = self._make_player_rect(200, 100)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertGreater(self.enemy.x, 100)
        self.assertEqual(self.enemy.direction, "right")

    def test_moves_left_when_player_is_to_the_left(self):
        player_rect = self._make_player_rect(0, 100)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertLess(self.enemy.x, 100)
        self.assertEqual(self.enemy.direction, "left")

    def test_moves_down_when_player_is_below(self):
        player_rect = self._make_player_rect(100, 200)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertGreater(self.enemy.y, 100)
        self.assertEqual(self.enemy.direction, "down")

    def test_moves_up_when_player_is_above(self):
        player_rect = self._make_player_rect(100, 0)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertLess(self.enemy.y, 100)
        self.assertEqual(self.enemy.direction, "up")

    def test_not_moving_when_player_at_same_position(self):
        player_rect = self._make_player_rect(100, 100)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertFalse(self.enemy.moving)

    def test_rect_follows_position(self):
        player_rect = self._make_player_rect(200, 100)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertEqual(self.enemy.rect.left, round(self.enemy.x))
        self.assertEqual(self.enemy.rect.top, round(self.enemy.y))

    def test_draw_rect_midbottom_matches_rect(self):
        player_rect = self._make_player_rect(200, 200)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertEqual(self.enemy.drawRect.midbottom, self.enemy.rect.midbottom)

    def test_frame_index_advances_when_moving(self):
        player_rect = self._make_player_rect(200, 100)
        self.enemy.frame_index = 0.0
        self.enemy.update(player_rect, [], {}, 32)
        self.assertGreater(self.enemy.frame_index, 0.0)

    def test_frame_index_resets_when_not_moving(self):
        player_rect = self._make_player_rect(100, 100)
        self.enemy.frame_index = 2.0
        self.enemy.update(player_rect, [], {}, 32)
        self.assertEqual(self.enemy.frame_index, 0)

    def test_frame_index_wraps_around(self):
        player_rect = self._make_player_rect(200, 100)
        self.enemy.frame_index = 3.95
        self.enemy.update(player_rect, [], {}, 32)
        self.assertLess(self.enemy.frame_index, 4.0)

    def test_last_dx_stored(self):
        player_rect = self._make_player_rect(200, 100)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertEqual(self.enemy._last_dx, self.enemy.speed)

    def test_last_dy_stored_when_moving_down(self):
        player_rect = self._make_player_rect(100, 200)
        self.enemy.update(player_rect, [], {}, 32)
        self.assertEqual(self.enemy._last_dy, self.enemy.speed)


class TestEnemyDamage(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.enemy = make_enemy()

    def tearDown(self):
        pygame.quit()

    def test_take_damage_reduces_health(self):
        self.enemy.take_damage(5)
        self.assertEqual(self.enemy.health, 10)

    def test_is_dead_false_when_alive(self):
        self.assertFalse(self.enemy.is_dead)

    def test_is_dead_true_when_health_zero(self):
        self.enemy.take_damage(15)
        self.assertTrue(self.enemy.is_dead)

    def test_is_dead_true_when_overkilled(self):
        self.enemy.take_damage(999)
        self.assertTrue(self.enemy.is_dead)

    def test_max_health(self):
        self.assertEqual(self.enemy.max_health, 15)

    def test_health_does_not_exceed_max(self):
        self.enemy.take_damage(5)
        self.assertLessEqual(self.enemy.health, self.enemy.max_health)


class TestEnemyDraw(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.enemy = make_enemy(100, 100)
        self.screen = pygame.Surface((800, 600))
        self.camera = MagicMock()
        self.camera.apply.return_value = pygame.Rect(90, 90, 48, 48)

    def tearDown(self):
        pygame.quit()

    def test_draw_calls_camera_apply(self):
        self.enemy.draw(self.screen, self.camera)
        self.camera.apply.assert_called_once_with(self.enemy.drawRect)

    def test_draw_uses_correct_direction_frame(self):
        blitted = []

        class TrackingScreen(pygame.Surface):
            def blit(self, source, dest, *args, **kwargs):
                blitted.append(source)
                return super().blit(source, dest, *args, **kwargs)

        screen = TrackingScreen((800, 600))
        self.enemy.direction = "left"
        self.enemy.frame_index = 1.0
        sentinel = pygame.Surface((48, 48), pygame.SRCALPHA)
        self.enemy.animations["left"][1] = sentinel

        self.enemy.draw(screen, self.camera)
        self.assertEqual(blitted[0], sentinel)


if __name__ == "__main__":
    unittest.main()