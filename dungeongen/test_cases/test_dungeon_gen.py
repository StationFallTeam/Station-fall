import unittest
import tempfile
from pathlib import Path

DUNGEONGEN_DIR = Path(__file__).resolve().parents[1]
DUNGEON_TYPES_DIR = DUNGEONGEN_DIR / "dungeon_types"

TEST_DUNGEON_TYPES = ("station_orange", "station_pink")

from dungeongen.classes import Rect, Room
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
    MIN_BRANCH_CHANCE,
    ROOM_SIZE,
    SIDE_DECAY,
    SIDE_START_CHANCE,
    TOP_BOTTOM_DECAY,
    TOP_BOTTOM_START_CHANCE,
)
from dungeongen.generation import carve_rect, chance_at_depth, clamp_chance, generate_layout, room_overlaps
from dungeongen.loading import (
    find_presets,
    load_all_hallway_prefabs,
    load_all_hallway_wall_prefabs,
    load_main_room_prefabs,
    load_main_room_wall_prefabs,
    load_prefabs,
    load_preset,
    load_wall_prefabs,
)


def _default_layout_kwargs(seed: int = 12345, **overrides):
    kwargs = {
        "base_room_size": BASE_ROOM_SIZE,
        "room_size": ROOM_SIZE,
        "hall_length": HALL_LENGTH,
        "hall_thickness": HALL_THICKNESS,
        "side_start_chance": SIDE_START_CHANCE,
        "side_decay": SIDE_DECAY,
        "top_bottom_start_chance": TOP_BOTTOM_START_CHANCE,
        "top_bottom_decay": TOP_BOTTOM_DECAY,
        "branch_from_top_bottom_start_chance": BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
        "branch_from_top_bottom_decay": BRANCH_FROM_TOP_BOTTOM_DECAY,
        "branch_from_side_start_chance": BRANCH_FROM_SIDE_START_CHANCE,
        "branch_from_side_decay": BRANCH_FROM_SIDE_DECAY,
        "allow_hallway_through_rooms": ALLOW_HALLWAY_THROUGH_ROOMS,
        "generate_vertical_first": GENERATE_VERTICAL_FIRST,
        "seed": seed,
    }
    kwargs.update(overrides)
    return kwargs


def _serialize_layout(tiles, rooms, hallways):
    return (
        tuple(sorted(tiles.items())),
        tuple(
            (
                room.rect.x,
                room.rect.y,
                room.rect.w,
                room.rect.h,
                room.prefab_id,
                room.is_base_room,
                room.wall_prefab_id,
                tuple(sorted(room.doors)),
            )
            for room in rooms
        ),
        tuple(
            (
                hallway.rect.x,
                hallway.rect.y,
                hallway.rect.w,
                hallway.rect.h,
                hallway.direction,
                hallway.prefab_id,
                hallway.wall_prefab_id,
            )
            for hallway in hallways
        ),
    )


def _resolve_test_dungeon_type(preferred: str | None = None):
    candidates = []
    if preferred:
        candidates.append(preferred)
    candidates.extend(TEST_DUNGEON_TYPES)

    for dungeon_type in candidates:
        if (DUNGEON_TYPES_DIR / dungeon_type).is_dir():
            return dungeon_type

    raise AssertionError("No compatible dungeon type found for test assets")


def _load_station_assets(dungeon_type: str | None = None):
    dungeon_type = _resolve_test_dungeon_type(dungeon_type)
    base_path = str(DUNGEON_TYPES_DIR)
    hallway_prefabs = load_all_hallway_prefabs(dungeon_type, base_path=base_path)
    hallway_wall_prefabs = load_all_hallway_wall_prefabs(dungeon_type, base_path=base_path)
    return {
        "prefabs": load_prefabs(dungeon_type, base_path=base_path),
        "wall_prefabs": load_wall_prefabs(dungeon_type, base_path=base_path),
        "main_room_prefabs": load_main_room_prefabs(dungeon_type, base_path=base_path),
        "main_room_wall_prefabs": load_main_room_wall_prefabs(dungeon_type, base_path=base_path),
        "hallway_prefabs_upways": hallway_prefabs["upways"],
        "hallway_prefabs_sideways": hallway_prefabs["sideways"],
        "hallway_wall_prefabs_sideways": hallway_wall_prefabs["sideways"],
    }


