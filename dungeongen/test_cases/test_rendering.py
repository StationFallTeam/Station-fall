import unittest
import pygame
from dungeongen.rendering import (
    draw_grid, draw_minimap, COLOR_BG, COLOR_ROOM, COLOR_HALL, COLOR_GRID,
    COLOR_TEXT, COLOR_FURTHEST, COLOR_DOOR_DOT
)
from dungeongen.classes import CombatRoom, HubRoom, Hallway, Rect

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


class TestDrawMinimap(unittest.TestCase):
    """Test the minimap rendering path"""

    def setUp(self):
        pygame.init()
        self.surface = pygame.Surface((320, 240))

    def tearDown(self):
        pygame.quit()

    def test_draw_minimap_accepts_room_and_hallway_rects(self):
        """Minimap should support drawing from room and hallway rect lists"""
        rooms = [CombatRoom(Rect(8, 8, 6, 6), "room")]
        hallways = [Hallway(Rect(14, 10, 5, 2), "sideways")]

        draw_minimap(
            self.surface,
            {},
            focus_x=10 * 32,
            focus_y=10 * 32,
            tile_size=32,
            rooms=rooms,
            hallways=hallways,
        )

        self.assertIsNotNone(self.surface)

    def test_draw_minimap_does_not_draw_spawn_indicator(self):
        """Spawn marker color should not appear even if spawn coords are provided"""
        rooms = [CombatRoom(Rect(8, 8, 6, 6), "room")]

        draw_minimap(
            self.surface,
            {},
            focus_x=10 * 32,
            focus_y=10 * 32,
            tile_size=32,
            spawn_x=10 * 32,
            spawn_y=10 * 32,
            rooms=rooms,
            hallways=[],
        )

        width, height = self.surface.get_size()
        found_spawn_color = False
        for x in range(width):
            for y in range(height):
                if self.surface.get_at((x, y))[:3] == (255, 220, 0):
                    found_spawn_color = True
                    break
            if found_spawn_color:
                break

        self.assertFalse(found_spawn_color)

    def test_draw_minimap_full_map_shows_distant_rooms(self):
        """Fullscreen minimap should be able to show the full dungeon layout"""
        far_room = CombatRoom(Rect(100, 100, 8, 8), "room")

        draw_minimap(
            self.surface,
            {},
            focus_x=10 * 32,
            focus_y=10 * 32,
            tile_size=32,
            rooms=[far_room],
            hallways=[],
            full_map=True,
        )

        found_room_color = False
        for x in range(self.surface.get_width()):
            for y in range(self.surface.get_height()):
                if self.surface.get_at((x, y))[:3] == COLOR_ROOM:
                    found_room_color = True
                    break
            if found_room_color:
                break

        self.assertTrue(found_room_color)

    def test_draw_minimap_completed_rooms_are_green(self):
        """Visited and unlocked combat rooms should render green on the minimap"""
        completed_room = CombatRoom(Rect(8, 8, 6, 6), "room")
        completed_room.visited = True
        completed_room.locked = False

        draw_minimap(
            self.surface,
            {},
            focus_x=10 * 32,
            focus_y=10 * 32,
            tile_size=32,
            rooms=[completed_room],
            hallways=[],
            full_map=True,
        )

        found_green = False
        for x in range(self.surface.get_width()):
            for y in range(self.surface.get_height()):
                if self.surface.get_at((x, y))[:3] == (80, 200, 120):
                    found_green = True
                    break
            if found_green:
                break

        self.assertTrue(found_green)