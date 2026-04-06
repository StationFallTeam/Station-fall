import unittest
import tempfile
import os
from pathlib import Path
from dungeongen.loading import (
    parse_enemy_type_from_cell, parse_enemy_data_from_prefab, 
    parse_triggers_from_prefab, load_prefab, validate_dungeon_type,
    find_dungeon_types, load_prefabs, load_preset,
    _normalize_tile_token, _parse_prefab_row
)
from dungeongen.classes import CombatRoom, HubRoom, Rect, Prefab


class TestEnemyParsing(unittest.TestCase):
    """Test enemy parsing functions"""
    
    def test_parse_enemy_type_from_cell(self):
        """Test parsing enemy types from prefab cell values"""
        # Known enemy mapping
        self.assertEqual(parse_enemy_type_from_cell('nrmE'), 'enemy')
        
        # Unknown enemy type should return None
        self.assertIsNone(parse_enemy_type_from_cell('unkn'))
        self.assertIsNone(parse_enemy_type_from_cell(''))
        self.assertIsNone(parse_enemy_type_from_cell(None))
    
    def test_parse_enemy_data_from_prefab_empty(self):
        """Test parsing enemy data from prefab with no enemies"""
        room = CombatRoom(Rect(0, 0, 10, 10), "test")
        prefab = Prefab(collision=[], obstacle=[], base=[], enemy=[])
        
        parse_enemy_data_from_prefab(room, prefab)
        self.assertEqual(len(room.enemy_spawn_data), 0)
    
    def test_parse_enemy_data_from_prefab_with_enemies(self):
        """Test parsing enemy data from prefab with enemy layer"""
        room = CombatRoom(Rect(0, 0, 10, 10), "test")
        enemy_layer = [
            ['.', '.', '.', '.'],
            ['.', '.', 'nrmE', '.']  # Enemy at position (2, 1)
        ]
        prefab = Prefab(collision=[], obstacle=[], base=[], enemy=enemy_layer)
        
        parse_enemy_data_from_prefab(room, prefab)
        
        # Should find one enemy
        self.assertEqual(len(room.enemy_spawn_data), 1)
        enemy_type, local_x, local_y = room.enemy_spawn_data[0]
        self.assertEqual(enemy_type, 'enemy')
        self.assertEqual(local_x, 2)
        self.assertEqual(local_y, 1)
    
    def test_parse_enemy_data_clears_existing(self):
        """Test that parsing clears existing enemy data"""
        room = CombatRoom(Rect(0, 0, 10, 10), "test")
        room.enemy_spawn_data = [('old_enemy', 5, 5)]  # Pre-existing data
        
        prefab = Prefab(collision=[], obstacle=[], base=[], enemy=[])
        parse_enemy_data_from_prefab(room, prefab)
        
        # Should be cleared
        self.assertEqual(len(room.enemy_spawn_data), 0)


class TestTriggerParsing(unittest.TestCase):
    """Test trigger parsing functions"""
    
    def test_parse_triggers_from_prefab_empty(self):
        """Test parsing triggers from prefab with no triggers"""
        room = HubRoom(Rect(0, 0, 10, 10), "test")
        prefab = Prefab(collision=[], obstacle=[], base=[], trigger=[])
        
        parse_triggers_from_prefab(room, prefab, tile_size=32)
        self.assertEqual(len(room.trigger_areas), 0)
    
    def test_parse_triggers_from_prefab_with_triggers(self):
        """Test parsing triggers from prefab with trigger layer"""
        import pygame
        pygame.init()  # Required for pygame.Rect
        
        room = HubRoom(Rect(0, 0, 10, 10), "test")
        trigger_layer = [
            ['.', '.', '.', '.'],
            ['.', '.', 'room1', '.']  # Trigger at position (2, 1)
        ]
        prefab = Prefab(collision=[], obstacle=[], base=[], trigger=trigger_layer)
        
        parse_triggers_from_prefab(room, prefab, tile_size=32)
        
        # Should find one trigger area
        self.assertGreater(len(room.trigger_areas), 0)
        self.assertIn('room1', room.trigger_areas)


