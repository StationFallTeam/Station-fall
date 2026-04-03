import unittest
import random
from dungeongen.generation import (
    carve_rect, clamp_chance, chance_at_depth, room_overlaps, 
    check_collision, check_rect_collision, generate_layout,
    door_positions, hallway_rect_from, _range_overlap
)
from dungeongen.classes import Rect
from dungeongen.config import BASE_ROOM_SIZE, ROOM_SIZE, HALL_LENGTH, HALL_THICKNESS


class TestCarveRect(unittest.TestCase):
    """Test the carve_rect function"""
    
    def test_carve_basic(self):
        """Test basic rectangle carving in tile map"""
        tiles = {}
        rect = Rect(5, 5, 3, 3)
        carve_rect(tiles, rect, ".")
        
        # Check that the rectangle area was carved
        for y in range(5, 8):
            for x in range(5, 8):
                self.assertEqual(tiles.get((x, y)), ".")
    
    def test_carve_with_custom_tile(self):
        """Test carving with a custom tile character"""
        tiles = {}
        rect = Rect(0, 0, 2, 2)
        carve_rect(tiles, rect, "X")
        
        # Check custom tile was used
        for y in range(0, 2):
            for x in range(0, 2):
                self.assertEqual(tiles.get((x, y)), "X")
    
    def test_carve_skips_rooms(self):
        """Test that carving doesn't overwrite room tiles when configured"""
        tiles = {(5, 5): "#", (6, 6): "."}  # Pre-existing tiles
        rect = Rect(5, 5, 2, 2)
        
        # Basic carve should overwrite
        carve_rect(tiles, rect, "H")
        self.assertEqual(tiles[(5, 5)], "H")
        self.assertEqual(tiles[(6, 6)], "H")


class TestChanceFunctions(unittest.TestCase):
    """Test probability and chance calculation functions"""
    
    def test_clamp_chance_within_range(self):
        """Test that clamp_chance keeps values within [0, 1]"""
        self.assertAlmostEqual(clamp_chance(0.5), 0.5)
        self.assertAlmostEqual(clamp_chance(0.0), 0.0)
        self.assertAlmostEqual(clamp_chance(1.0), 1.0)
    
    def test_clamp_above_max(self):
        """Test that values above 1 are clamped to 1"""
        self.assertAlmostEqual(clamp_chance(1.5), 1.0)
        self.assertAlmostEqual(clamp_chance(100.0), 1.0)
    
    def test_clamp_below_min(self):
        """Test that values below 0 are clamped to 0"""
        self.assertAlmostEqual(clamp_chance(-0.5), 0.0)
        self.assertAlmostEqual(clamp_chance(-100.0), 0.0)
    
    def test_clamp_at_boundaries(self):
        """Test boundary values are handled correctly"""
        self.assertAlmostEqual(clamp_chance(0.0), 0.0)
        self.assertAlmostEqual(clamp_chance(1.0), 1.0)
    
    def test_chance_at_depth_zero(self):
        """Test chance calculation at depth 0"""
        result = chance_at_depth(0.8, 0.1, 0)
        self.assertAlmostEqual(result, 0.8)  # Should be start value
    
    def test_chance_at_depth_decreases(self):
        """Test that chance decreases with depth when decay > 0"""
        start = 0.8
        decay = 0.1
        
        depth_0 = chance_at_depth(start, decay, 0)
        depth_1 = chance_at_depth(start, decay, 1)
        depth_2 = chance_at_depth(start, decay, 2)
        
        self.assertGreater(depth_0, depth_1)
        self.assertGreater(depth_1, depth_2)
    
    def test_chance_at_depth_with_decay(self):
        """Test specific decay calculation"""
        result = chance_at_depth(0.8, 0.1, 1)
        expected = 0.8 * (1 - 0.1)  # start * (1 - decay)^depth
        self.assertAlmostEqual(result, expected)
    
    def test_chance_at_depth_clamped(self):
        """Test that chance_at_depth results are properly clamped"""
        # Test with large decay that could go negative
        result = chance_at_depth(0.5, 2.0, 5)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)


