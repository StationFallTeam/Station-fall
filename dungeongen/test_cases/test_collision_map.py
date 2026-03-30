import unittest
from pathlib import Path

DUNGEONGEN_DIR = Path(__file__).resolve().parents[2] / "dungeongen"
DUNGEON_TYPES_DIR = DUNGEONGEN_DIR / "dungeon_types"

TEST_DUNGEON_TYPES = ("station_orange", "station_pink")

from dungeongen.config import (
    ALLOW_HALLWAY_THROUGH_ROOMS,
    BASE_ROOM_SIZE,
    BRANCH_FROM_SIDE_DECAY,
    BRANCH_FROM_SIDE_START_CHANCE,
    BRANCH_FROM_TOP_BOTTOM_DECAY,
    BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
    GENERATE_VERTICAL_FIRST,
    HALL_LENGTH,
    HALL_THICKNESS,
    ROOM_SIZE,
    SIDE_DECAY,
    SIDE_START_CHANCE,
    TOP_BOTTOM_DECAY,
    TOP_BOTTOM_START_CHANCE,
)
from dungeongen.generation import check_collision, check_rect_collision, generate_layout
from dungeongen.loading import (
    load_all_hallway_prefabs,
    load_all_hallway_wall_prefabs,
    load_main_room_prefabs,
    load_main_room_wall_prefabs,
    load_prefabs,
    load_wall_prefabs,
)


def _setup_collision_test():
    """Load assets and build a real collision map for collision tests."""
    dungeon_type = None
    for candidate in TEST_DUNGEON_TYPES:
        if (DUNGEON_TYPES_DIR / candidate).is_dir():
            dungeon_type = candidate
            break

    assert dungeon_type is not None, "No compatible dungeon type found for collision tests"

    base_path = str(DUNGEON_TYPES_DIR)
    prefabs = load_prefabs(dungeon_type, base_path=base_path)
    wall_prefabs = load_wall_prefabs(dungeon_type, base_path=base_path)
    main_room_prefabs = load_main_room_prefabs(dungeon_type, base_path=base_path)
    main_room_wall_prefabs = load_main_room_wall_prefabs(dungeon_type, base_path=base_path)
    hallway_prefabs = load_all_hallway_prefabs(dungeon_type, base_path=base_path)
    hallway_wall_prefabs = load_all_hallway_wall_prefabs(dungeon_type, base_path=base_path)

    tiles, rooms, hallways, collision_map = generate_layout(
        base_room_size=BASE_ROOM_SIZE,
        room_size=ROOM_SIZE,
        hall_length=HALL_LENGTH,
        hall_thickness=HALL_THICKNESS,
        seed=12345,
        prefabs=prefabs,
        wall_prefabs=wall_prefabs,
        main_room_prefabs=main_room_prefabs,
        main_room_wall_prefabs=main_room_wall_prefabs,
        hallway_prefabs_upways=hallway_prefabs["upways"],
        hallway_prefabs_sideways=hallway_prefabs["sideways"],
        hallway_wall_prefabs_sideways=hallway_wall_prefabs["sideways"],
        side_start_chance=SIDE_START_CHANCE,
        side_decay=SIDE_DECAY,
        branch_from_side_start_chance=BRANCH_FROM_SIDE_START_CHANCE,
        branch_from_side_decay=BRANCH_FROM_SIDE_DECAY,
        top_bottom_start_chance=TOP_BOTTOM_START_CHANCE,
        top_bottom_decay=TOP_BOTTOM_DECAY,
        branch_from_top_bottom_start_chance=BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
        branch_from_top_bottom_decay=BRANCH_FROM_TOP_BOTTOM_DECAY,
        generate_vertical_first=GENERATE_VERTICAL_FIRST,
        allow_hallway_through_rooms=ALLOW_HALLWAY_THROUGH_ROOMS,
    )

    return tiles, rooms, hallways, collision_map


class TestCollisionMap(unittest.TestCase):
    """Test collision map generation and functionality."""

    def test_collision_map_generation(self):
        """Test that collision data is stamped when real prefabs are loaded."""
        _, rooms, hallways, collision_map = _setup_collision_test()

        self.assertGreater(len(rooms), 0)
        self.assertGreater(len(hallways), 0)
        self.assertGreater(len(collision_map), 0)
        self.assertTrue(any(value == "." for value in collision_map.values()))
        self.assertTrue(any(value != "." for value in collision_map.values()))

    def test_collision_map_walkable(self):
        """Test that the base room center is walkable in the collision map."""
        _, rooms, _, collision_map = _setup_collision_test()

        base_room = next(room for room in rooms if room.is_base_room)
        center_x, center_y = base_room.center
        self.assertEqual(collision_map[(center_x, center_y)], ".")
        self.assertFalse(check_collision(collision_map, center_x, center_y))

    def test_collision_map_border_is_solid(self):
        """Test that generated border tiles are solid and collide."""
        _, _, _, collision_map = _setup_collision_test()

        border_tile = next((position for position, value in collision_map.items() if value == "#"), None)
        self.assertIsNotNone(border_tile)
        self.assertTrue(check_collision(collision_map, *border_tile))

    def test_rect_collision_check(self):
        """Test both walkable and solid rect collision checks."""
        _, rooms, _, collision_map = _setup_collision_test()

        base_room = next(room for room in rooms if room.is_base_room)
        center_x, center_y = base_room.center
        solid_x, solid_y = next(position for position, value in collision_map.items() if value == "#")

        self.assertFalse(check_rect_collision(collision_map, center_x, center_y, 1, 1, tile_size=1))
        self.assertTrue(check_rect_collision(collision_map, solid_x, solid_y, 1, 1, tile_size=1))