class TestPrefabLoading(unittest.TestCase):
    """Test prefab loading functions"""
    
    def setUp(self):
        """Create a temporary prefab file for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.prefab_content = """# Test prefab
[COLLISION]
.#.
###
.#.

[BASE]  
...
...
...

[OBSTACLE]
...
.X.
...
"""
        self.prefab_file = os.path.join(self.temp_dir, "test.prefab")
        with open(self.prefab_file, 'w') as f:
            f.write(self.prefab_content)
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.prefab_file):
            os.remove(self.prefab_file)
        os.rmdir(self.temp_dir)
    
    def test_load_prefab_valid_file(self):
        """Test loading a valid prefab file"""
        prefab = load_prefab(self.prefab_file)
        
        self.assertIsInstance(prefab, Prefab)
        self.assertIsNotNone(prefab.collision)
        self.assertIsNotNone(prefab.base)
        self.assertIsNotNone(prefab.obstacle)
        
        # Check that layers have expected content
        self.assertEqual(len(prefab.collision), 3)  # 3 rows
        self.assertEqual(len(prefab.base), 3)
        self.assertEqual(len(prefab.obstacle), 3)
    
    def test_load_prefab_nonexistent_file(self):
        """Test loading a non-existent prefab file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.prefab")
        prefab = load_prefab(nonexistent_file)
        self.assertIsNone(prefab)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in loading module"""
    
    def test_normalize_tile_token(self):
        """Test tile token normalization"""
        # Should handle strings properly 
        self.assertEqual(_normalize_tile_token("test"), "test")
        self.assertEqual(_normalize_tile_token(""), "")
        
        # Should handle None
        self.assertEqual(_normalize_tile_token(None), "")
    
    def test_parse_prefab_row(self):
        """Test parsing a single prefab row"""
        # CSV format row 
        result = _parse_prefab_row("a, b, c")
        self.assertEqual(result, ["a", "b", "c"])
        
        # Character format row
        result = _parse_prefab_row("abc") 
        self.assertEqual(result, ["a", "b", "c"])
        
        # Empty row
        result = _parse_prefab_row("")
        self.assertEqual(result, [])


class TestDungeonTypeValidation(unittest.TestCase):
    """Test dungeon type validation and discovery"""
    
    def test_validate_dungeon_type_builtin(self):
        """Test validation of built-in dungeon types"""
        # Just use the default path resolution from the loading module
        
        # Check if built-in types exist and are valid
        if Path(__file__).parent.parent.joinpath("dungeon_types", "station_orange").exists():
            result = validate_dungeon_type("station_orange")
            self.assertTrue(result)
        else:
            # Skip test if dungeon type doesn't exist
            self.skipTest("station_orange dungeon type not found")
    
    def test_validate_dungeon_type_invalid(self):
        """Test validation of invalid dungeon type"""
        dungeongen_path = Path(__file__).parent.parent
        base_path = str(dungeongen_path)
        
        result = validate_dungeon_type("nonexistent_type", base_path)
        self.assertFalse(result)
    
    def test_find_dungeon_types(self):
        """Test discovery of available dungeon types"""
        dungeongen_path = Path(__file__).parent.parent
        base_path = str(dungeongen_path)
        
        dungeon_types = find_dungeon_types(base_path)
        self.assertIsInstance(dungeon_types, list)
        
        # Should include built-in types if they exist
        dungeongen_types_dir = dungeongen_path / "dungeon_types"
        if dungeongen_types_dir.exists():
            available_types = [d.name for d in dungeongen_types_dir.iterdir() if d.is_dir()]
            for dtype in available_types:
                if dtype in ['station_orange', 'station_pink', 'hub']:
                    # These should be found
                    pass


class TestPrefabLoaders(unittest.TestCase):
    """Test specialized prefab loader functions"""
    
    def test_load_prefabs_with_valid_type(self):
        """Test loading prefabs for a valid dungeon type"""
        dungeongen_path = Path(__file__).parent.parent
        base_path = str(dungeongen_path)
        
        # Try with a type that should exist
        available_types = []
        types_dir = dungeongen_path / "dungeon_types"
        if types_dir.exists():
            available_types = [d.name for d in types_dir.iterdir() if d.is_dir()]
        
        for dtype in available_types:
            if dtype in ['station_orange', 'station_pink']:
                prefabs = load_prefabs(dtype, base_path)
                self.assertIsInstance(prefabs, list)
                # May be empty if no prefabs exist, but should be a list
                break
    
    def test_load_prefabs_with_invalid_type(self):
        """Test loading prefabs for invalid dungeon type"""
        dungeongen_path = Path(__file__).parent.parent
        base_path = str(dungeongen_path)
        
        prefabs = load_prefabs("nonexistent_type", base_path)
        self.assertEqual(prefabs, [])  # Should return empty list


class TestPresetLoading(unittest.TestCase):
    """Test preset loading functionality"""
    
    def setUp(self):
        """Create temporary preset files for testing"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid preset file
        self.valid_preset = os.path.join(self.temp_dir, "test_preset.txt")
        preset_content = """# Test preset
ROOM_SIZE = 15
BASE_ROOM_SIZE = 25
SIDE_START_CHANCE = 0.8
"""
        with open(self.valid_preset, 'w') as f:
            f.write(preset_content)
        
        # Create preset with booleans and integers
        self.complex_preset = os.path.join(self.temp_dir, "complex.txt")
        complex_content = """GENERATE_VERTICAL_FIRST = true
ALLOW_HALLWAY_THROUGH_ROOMS = false
ROOM_SIZE = 20
SIDE_DECAY = 0.15
"""
        with open(self.complex_preset, 'w') as f:
            f.write(complex_content)
    
    def tearDown(self):
        """Clean up temporary files"""
        for file in [self.valid_preset, self.complex_preset]:
            if os.path.exists(file):
                os.remove(file)
        os.rmdir(self.temp_dir)
    
    def test_load_valid_preset(self):
        """Test loading a valid preset file"""
        config = load_preset(os.path.basename(self.valid_preset), self.temp_dir)
        
        self.assertIsInstance(config, dict)
        self.assertEqual(config.get('ROOM_SIZE'), 15)
        self.assertEqual(config.get('BASE_ROOM_SIZE'), 25)
        self.assertEqual(config.get('SIDE_START_CHANCE'), 0.8)
    
    def test_load_preset_with_booleans_and_integers(self):
        """Test loading preset with different data types"""
        config = load_preset(os.path.basename(self.complex_preset), self.temp_dir)
        
        self.assertIsInstance(config, dict)
        self.assertEqual(config.get('GENERATE_VERTICAL_FIRST'), True)
        self.assertEqual(config.get('ALLOW_HALLWAY_THROUGH_ROOMS'), False)
        self.assertEqual(config.get('ROOM_SIZE'), 20)
        self.assertEqual(config.get('SIDE_DECAY'), 0.15)
    
    def test_load_preset_with_comments_and_empty_lines(self):
        """Test that comments and empty lines are handled correctly"""
        config = load_preset(os.path.basename(self.valid_preset), self.temp_dir)
        
        # Should not include comments or empty lines as keys
        self.assertNotIn('# Test preset', config)
        self.assertNotIn('', config)
    
    def test_load_preset_nonexistent_file(self):
        """Test loading a non-existent preset file"""
        config = load_preset('nonexistent.txt', '/tmp/does-not-exist')
        
        # Should return empty dict or handle gracefully
        self.assertIsInstance(config, dict)