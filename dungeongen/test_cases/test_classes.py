import unittest
from pathlib import Path
from dungeongen.classes import Rect, BaseRoom, HubRoom, CombatRoom, Hallway, DungeonGen, HubGen


class TestRect(unittest.TestCase):
    """Test the Rect class functionality"""
    
    def test_rect_creation(self):
        """Test Rect constructor and basic properties"""
        rect = Rect(10, 20, 30, 40)
        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)
        self.assertEqual(rect.w, 30)
        self.assertEqual(rect.h, 40)
    
    def test_rect_right_property(self):
        """Test the right property calculation"""
        rect = Rect(10, 20, 30, 40)
        self.assertEqual(rect.right, 39)  # x + w - 1
    
    def test_rect_bottom_property(self):
        """Test the bottom property calculation"""
        rect = Rect(10, 20, 30, 40)
        self.assertEqual(rect.bottom, 59)  # y + h - 1
    
    def test_rect_center_property(self):
        """Test the center property calculation"""
        rect = Rect(10, 20, 30, 40)
        center_x, center_y = rect.center
        self.assertEqual(center_x, 25)  # x + width/2
        self.assertEqual(center_y, 40)  # y + height/2


class TestBaseRoom(unittest.TestCase):
    """Test the BaseRoom abstract class"""
    
    def test_base_room_cannot_be_instantiated_directly(self):
        """Test that BaseRoom cannot be instantiated directly"""
        rect = Rect(0, 0, 10, 10)
        # BaseRoom is abstract, but we can test its functionality through subclasses
        hub_room = HubRoom(rect, "test")
        self.assertIsInstance(hub_room, BaseRoom)
        self.assertEqual(hub_room.rect, rect)
        self.assertEqual(hub_room.prefab_id, "test")


class TestHubRoom(unittest.TestCase):
    """Test the HubRoom class functionality"""
    
    def test_hub_room_creation(self):
        """Test HubRoom constructor and properties"""
        rect = Rect(0, 0, 15, 15)
        hub_room = HubRoom(rect, "hub_test")
        
        self.assertEqual(hub_room.rect, rect)
        self.assertEqual(hub_room.prefab_id, "hub_test")
        self.assertIsInstance(hub_room.trigger_areas, dict)
        self.assertEqual(len(hub_room.trigger_areas), 0)
    
    def test_hub_room_has_no_combat_attributes(self):
        """Test that HubRoom doesn't have combat-specific attributes"""
        rect = Rect(0, 0, 10, 10)
        hub_room = HubRoom(rect, "test")
        
        # Should have hub-specific attributes
        self.assertTrue(hasattr(hub_room, 'trigger_areas'))
        
        # Should NOT have combat-specific attributes
        self.assertFalse(hasattr(hub_room, 'locked'))
        self.assertFalse(hasattr(hub_room, 'enemies_spawned'))
        self.assertFalse(hasattr(hub_room, 'door_positions'))
        self.assertFalse(hasattr(hub_room, 'enemy_spawn_data'))
    
    def test_hub_room_center_property(self):
        """Test HubRoom center calculation through BaseRoom"""
        rect = Rect(5, 10, 20, 30)
        hub_room = HubRoom(rect, "center_test")
        center_x, center_y = hub_room.center
        self.assertEqual(center_x, 15)  # x + width/2
        self.assertEqual(center_y, 25)  # y + height/2