class TestDungeonGen(unittest.TestCase):
    """Test dungeon generation functionality."""

    def test_load_valid_preset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_dir = Path(temp_dir) / "dungeon_gen_presets"
            preset_dir.mkdir()
            (preset_dir / "test_preset.txt").write_text(
                "SIDE_START_CHANCE = 1.0\n"
                "SIDE_DECAY = 0.125\n"
                "BRANCH_FROM_SIDE_START_CHANCE = 0.5\n",
                encoding="utf-8",
            )

            result = load_preset("test_preset.txt", directory=str(preset_dir))

            self.assertEqual(result["SIDE_START_CHANCE"], 1.0)
            self.assertEqual(result["SIDE_DECAY"], 0.125)
            self.assertEqual(result["BRANCH_FROM_SIDE_START_CHANCE"], 0.5)

    def test_load_preset_with_comments_and_empty_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_dir = Path(temp_dir) / "dungeon_gen_presets"
            preset_dir.mkdir()
            (preset_dir / "test_preset.txt").write_text(
                "# This is a comment\n"
                "SIDE_START_CHANCE = 1.0\n"
                "\n"
                "# Another comment\n"
                "SIDE_DECAY = 0.125\n"
                "\n",
                encoding="utf-8",
            )

            result = load_preset("test_preset.txt", directory=str(preset_dir))

            self.assertEqual(result, {
                "SIDE_START_CHANCE": 1.0,
                "SIDE_DECAY": 0.125,
            })

    def test_load_preset_with_booleans_and_integers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_dir = Path(temp_dir) / "dungeon_gen_presets"
            preset_dir.mkdir()
            (preset_dir / "test_preset.txt").write_text(
                "GENERATE_VERTICAL_FIRST = True\n"
                "ALLOW_HALLWAY_THROUGH_ROOMS = false\n"
                "MAX_BRANCHING_DEPTH = 100\n",
                encoding="utf-8",
            )

            result = load_preset("test_preset.txt", directory=str(preset_dir))

            self.assertTrue(result["GENERATE_VERTICAL_FIRST"] is True)
            self.assertTrue(result["ALLOW_HALLWAY_THROUGH_ROOMS"] is False)
            self.assertEqual(result["MAX_BRANCHING_DEPTH"], 100)
            self.assertIsInstance(result["MAX_BRANCHING_DEPTH"], int)

    def test_load_preset_nonexistent_file(self):
        result = load_preset("nonexistent.txt", directory="/tmp/does-not-exist")
        self.assertEqual(result, {})

    def test_find_presets_filters_and_sorts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_dir = Path(temp_dir) / "dungeon_gen_presets"
            preset_dir.mkdir()
            (preset_dir / "z_preset.txt").touch()
            (preset_dir / "a_preset.txt").touch()
            (preset_dir / "m_preset.txt").touch()
            (preset_dir / "README.txt").touch()
            (preset_dir / "gen_presets.txt").touch()
            (preset_dir / "other.py").touch()

            result = find_presets(directory=str(preset_dir))

            self.assertEqual(result, ["a_preset.txt", "m_preset.txt", "z_preset.txt"])

    def test_find_presets_empty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_dir = Path(temp_dir) / "dungeon_gen_presets"
            preset_dir.mkdir()
            result = find_presets(directory=str(preset_dir))
            self.assertEqual(result, [])

    def test_clamp_below_min(self):
        self.assertEqual(clamp_chance(-0.5), MIN_BRANCH_CHANCE)

    def test_clamp_above_max(self):
        self.assertEqual(clamp_chance(1.5), 1.0)

    def test_clamp_within_range(self):
        self.assertEqual(clamp_chance(0.5), 0.5)

    def test_clamp_at_boundaries(self):
        self.assertEqual(clamp_chance(MIN_BRANCH_CHANCE), MIN_BRANCH_CHANCE)
        self.assertEqual(clamp_chance(1.0), 1.0)

    def test_chance_at_depth_zero(self):
        self.assertEqual(chance_at_depth(1.0, 0.1, 0), 1.0)

    def test_chance_at_depth_decreases(self):
        depth0 = chance_at_depth(1.0, 0.1, 0)
        depth1 = chance_at_depth(1.0, 0.1, 1)
        depth2 = chance_at_depth(1.0, 0.1, 2)
        self.assertTrue(depth0 > depth1 > depth2)

    def test_chance_at_depth_with_decay(self):
        self.assertEqual(chance_at_depth(1.0, 0.1, 5), 0.5)

    def test_chance_at_depth_clamped(self):
        self.assertEqual(chance_at_depth(0.5, 0.2, 10), MIN_BRANCH_CHANCE)

    def test_rect_creation(self):
        rect = Rect(10, 20, 30, 40)
        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)
        self.assertEqual(rect.w, 30)
        self.assertEqual(rect.h, 40)

    def test_rect_right_property(self):
        self.assertEqual(Rect(10, 20, 30, 40).right, 39)

    def test_rect_bottom_property(self):
        self.assertEqual(Rect(10, 20, 30, 40).bottom, 59)

    def test_rect_center_property(self):
        self.assertEqual(Rect(0, 0, 10, 10).center, (5, 5))

    def test_room_creation(self):
        rect = Rect(0, 0, 10, 10)
        room = Room(rect, prefab_id=5, is_base_room=True)
        self.assertEqual(room.prefab_id, 5)
        self.assertEqual(room.rect, rect)
        self.assertTrue(room.is_base_room is True)
        self.assertIsNone(room.wall_prefab_id)
        self.assertEqual(room.doors, [])

    def test_room_center_property(self):
        self.assertEqual(Room(Rect(0, 0, 10, 10)).center, (5, 5))

    def test_no_overlap_empty_tiles(self):
        self.assertFalse(room_overlaps({}, Rect(0, 0, 5, 5)))

    def test_overlap_with_room(self):
        self.assertTrue(room_overlaps({(0, 0): ".", (1, 1): "."}, Rect(0, 0, 5, 5)))

    def test_no_overlap_with_hallway(self):
        self.assertFalse(room_overlaps({(0, 0): "h", (1, 1): "h"}, Rect(0, 0, 5, 5)))

    def test_overlap_partial(self):
        self.assertTrue(room_overlaps({(4, 4): "."}, Rect(0, 0, 5, 5)))

    def test_carve_basic(self):
        tiles = {}
        carve_rect(tiles, Rect(0, 0, 3, 3), ".")
        self.assertEqual(len(tiles), 9)
        self.assertTrue(all(value == "." for value in tiles.values()))

    def test_carve_hallway_skips_rooms(self):
        tiles = {(0, 0): ".", (1, 1): "."}
        carve_rect(tiles, Rect(0, 0, 3, 3), "h")
        self.assertEqual(tiles[(0, 0)], ".")
        self.assertEqual(tiles[(1, 1)], ".")

    def test_generate_layout_basic(self):
        tiles, rooms, hallways, collision_map = generate_layout(**_default_layout_kwargs(seed=42))

        self.assertIsInstance(tiles, dict)
        self.assertIsInstance(rooms, list)
        self.assertIsInstance(hallways, list)
        self.assertIsInstance(collision_map, dict)
        self.assertGreater(len(tiles), 0)
        self.assertGreater(len(rooms), 0)
        self.assertGreater(len(hallways), 0)

    def test_generate_layout_with_seed_reproducible(self):
        layout1 = generate_layout(**_default_layout_kwargs(seed=12345))
        layout2 = generate_layout(**_default_layout_kwargs(seed=12345))

        self.assertEqual(_serialize_layout(*layout1[:3]), _serialize_layout(*layout2[:3]))
        self.assertEqual(layout1[3], layout2[3])

    def test_generate_layout_different_seeds(self):
        layout1 = generate_layout(**_default_layout_kwargs(seed=111))
        layout2 = generate_layout(**_default_layout_kwargs(seed=222))

        self.assertNotEqual(_serialize_layout(*layout1[:3]), _serialize_layout(*layout2[:3]))

    def test_generate_layout_has_single_base_room(self):
        _, rooms, _, _ = generate_layout(**_default_layout_kwargs(seed=42))
        base_rooms = [room for room in rooms if room.is_base_room]
        self.assertEqual(len(base_rooms), 1)

    def test_generate_layout_vertical_first_toggle_changes_layout(self):
        layout1 = generate_layout(**_default_layout_kwargs(seed=42, generate_vertical_first=False))
        layout2 = generate_layout(**_default_layout_kwargs(seed=42, generate_vertical_first=True))

        self.assertNotEqual(_serialize_layout(*layout1[:3]), _serialize_layout(*layout2[:3]))

    def test_generate_layout_zero_chance_only_generates_base_room(self):
        tiles, rooms, hallways, collision_map = generate_layout(
            **_default_layout_kwargs(
                seed=42,
                side_start_chance=0.0,
                top_bottom_start_chance=0.0,
                branch_from_side_start_chance=0.0,
                branch_from_top_bottom_start_chance=0.0,
            )
        )

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(hallways), 0)
        self.assertEqual(len(tiles), BASE_ROOM_SIZE[0] * BASE_ROOM_SIZE[1])
        self.assertEqual(collision_map, {})

    def test_generate_layout_with_assets_builds_collision_map(self):
        assets = _load_station_assets()
        tiles, rooms, hallways, collision_map = generate_layout(
            **_default_layout_kwargs(seed=42, **assets)
        )

        self.assertTrue(assets["prefabs"])
        self.assertTrue(assets["main_room_prefabs"])
        self.assertTrue(assets["hallway_prefabs_upways"])
        self.assertTrue(assets["hallway_prefabs_sideways"])
        self.assertGreater(len(tiles), 0)
        self.assertGreater(len(rooms), 0)
        self.assertGreater(len(hallways), 0)
        self.assertGreater(len(collision_map), 0)
        self.assertTrue(any(room.prefab_id is not None for room in rooms))
        self.assertTrue(all(hallway.direction in {"upways", "sideways"} for hallway in hallways))

    def test_generate_layout_penetration_keeps_doors_on_room_edges(self):
        _, rooms, _, _ = generate_layout(
            **_default_layout_kwargs(seed=85, allow_hallway_through_rooms=True)
        )

        for room in rooms:
            for door_x, door_y in room.doors:
                on_room_bounds = room.rect.x <= door_x <= room.rect.right and room.rect.y <= door_y <= room.rect.bottom
                on_edge = (
                    door_x == room.rect.x
                    or door_x == room.rect.right
                    or door_y == room.rect.y
                    or door_y == room.rect.bottom
                )
                self.assertTrue(on_room_bounds and on_edge)

    def test_generate_layout_penetration_detects_hallway_room_contacts_as_doors(self):
        _, rooms, hallways, _ = generate_layout(
            **_default_layout_kwargs(seed=1774301974314605753, allow_hallway_through_rooms=True)
        )

        for hallway in hallways:
            for room in rooms:
                if hallway.direction == "sideways":
                    overlap_start = max(hallway.rect.y, room.rect.y)
                    overlap_end = min(hallway.rect.bottom, room.rect.bottom)
                    if overlap_start <= overlap_end:
                        door_y = (overlap_start + overlap_end) // 2
                        if hallway.rect.right == room.rect.x - 1:
                            self.assertIn((room.rect.x, door_y), room.doors)
                        if hallway.rect.x == room.rect.right + 1:
                            self.assertIn((room.rect.right, door_y), room.doors)

            if hallway.direction == "upways":
                overlap_start = max(hallway.rect.x, room.rect.x)
                overlap_end = min(hallway.rect.right, room.rect.right)
                if overlap_start <= overlap_end:
                    door_x = (overlap_start + overlap_end) // 2
                    if hallway.rect.bottom == room.rect.y - 1:
                        assert (door_x, room.rect.y) in room.doors
                    if hallway.rect.y == room.rect.bottom + 1:
                        assert (door_x, room.rect.bottom) in room.doors