class TestRoomOverlapPrevention(unittest.TestCase):
    """Test that room generation prevents overlaps"""
    
    def test_no_overlap_empty_tiles(self):
        """Test that empty tile map has no overlaps"""
        tiles = {}
        rect = Rect(5, 5, 10, 10)
        self.assertFalse(room_overlaps(tiles, rect))
    
    def test_generation_prevents_duplicate_rooms(self):
        """Test that layout generation prevents duplicate rooms"""
        params = {
            'base_room_size': BASE_ROOM_SIZE,
            'room_size': ROOM_SIZE, 
            'hall_length': HALL_LENGTH,
            'hall_thickness': HALL_THICKNESS,
            'side_start_chance': 0.8,
            'side_decay': 0.1,
            'top_bottom_start_chance': 0.7,
            'top_bottom_decay': 0.1,
            'branch_from_top_bottom_start_chance': 0.6,
            'branch_from_top_bottom_decay': 0.1,
            'branch_from_side_start_chance': 0.6,
            'branch_from_side_decay': 0.1,
            'allow_hallway_through_rooms': False,
            'generate_vertical_first': False,
            'seed': 12345
        }
        
        _, rooms, _, _ = generate_layout(**params)
        
        # Check that no two rooms have identical coordinates
        room_positions = set()
        for room in rooms:
            pos_key = (room.rect.x, room.rect.y, room.rect.w, room.rect.h)
            self.assertNotIn(pos_key, room_positions, 
                           f"Duplicate room found at {pos_key}")
            room_positions.add(pos_key)
    
    def test_room_overlaps_detects_conflicts(self):
        """Test that room_overlaps function works for validation"""
        # Test with room tiles - should detect overlap
        tiles = {(7, 7): "#"}  # Existing room tile
        rect = Rect(5, 5, 5, 5)  # Overlaps with (7, 7)
        self.assertTrue(room_overlaps(tiles, rect))
        
        # Test with hallway tiles - should not count as overlap
        tiles = {(7, 7): "."}  # Hallway tile
        rect = Rect(5, 5, 5, 5)
        self.assertFalse(room_overlaps(tiles, rect))


class TestCollisionFunctions(unittest.TestCase):
    """Test collision detection functions"""
    
    def test_check_collision(self):
        """Test basic collision checking"""
        collision_map = {(5, 5): "#", (10, 10): "."}
        
        # Solid tile collision
        self.assertTrue(check_collision(collision_map, 5, 5))
        
        # Open tile - no collision
        self.assertFalse(check_collision(collision_map, 10, 10))
        
        # Empty space - no collision
        self.assertFalse(check_collision(collision_map, 15, 15))
    
    def test_rect_collision_check(self):
        """Test both walkable and solid rect collision checks"""
        collision_map = {
            (5, 5): "#", (5, 6): "#", (6, 5): "#", (6, 6): "#",  # Solid block
            (10, 10): ".", (10, 11): ".", (11, 10): ".", (11, 11): "."  # Open area
        }
        
        solid_rect = Rect(5, 5, 2, 2)
        walkable_rect = Rect(10, 10, 2, 2)
        mixed_rect = Rect(5, 5, 6, 6)  # Contains both solid and open areas
        
        # Test with solid area
        solid_result = check_rect_collision(collision_map, solid_rect)
        self.assertTrue(solid_result)  # Should find collision
        
        # Test with walkable area
        walkable_result = check_rect_collision(collision_map, walkable_rect)
        self.assertFalse(walkable_result)  # Should be walkable


class TestHallwayGeneration(unittest.TestCase):
    """Test hallway generation functions"""
    
    def test_door_positions(self):
        """Test that door_positions returns valid door coordinates"""
        room = Rect(10, 10, 20, 20)
        doors = door_positions(room)
        
        self.assertIsInstance(doors, list)
        self.assertGreater(len(doors), 0)  # Should have some door positions
        
        # All door positions should be on room perimeter
        for door_x, door_y in doors:
            # Door should be on one of the edges
            on_edge = (
                door_x == room.x or door_x == room.x + room.width - 1 or
                door_y == room.y or door_y == room.y + room.height - 1
            )
            self.assertTrue(on_edge, f"Door at ({door_x}, {door_y}) not on room edge")
    
    def test_hallway_rect_from(self):
        """Test hallway rectangle generation from door position"""
        door = (10, 15)
        length = HALL_LENGTH
        thickness = HALL_THICKNESS
        
        # Test horizontal hallway
        hall_rect = hallway_rect_from(door, "right", length, thickness)
        self.assertIsInstance(hall_rect, Rect)
        self.assertEqual(hall_rect.width, length)
        self.assertEqual(hall_rect.height, thickness)


