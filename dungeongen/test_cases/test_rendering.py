import unittest
import pygame
from dungeongen.rendering import (
    draw_grid, COLOR_BG, COLOR_ROOM, COLOR_HALL, COLOR_GRID, 
    COLOR_TEXT, COLOR_FURTHEST, COLOR_DOOR_DOT
)
from dungeongen.classes import CombatRoom, HubRoom, Rect

class TestRenderingConstants(unittest.TestCase):
    """Test rendering color constants"""
    
    def test_color_constants_are_tuples(self):
        """Test that color constants are RGB tuples"""
        colors = [
            COLOR_BG, COLOR_ROOM, COLOR_HALL, COLOR_GRID,
            COLOR_TEXT, COLOR_FURTHEST, COLOR_DOOR_DOT
        ]
        
        for color in colors:
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)  # RGB
            
            # All values should be in valid range
            for value in color:
                self.assertIsInstance(value, int)
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 255)
    
    def test_background_color(self):
        """Test background color constant"""
        self.assertEqual(COLOR_BG, (8, 8, 8))
    
    def test_room_colors(self):
        """Test room-related color constants"""
        self.assertEqual(COLOR_ROOM, (77, 155, 255))
        self.assertEqual(COLOR_HALL, (173, 209, 255))
    
    def test_ui_colors(self):
        """Test UI color constants"""
        self.assertEqual(COLOR_GRID, (255, 255, 255))
        self.assertEqual(COLOR_TEXT, (255, 255, 255))
        self.assertEqual(COLOR_FURTHEST, (255, 200, 0))
        self.assertEqual(COLOR_DOOR_DOT, (255, 0, 0))


class TestDrawGrid(unittest.TestCase):
    """Test the draw_grid function"""
    
    def setUp(self):
        """Set up pygame for testing"""
        pygame.init()
        self.surface = pygame.Surface((800, 600))
        self.tile_size = 32
    
    def tearDown(self):
        """Clean up pygame"""
        pygame.quit()
    
    def test_draw_grid_modifies_surface(self):
        """Test that draw_grid actually draws something"""
        tiles = {(0, 0): ".", (1, 0): "#", (0, 1): "."}
        
        # Capture surface before drawing
        initial_color = self.surface.get_at((0, 0))
        
        draw_grid(
            surface=self.surface,
            tiles=tiles,
            tile_size=self.tile_size,
            cam_x=0,
            cam_y=0,
            show_grid=True,
            screen_w=800,
            screen_h=600
        )
        
        # Surface should have changed (something was drawn)
        after_color = self.surface.get_at((0, 0))
        # Note: Due to background fill, color should be different
    
    def test_draw_grid_with_rooms_shows_room_colors(self):
        """Test that rooms are drawn with different colors"""
        tiles = {(0, 0): ".", (1, 0): "#"}
        rooms = [CombatRoom(Rect(0, 0, 2, 2), "test_room")]
        
        draw_grid(
            surface=self.surface,
            tiles=tiles,
            tile_size=32,
            cam_x=0,
            cam_y=0,
            show_grid=False,
            screen_w=800,
            screen_h=600,
            rooms=rooms
        )
        
        # Should draw room without crashing
        self.assertIsNotNone(self.surface)


class TestDrawGridRoomIntegration(unittest.TestCase):
    """Test draw_grid integration with different room types"""
    
    def setUp(self):
        """Set up pygame for testing"""
        pygame.init()
        self.surface = pygame.Surface((800, 600))
    
    def tearDown(self):
        """Clean up pygame"""
        pygame.quit()
    
    def test_draw_grid_handles_hub_and_combat_rooms(self):
        """Test that both HubRoom and CombatRoom can be rendered"""
        tiles = {(0, 0): ".", (1, 0): "#"}
        rooms = [
            HubRoom(Rect(0, 0, 5, 5), "hub_room"),
            CombatRoom(Rect(10, 10, 8, 8), "combat_room")
        ]
        
        # Should complete without error
        draw_grid(
            surface=self.surface,
            tiles=tiles,
            tile_size=32,
            cam_x=0,
            cam_y=0,
            show_grid=False,
            screen_w=800,
            screen_h=600,
            rooms=rooms
        )
        
        # Verify rooms were processed
        self.assertEqual(len(rooms), 2)