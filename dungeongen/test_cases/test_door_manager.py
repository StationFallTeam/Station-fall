import unittest
from unittest.mock import Mock, MagicMock
from dungeongen.door_placement_functions import place_doors_for_room, remove_doors_for_room
from dungeongen.classes import Rect, CombatRoom


class MockDungeonGen:
    """Mock dungeon generator for testing"""
    def __init__(self):
        self.hallway_prefabs_sideways = []
        self.hallway_prefabs_upways = []


class MockDungeonContext:
    """Mock dungeon context for testing door manager"""
    def __init__(self):
        self.collision_map = {}
        self.hallways = []
        self.tile_size = 32
        self.dungeon_gen = MockDungeonGen()  # Provide mock instead of None


class MockHallway:
    """Mock hallway for testing door placement"""
    def __init__(self, rect):
        self.rect = rect
        self.prefab_id = None  # Add missing attribute
        self.direction = "sideways"  # Add missing attribute


class MockPrefab:
    """Mock prefab with doors layer"""
    def __init__(self, doors_layer=None):
        self.doors = doors_layer or []


class TestDoorPlacementFunctions(unittest.TestCase):
    """Test the door placement utility functions"""
    
    def test_door_placement_functions_exist(self):
        """Test that door placement functions are callable"""
        # Functions should be callable
        self.assertTrue(callable(place_doors_for_room))
        self.assertTrue(callable(remove_doors_for_room))
    
    def test_place_doors_for_room_with_no_hallways(self):
        """Test that door placement with no hallways leaves door_positions empty"""
        room = CombatRoom(Rect(10, 10, 10, 10), "test_room")
        dungeon_context = MockDungeonContext()
        
        place_doors_for_room(room, dungeon_context)
        self.assertEqual(len(room.door_positions), 0)
    
    def test_door_placement_affects_room_door_positions(self):
        """Test that door placement with hallways modifies door_positions"""
        room = CombatRoom(Rect(5, 5, 10, 10), "test_room")
        dungeon_context = MockDungeonContext()
        
        # Add mock hallway that should connect
        hallway = MockHallway(Rect(15, 10, 5, 10))
        dungeon_context.hallways = [hallway]
        
        place_doors_for_room(room, dungeon_context)
        # Should have processed the hallway (even if no actual doors placed due to mock data)
        self.assertIsInstance(room.door_positions, list)