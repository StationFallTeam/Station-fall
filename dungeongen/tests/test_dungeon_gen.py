import sys
import tempfile
from pathlib import Path


DUNGEONGEN_DIR = Path(__file__).resolve().parents[1]
DUNGEON_TYPES_DIR = DUNGEONGEN_DIR / "dungeon_types"
sys.path.insert(0, str(DUNGEONGEN_DIR))

TEST_DUNGEON_TYPES = ("station_orange", "station_pink")

from classes import Rect, Room
from config import (
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
from generation import carve_rect, chance_at_depth, clamp_chance, generate_layout, room_overlaps
from loading import (
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


def test_load_valid_preset():
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

        assert result["SIDE_START_CHANCE"] == 1.0
        assert result["SIDE_DECAY"] == 0.125
        assert result["BRANCH_FROM_SIDE_START_CHANCE"] == 0.5


def test_load_preset_with_comments_and_empty_lines():
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

        assert result == {
            "SIDE_START_CHANCE": 1.0,
            "SIDE_DECAY": 0.125,
        }


def test_load_preset_with_booleans_and_integers():
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

        assert result["GENERATE_VERTICAL_FIRST"] is True
        assert result["ALLOW_HALLWAY_THROUGH_ROOMS"] is False
        assert result["MAX_BRANCHING_DEPTH"] == 100
        assert isinstance(result["MAX_BRANCHING_DEPTH"], int)


def test_load_preset_nonexistent_file():
    result = load_preset("nonexistent.txt", directory="/tmp/does-not-exist")
    assert result == {}


def test_find_presets_filters_and_sorts():
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

        assert result == ["a_preset.txt", "m_preset.txt", "z_preset.txt"]


def test_find_presets_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        preset_dir = Path(temp_dir) / "dungeon_gen_presets"
        preset_dir.mkdir()
        result = find_presets(directory=str(preset_dir))
        assert result == []


def test_clamp_below_min():
    assert clamp_chance(-0.5) == MIN_BRANCH_CHANCE


def test_clamp_above_max():
    assert clamp_chance(1.5) == 1.0


def test_clamp_within_range():
    assert clamp_chance(0.5) == 0.5


def test_clamp_at_boundaries():
    assert clamp_chance(MIN_BRANCH_CHANCE) == MIN_BRANCH_CHANCE
    assert clamp_chance(1.0) == 1.0


def test_chance_at_depth_zero():
    assert chance_at_depth(1.0, 0.1, 0) == 1.0


def test_chance_at_depth_decreases():
    depth0 = chance_at_depth(1.0, 0.1, 0)
    depth1 = chance_at_depth(1.0, 0.1, 1)
    depth2 = chance_at_depth(1.0, 0.1, 2)
    assert depth0 > depth1 > depth2


def test_chance_at_depth_with_decay():
    assert chance_at_depth(1.0, 0.1, 5) == 0.5


def test_chance_at_depth_clamped():
    assert chance_at_depth(0.5, 0.2, 10) == MIN_BRANCH_CHANCE


def test_rect_creation():
    rect = Rect(10, 20, 30, 40)
    assert rect.x == 10
    assert rect.y == 20
    assert rect.w == 30
    assert rect.h == 40


def test_rect_right_property():
    assert Rect(10, 20, 30, 40).right == 39


def test_rect_bottom_property():
    assert Rect(10, 20, 30, 40).bottom == 59


def test_rect_center_property():
    assert Rect(0, 0, 10, 10).center == (5, 5)


def test_room_creation():
    rect = Rect(0, 0, 10, 10)
    room = Room(rect, prefab_id=5, is_base_room=True)
    assert room.prefab_id == 5
    assert room.rect == rect
    assert room.is_base_room is True
    assert room.wall_prefab_id is None
    assert room.doors == []


def test_room_center_property():
    assert Room(Rect(0, 0, 10, 10)).center == (5, 5)


def test_no_overlap_empty_tiles():
    assert not room_overlaps({}, Rect(0, 0, 5, 5))


def test_overlap_with_room():
    assert room_overlaps({(0, 0): ".", (1, 1): "."}, Rect(0, 0, 5, 5))


def test_no_overlap_with_hallway():
    assert not room_overlaps({(0, 0): "h", (1, 1): "h"}, Rect(0, 0, 5, 5))


def test_overlap_partial():
    assert room_overlaps({(4, 4): "."}, Rect(0, 0, 5, 5))


def test_carve_basic():
    tiles = {}
    carve_rect(tiles, Rect(0, 0, 3, 3), ".")
    assert len(tiles) == 9
    assert all(value == "." for value in tiles.values())


def test_carve_hallway_skips_rooms():
    tiles = {(0, 0): ".", (1, 1): "."}
    carve_rect(tiles, Rect(0, 0, 3, 3), "h")
    assert tiles[(0, 0)] == "."
    assert tiles[(1, 1)] == "."


def test_generate_layout_basic():
    tiles, rooms, hallways, collision_map = generate_layout(**_default_layout_kwargs(seed=42))

    assert isinstance(tiles, dict)
    assert isinstance(rooms, list)
    assert isinstance(hallways, list)
    assert isinstance(collision_map, dict)
    assert len(tiles) > 0
    assert len(rooms) > 0
    assert len(hallways) > 0


def test_generate_layout_with_seed_reproducible():
    layout1 = generate_layout(**_default_layout_kwargs(seed=12345))
    layout2 = generate_layout(**_default_layout_kwargs(seed=12345))

    assert _serialize_layout(*layout1[:3]) == _serialize_layout(*layout2[:3])
    assert layout1[3] == layout2[3]


def test_generate_layout_different_seeds():
    layout1 = generate_layout(**_default_layout_kwargs(seed=111))
    layout2 = generate_layout(**_default_layout_kwargs(seed=222))

    assert _serialize_layout(*layout1[:3]) != _serialize_layout(*layout2[:3])


def test_generate_layout_has_single_base_room():
    _, rooms, _, _ = generate_layout(**_default_layout_kwargs(seed=42))
    base_rooms = [room for room in rooms if room.is_base_room]
    assert len(base_rooms) == 1


def test_generate_layout_vertical_first_toggle_changes_layout():
    layout1 = generate_layout(**_default_layout_kwargs(seed=42, generate_vertical_first=False))
    layout2 = generate_layout(**_default_layout_kwargs(seed=42, generate_vertical_first=True))

    assert _serialize_layout(*layout1[:3]) != _serialize_layout(*layout2[:3])


def test_generate_layout_zero_chance_only_generates_base_room():
    tiles, rooms, hallways, collision_map = generate_layout(
        **_default_layout_kwargs(
            seed=42,
            side_start_chance=0.0,
            top_bottom_start_chance=0.0,
            branch_from_side_start_chance=0.0,
            branch_from_top_bottom_start_chance=0.0,
        )
    )

    assert len(rooms) == 1
    assert len(hallways) == 0
    assert len(tiles) == BASE_ROOM_SIZE[0] * BASE_ROOM_SIZE[1]
    assert collision_map == {}


def test_generate_layout_with_assets_builds_collision_map():
    assets = _load_station_assets()
    tiles, rooms, hallways, collision_map = generate_layout(
        **_default_layout_kwargs(seed=42, **assets)
    )

    assert assets["prefabs"]
    assert assets["main_room_prefabs"]
    assert assets["hallway_prefabs_upways"]
    assert assets["hallway_prefabs_sideways"]
    assert len(tiles) > 0
    assert len(rooms) > 0
    assert len(hallways) > 0
    assert len(collision_map) > 0
    assert any(room.prefab_id is not None for room in rooms)
    assert all(hallway.direction in {"upways", "sideways"} for hallway in hallways)


def test_generate_layout_penetration_keeps_doors_on_room_edges():
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
            assert on_room_bounds and on_edge


def test_generate_layout_penetration_detects_hallway_room_contacts_as_doors():
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
                        assert (room.rect.x, door_y) in room.doors
                    if hallway.rect.x == room.rect.right + 1:
                        assert (room.rect.right, door_y) in room.doors

            if hallway.direction == "upways":
                overlap_start = max(hallway.rect.x, room.rect.x)
                overlap_end = min(hallway.rect.right, room.rect.right)
                if overlap_start <= overlap_end:
                    door_x = (overlap_start + overlap_end) // 2
                    if hallway.rect.bottom == room.rect.y - 1:
                        assert (door_x, room.rect.y) in room.doors
                    if hallway.rect.y == room.rect.bottom + 1:
                        assert (door_x, room.rect.bottom) in room.doors


def main():
    print("Running tests...")
    print()

    tests = sorted(
        [value for name, value in globals().items() if name.startswith("test_") and callable(value)],
        key=lambda test_func: test_func.__name__,
    )

    for test_func in tests:
        test_func()
        print(test_func.__name__)

    print()
    print("All tests passed!")


if __name__ == '__main__':
    main()