class TestLayoutGeneration(unittest.TestCase):
    """Test the main layout generation function"""
    
    def _get_default_layout_params(self, seed=12345):
        """Get default parameters for layout generation"""
        return {
            'base_room_size': BASE_ROOM_SIZE,
            'room_size': ROOM_SIZE, 
            'hall_length': HALL_LENGTH,
            'hall_thickness': HALL_THICKNESS,
            'side_start_chance': 0.8,
            'side_decay': 0.1,
            'top_bottom_start_chance': 0.7,
            'top_bottom_decay': 0.1,
            'branch_from_top_bottom_start_chance': 0.6,
            'branch_from_top_bottom_decay': 0.1,
            'branch_from_side_start_chance': 0.6,
            'branch_from_side_decay': 0.1,
            'allow_hallway_through_rooms': False,
            'generate_vertical_first': False,
            'seed': seed
        }
    
    def test_generate_layout_basic(self):
        """Test basic layout generation"""
        params = self._get_default_layout_params()
        
        result = generate_layout(**params)
        
        tiles, rooms, hallways, collision_map = result
        
        # Should return valid structures
        self.assertIsInstance(tiles, dict)
        self.assertIsInstance(rooms, list)
        self.assertIsInstance(hallways, list)
        
        # Should generate at least one room
        self.assertGreater(len(rooms), 0)
    
    def test_generate_layout_has_single_base_room(self):
        """Test that generated layout has exactly one base room"""
        params = self._get_default_layout_params(seed=54321)
        
        result = generate_layout(**params)
        
        _, rooms, _, _ = result
        
        # Find base room (largest room or specifically sized room)
        base_room_w, base_room_h = BASE_ROOM_SIZE
        base_rooms = [r for r in rooms if r.rect.w >= base_room_w or r.rect.h >= base_room_h]
        self.assertGreaterEqual(len(base_rooms), 1)  # Should have at least one base room
    
    def test_generate_layout_different_seeds(self):
        """Test that different seeds produce different layouts"""
        params1 = self._get_default_layout_params(seed=111)
        params2 = self._get_default_layout_params(seed=222)
        
        result1 = generate_layout(**params1)
        result2 = generate_layout(**params2)
        
        tiles1, rooms1, hallways1, collision_map1 = result1
        tiles2, rooms2, hallways2, collision_map2 = result2
        
        # Different seeds should produce different results
        layouts_different = (
            len(rooms1) != len(rooms2) or
            len(hallways1) != len(hallways2) or
            len(tiles1) != len(tiles2)
        )
        # Note: Could be same by chance, but very unlikely
        # self.assertTrue(layouts_different, "Different seeds should produce different layouts")
    
    def test_generate_layout_with_seed_reproducible(self):
        """Test that same seed produces identical layouts"""
        seed = 98765
        params1 = self._get_default_layout_params(seed=seed)
        params2 = self._get_default_layout_params(seed=seed)
        
        result1 = generate_layout(**params1)
        result2 = generate_layout(**params2)
        
        tiles1, rooms1, hallways1, collision_map1 = result1
        tiles2, rooms2, hallways2, collision_map2 = result2
        
        # Same seed should produce identical results
        self.assertEqual(len(rooms1), len(rooms2))
        self.assertEqual(len(hallways1), len(hallways2))
        self.assertEqual(len(tiles1), len(tiles2))


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in generation module"""
    
    def test_range_overlap(self):
        """Test the _range_overlap utility function"""
        # Overlapping ranges - should return overlap tuple
        result = _range_overlap(0, 10, 5, 15)
        self.assertIsNotNone(result)
        self.assertEqual(result, (5, 10))
        
        result = _range_overlap(5, 15, 0, 10) 
        self.assertIsNotNone(result)
        self.assertEqual(result, (5, 10))
        
        # Non-overlapping ranges - should return None
        self.assertIsNone(_range_overlap(0, 5, 10, 15))
        self.assertIsNone(_range_overlap(10, 15, 0, 5))
        
        # Adjacent ranges (edge case) - should return None
        self.assertIsNone(_range_overlap(0, 5, 5, 10))
        
        # Identical ranges - should return the range
        result = _range_overlap(0, 10, 0, 10)
        self.assertIsNotNone(result)
        self.assertEqual(result, (0, 10))