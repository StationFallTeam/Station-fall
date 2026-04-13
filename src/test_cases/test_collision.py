import unittest
from unittest.mock import patch
import pygame
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.collision import CollisionSystem, collision_system, update_collision_walls, clear_temporary_walls, add_triggers, clear_triggers, is_in_trigger, handle_all_collisions


class MockPlayer:
    def __init__(self, x, y, width=32, height=32):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.drawRect = pygame.Rect(x, y, width, height)
        self.drawRect.midbottom = self.rect.midbottom
        self._last_dx = 0
        self._last_dy = 0
        self.health = 100
        self.is_invincible = False
    
    def take_damage(self, damage):
        self.health -= damage


class MockEnemy:
    def __init__(self, x, y, width=24, height=24):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.health = 50
        
    def take_damage(self, damage):
        self.health -= damage


class MockBullet:
    def __init__(self, x, y, damage=25, width=4, height=4):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.damage = damage
        
    def get_rect(self):
        return self.rect


class TestCollisionSystem(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        
        # Mock pygame.image.load to prevent file loading during tests
        fake_surface = pygame.Surface((32, 32))
        patcher = patch("pygame.image.load", return_value=fake_surface)
        self.addCleanup(patcher.stop)
        patcher.start()
        
        # Create a fresh collision system for each test
        self.collision_system = CollisionSystem()
        
    def tearDown(self):
        self.collision_system.walls.clear()
        self.collision_system.temporary_walls.clear()
        self.collision_system.triggers.clear()

    # Test basic wall management
    def test_update_walls(self):
        walls = [pygame.Rect(0, 0, 50, 50), pygame.Rect(100, 100, 30, 30)]
        self.collision_system.update_walls(walls)
        
        self.assertEqual(len(self.collision_system.walls), 2)
        self.assertEqual(self.collision_system.walls, walls)

    def test_add_temporary_walls(self):
        temp_walls = [pygame.Rect(200, 200, 20, 20)]
        self.collision_system.add_temporary_walls(temp_walls)
        
        self.assertEqual(len(self.collision_system.temporary_walls), 1)
        self.assertIn(temp_walls[0], self.collision_system.temporary_walls)

    def test_remove_temporary_walls(self):
        wall1 = pygame.Rect(200, 200, 20, 20)
        wall2 = pygame.Rect(250, 250, 20, 20)
        self.collision_system.add_temporary_walls([wall1, wall2])
        
        self.collision_system.remove_temporary_walls([wall1])
        
        self.assertEqual(len(self.collision_system.temporary_walls), 1)
        self.assertNotIn(wall1, self.collision_system.temporary_walls)
        self.assertIn(wall2, self.collision_system.temporary_walls)

    def test_clear_temporary_walls(self):
        temp_walls = [pygame.Rect(200, 200, 20, 20), pygame.Rect(250, 250, 20, 20)]
        self.collision_system.add_temporary_walls(temp_walls)
        
        self.collision_system.clear_temporary_walls()
        
        self.assertEqual(len(self.collision_system.temporary_walls), 0)

    def test_get_all_walls(self):
        static_walls = [pygame.Rect(0, 0, 50, 50)]
        temp_walls = [pygame.Rect(200, 200, 20, 20)]
        
        self.collision_system.update_walls(static_walls)
        self.collision_system.add_temporary_walls(temp_walls)
        
        all_walls = self.collision_system.get_all_walls()
        
        self.assertEqual(len(all_walls), 2)
        self.assertIn(static_walls[0], all_walls)
        self.assertIn(temp_walls[0], all_walls)

    # Test trigger system
    def test_add_triggers(self):
        triggers = {
            "test_trigger": [pygame.Rect(100, 100, 50, 50)]
        }
        self.collision_system.add_triggers(triggers)
        
        self.assertIn("test_trigger", self.collision_system.triggers)
        self.assertEqual(len(self.collision_system.triggers["test_trigger"]), 1)

    def test_clear_triggers(self):
        triggers = {
            "trigger1": [pygame.Rect(100, 100, 50, 50)],
            "trigger2": [pygame.Rect(200, 200, 30, 30)]
        }
        self.collision_system.add_triggers(triggers)
        
        self.collision_system.clear_triggers()
        
        self.assertEqual(len(self.collision_system.triggers), 0)

    def test_is_in_trigger_true(self):
        player = MockPlayer(100, 100)
        trigger_rect = pygame.Rect(95, 95, 50, 50)  # Overlaps with player
        self.collision_system.add_triggers({"test_trigger": [trigger_rect]})
        
        result = self.collision_system.is_in_trigger(player, "test_trigger")
        
        self.assertTrue(result)

    def test_is_in_trigger_false(self):
        player = MockPlayer(100, 100)
        trigger_rect = pygame.Rect(200, 200, 50, 50)  # Away from player
        self.collision_system.add_triggers({"test_trigger": [trigger_rect]})
        
        result = self.collision_system.is_in_trigger(player, "test_trigger")
        
        self.assertFalse(result)

    def test_is_in_trigger_nonexistent(self):
        player = MockPlayer(100, 100)
        
        result = self.collision_system.is_in_trigger(player, "nonexistent_trigger")
        
        self.assertFalse(result)

    # Test player wall collision resolution
    def test_player_wall_collision_x_axis(self):
        player = MockPlayer(100, 100)
        player._last_dx = 10  # Moving right
        player._last_dy = 0
        player.x = 110  # Moved position
        player.rect.x = 110
        
        # Wall blocking rightward movement
        wall = pygame.Rect(115, 95, 50, 50)
        walls = [wall]
        
        self.collision_system._resolve_player_wall_collision_proper(player, walls)
        
        # Player should be pushed back to original X position
        self.assertEqual(player.x, 100)
        self.assertEqual(player.rect.x, 100)

    def test_player_wall_collision_y_axis(self):
        player = MockPlayer(100, 100)
        player._last_dx = 0
        player._last_dy = -10  # Moving up
        player.y = 90  # Moved position
        player.rect.y = 90
        
        # Wall blocking upward movement
        wall = pygame.Rect(95, 85, 50, 50)
        walls = [wall]
        
        self.collision_system._resolve_player_wall_collision_proper(player, walls)
        
        # Player should be pushed back to original Y position
        self.assertEqual(player.y, 100)
        self.assertEqual(player.rect.y, 100)

    def test_player_no_collision(self):
        player = MockPlayer(100, 100)
        player._last_dx = 10
        player._last_dy = 5
        player.x = 110
        player.y = 105
        player.rect.x = 110
        player.rect.y = 105
        
        # No walls to collide with
        walls = []
        
        self.collision_system._resolve_player_wall_collision_proper(player, walls)
        
        # Player should remain at moved position
        self.assertEqual(player.x, 110)
        self.assertEqual(player.y, 105)

    # Test enemy collisions
    def test_enemy_wall_collision_horizontal(self):
        enemy = MockEnemy(100, 100)
        wall = pygame.Rect(120, 95, 50, 50)  # Wall to the right, overlapping
        
        self.collision_system._resolve_enemy_wall_collision(enemy, wall)
        
        # Enemy should be pushed to the left of the wall
        self.assertEqual(enemy.rect.right, wall.left)

    def test_enemy_wall_collision_vertical(self):
        enemy = MockEnemy(100, 100)
        wall = pygame.Rect(95, 120, 50, 50)  # Wall below, overlapping
        
        self.collision_system._resolve_enemy_wall_collision(enemy, wall)
        
        # Enemy should be pushed above the wall
        self.assertEqual(enemy.rect.bottom, wall.top)

    def test_enemy_enemy_collision(self):
        enemy1 = MockEnemy(100, 100)
        enemy2 = MockEnemy(105, 105)  # Overlapping position
        
        original_center1 = enemy1.rect.center
        original_center2 = enemy2.rect.center
        
        self.collision_system._resolve_enemy_enemy_collision(enemy1, enemy2)
        
        # Enemies should be pushed apart
        new_center1 = enemy1.rect.center
        new_center2 = enemy2.rect.center
        
        # Check that they moved apart (distance should increase)
        original_distance = ((original_center1[0] - original_center2[0])**2 + 
                           (original_center1[1] - original_center2[1])**2)**0.5
        new_distance = ((new_center1[0] - new_center2[0])**2 + 
                       (new_center1[1] - new_center2[1])**2)**0.5
        
        self.assertGreater(new_distance, original_distance)

    # Test entity collisions
    @patch('src.floating_texts.FloatingText')
    def test_player_enemy_collision(self, mock_floating_text):
        player = MockPlayer(100, 100)
        enemy = MockEnemy(100, 100)  # Same position
        floating_texts = []
        
        self.collision_system._handle_player_enemy_collision(player, enemy, floating_texts)
        
        # Player should take damage
        self.assertEqual(player.health, 90)  # 100 - 10 damage
        
        # Floating text should be created
        mock_floating_text.assert_called_once()

    @patch('src.floating_texts.FloatingText')
    def test_player_enemy_collision_invincible(self, mock_floating_text):
        player = MockPlayer(100, 100)
        player.is_invincible = True
        enemy = MockEnemy(100, 100)
        floating_texts = []
        
        self.collision_system._handle_player_enemy_collision(player, enemy, floating_texts)
        
        # Player should not take damage
        self.assertEqual(player.health, 100)
        
        # No floating text should be created
        mock_floating_text.assert_not_called()

    @patch('src.floating_texts.FloatingText')
    def test_bullet_enemy_collision(self, mock_floating_text):
        bullet = MockBullet(100, 100, damage=25)
        enemy = MockEnemy(100, 100)
        floating_texts = []
        
        damage_dealt = self.collision_system._handle_bullet_enemy_collision(bullet, enemy, floating_texts)
        
        # Enemy should take damage
        self.assertEqual(enemy.health, 25)  # 50 - 25 damage
        self.assertEqual(damage_dealt, 25)
        
        # Floating text should be created
        mock_floating_text.assert_called_once()

    @patch('src.coin.Coin')
    def test_enemy_death(self, mock_coin):
        enemy = MockEnemy(100, 100)
        enemies = [enemy]
        floating_texts = []
        coins = []
        
        self.collision_system._handle_enemy_death(enemy, enemies, floating_texts, coins)
        
        # Enemy should be removed from list
        self.assertNotIn(enemy, enemies)
        
        # Coin should be created
        mock_coin.assert_called_once()
        self.assertGreaterEqual(len(coins), 1)
        self.assertLessEqual(len(coins), 2) # could drop 2 items if a coin and a health drop both spawn

    # Test integrated collision handling
    @patch('src.floating_texts.FloatingText')
    @patch('src.coin.Coin')
    def test_handle_all_collisions(self, mock_coin, mock_floating_text):
        player = MockPlayer(100, 100)
        enemy = MockEnemy(200, 200)
        bullet = MockBullet(205, 205)  # Inside enemy rect (200-224, 200-224)
        
        enemies = [enemy]
        bullets = [bullet]
        floating_texts = []
        coins = []
        
        walls = [pygame.Rect(50, 50, 20, 20)]
        self.collision_system.update_walls(walls)
        
        self.collision_system.handle_all_collisions(player, enemies, bullets, floating_texts, coins)
        
        # Bullet should hit enemy and be removed
        self.assertNotIn(bullet, bullets)
        
        # Enemy should take damage
        self.assertEqual(enemy.health, 25)  # 50 - 25 damage


class TestGlobalCollisionFunctions(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        
        # Clear the global collision system
        collision_system.walls.clear()
        collision_system.temporary_walls.clear()
        collision_system.triggers.clear()

    def test_update_collision_walls(self):
        walls = [pygame.Rect(0, 0, 50, 50)]
        update_collision_walls(walls)
        
        self.assertEqual(collision_system.walls, walls)

    def test_clear_temporary_walls_global(self):
        collision_system.temporary_walls = [pygame.Rect(100, 100, 20, 20)]
        clear_temporary_walls()
        
        self.assertEqual(len(collision_system.temporary_walls), 0)

    def test_add_triggers_global(self):
        triggers = {"test": [pygame.Rect(50, 50, 30, 30)]}
        add_triggers(triggers)
        
        self.assertIn("test", collision_system.triggers)

    def test_clear_triggers_global(self):
        collision_system.triggers = {"test": [pygame.Rect(50, 50, 30, 30)]}
        clear_triggers()
        
        self.assertEqual(len(collision_system.triggers), 0)

    def test_is_in_trigger_global(self):
        player = MockPlayer(100, 100)
        trigger_rect = pygame.Rect(95, 95, 50, 50)
        collision_system.triggers = {"test_trigger": [trigger_rect]}
        
        result = is_in_trigger(player, "test_trigger")
        
        self.assertTrue(result)

    @patch('src.collision.collision_system.handle_all_collisions')
    def test_handle_all_collisions_global(self, mock_handle):
        player = MockPlayer(100, 100)
        enemies = []
        bullets = []
        
        handle_all_collisions(player, enemies, bullets)
        
        mock_handle.assert_called_once_with(player, enemies, bullets, None, None)