class TestCombatRoom(unittest.TestCase):
    """Test the CombatRoom class functionality"""
    
    def test_combat_room_creation(self):
        """Test CombatRoom constructor and default properties"""
        rect = Rect(5, 5, 20, 20)
        combat_room = CombatRoom(rect, "combat_test")
        
        self.assertEqual(combat_room.rect, rect)
        self.assertEqual(combat_room.prefab_id, "combat_test")
        self.assertEqual(combat_room.visited, False)
        self.assertEqual(combat_room.locked, False)
        self.assertIsInstance(combat_room.enemies_spawned, list)
        self.assertIsInstance(combat_room.door_positions, list)
        self.assertIsInstance(combat_room.enemy_spawn_data, list)
        self.assertEqual(combat_room.spawn_timer, 0)
        self.assertEqual(combat_room.unlock_timer, 0)
        self.assertFalse(combat_room.is_boss_room)
    
    def test_combat_room_has_no_hub_attributes(self):
        """Test that CombatRoom doesn't have hub-specific attributes"""
        rect = Rect(0, 0, 10, 10)
        combat_room = CombatRoom(rect, "test")
        
        # Should have combat-specific attributes
        self.assertTrue(hasattr(combat_room, 'locked'))
        self.assertTrue(hasattr(combat_room, 'enemies_spawned'))
        self.assertTrue(hasattr(combat_room, 'door_positions'))
        self.assertTrue(hasattr(combat_room, 'enemy_spawn_data'))
        
        # Should NOT have hub-specific attributes
        self.assertFalse(hasattr(combat_room, 'trigger_areas'))
    
    def test_combat_room_has_create_enemy_method(self):
        """Test that CombatRoom has the _create_enemy_by_type method"""
        rect = Rect(0, 0, 10, 10)
        combat_room = CombatRoom(rect, "test")
        self.assertTrue(hasattr(combat_room, '_create_enemy_by_type'))

    def test_boss_room_spawn_plan_uses_center_boss(self):
        rect = Rect(10, 20, 8, 8)
        combat_room = CombatRoom(rect, "test")
        combat_room.enemy_spawn_data = [("enemy", 1, 1)]
        combat_room.is_boss_room = True

        self.assertEqual(combat_room._get_spawn_plan(), [("boss", 4, 4)])


class TestHallway(unittest.TestCase):
    """Test the Hallway class functionality"""
    
    def test_hallway_creation(self):
        """Test Hallway constructor and properties"""
        rect = Rect(10, 10, 5, 20)
        hallway = Hallway(rect, "horizontal", "hall_prefab")
        
        self.assertEqual(hallway.rect, rect)
        self.assertEqual(hallway.direction, "horizontal")
        self.assertEqual(hallway.prefab_id, "hall_prefab")


class TestDungeonGen(unittest.TestCase):
    """Test the DungeonGen class functionality"""
    
    def test_dungeon_gen_creation(self):
        """Test DungeonGen constructor and initial state"""
        dungeon_gen = DungeonGen()
        
        # Check initial state
        self.assertEqual(dungeon_gen.loaded, False)
        self.assertEqual(dungeon_gen.generated, False)
        self.assertIsInstance(dungeon_gen.rooms, list)
        self.assertIsInstance(dungeon_gen.hallways, list)
        self.assertIsInstance(dungeon_gen.collision_map, dict)
        self.assertEqual(len(dungeon_gen.rooms), 0)
        self.assertEqual(len(dungeon_gen.hallways), 0)
    
    def test_dungeon_gen_has_load_complete_method(self):
        """Test that DungeonGen has the unified load_complete method"""
        dungeon_gen = DungeonGen()
        self.assertTrue(hasattr(dungeon_gen, 'load_complete'))

    def test_mark_boss_room_marks_farthest_combat_room(self):
        dungeon_gen = DungeonGen()
        near_room = CombatRoom(Rect(5, 5, 8, 8), "near")
        far_room = CombatRoom(Rect(30, 40, 8, 8), "far")
        dungeon_gen.rooms = [near_room, far_room]

        dungeon_gen._mark_boss_room()

        self.assertFalse(near_room.is_boss_room)
        self.assertTrue(far_room.is_boss_room)


class TestHubGen(unittest.TestCase):
    """Test the HubGen class functionality"""
    
    def test_hub_gen_creation(self):
        """Test HubGen constructor and initial state"""
        hub_gen = HubGen()
        
        # Check initial state
        self.assertEqual(hub_gen.loaded, False)
        self.assertEqual(hub_gen.generated, False)
        self.assertIsInstance(hub_gen.rooms, list)
        self.assertIsInstance(hub_gen.hallways, list)
        self.assertIsInstance(hub_gen.collision_map, dict)
        self.assertEqual(len(hub_gen.rooms), 0)
        self.assertEqual(len(hub_gen.hallways), 0)
    
    def test_hub_gen_has_load_complete_method(self):
        """Test that HubGen has the unified load_complete method"""
        hub_gen = HubGen()
        self.assertTrue(hasattr(hub_gen, 'load_complete'))
    
    def test_hub_gen_with_custom_path(self):
        """Test HubGen with custom hub path"""
        hub_gen = HubGen(hub_path="custom_hub")
        self.assertEqual(hub_gen.hub_path, "custom_hub")