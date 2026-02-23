import tempfile
import os
from pathlib import Path
import dungeon_gen


def test_load_valid_preset():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        preset_content = """SIDE_START_CHANCE = 1.0
SIDE_DECAY = 0.125
BRANCH_FROM_SIDE_START_CHANCE = 0.5"""
        with open("test_preset.txt", "w") as f:
            f.write(preset_content)
        result = dungeon_gen.load_preset("test_preset.txt")
        assert result['SIDE_START_CHANCE'] == 1.0
        assert result['SIDE_DECAY'] == 0.125
        assert result['BRANCH_FROM_SIDE_START_CHANCE'] == 0.5
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_load_preset_with_comments():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        preset_content = """# This is a comment
SIDE_START_CHANCE = 1.0
# Another comment
SIDE_DECAY = 0.125"""
        with open("test_preset.txt", "w") as f:
            f.write(preset_content)
        result = dungeon_gen.load_preset("test_preset.txt")
        assert len(result) == 2
        assert '#' not in str(result)
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_load_preset_with_booleans():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        preset_content = """GENERATE_VERTICAL_FIRST = True
ALLOW_HALLWAY_THROUGH_ROOMS = False"""
        with open("test_preset.txt", "w") as f:
            f.write(preset_content)
        result = dungeon_gen.load_preset("test_preset.txt")
        assert result['GENERATE_VERTICAL_FIRST'] == True
        assert result['ALLOW_HALLWAY_THROUGH_ROOMS'] == False
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_load_preset_with_integers():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        preset_content = """MAX_BRANCHING_DEPTH = 100
ROOM_SIZE = 8"""
        with open("test_preset.txt", "w") as f:
            f.write(preset_content)
        result = dungeon_gen.load_preset("test_preset.txt")
        assert result['MAX_BRANCHING_DEPTH'] == 100
        assert result['ROOM_SIZE'] == 8
        assert isinstance(result['MAX_BRANCHING_DEPTH'], int)
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_load_preset_nonexistent_file():
    result = dungeon_gen.load_preset("nonexistent.txt")
    assert result == {}


def test_load_preset_with_empty_lines():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        preset_content = """SIDE_START_CHANCE = 1.0

SIDE_DECAY = 0.125

"""
        with open("test_preset.txt", "w") as f:
            f.write(preset_content)
        result = dungeon_gen.load_preset("test_preset.txt")
        assert len(result) == 2
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_find_presets_basic():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        Path("preset1.txt").touch()
        Path("preset2.txt").touch()
        Path("other.py").touch()
        result = dungeon_gen.find_presets()
        assert "preset1.txt" in result
        assert "preset2.txt" in result
        assert "other.py" not in result
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_find_presets_excludes_readme():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        Path("README.txt").touch()
        Path("preset.txt").touch()
        result = dungeon_gen.find_presets()
        assert "README.txt" not in result
        assert "preset.txt" in result
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_find_presets_excludes_gen_presets():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        Path("gen_presets.txt").touch()
        Path("long.txt").touch()
        result = dungeon_gen.find_presets()
        assert "gen_presets.txt" not in result
        assert "long.txt" in result
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_find_presets_sorted():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        Path("z_preset.txt").touch()
        Path("a_preset.txt").touch()
        Path("m_preset.txt").touch()
        result = dungeon_gen.find_presets()
        assert result == ["a_preset.txt", "m_preset.txt", "z_preset.txt"]
    finally:
        os.chdir(old_cwd)
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def test_find_presets_empty_directory():
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        result = dungeon_gen.find_presets()
        assert result == []
    finally:
        os.chdir(old_cwd)
        os.rmdir(temp_dir)


def test_clamp_below_min():
    result = dungeon_gen.clamp_chance(-0.5)
    assert result == 0.0


def test_clamp_above_max():
    result = dungeon_gen.clamp_chance(1.5)
    assert result == 1.0


def test_clamp_within_range():
    result = dungeon_gen.clamp_chance(0.5)
    assert result == 0.5


def test_clamp_at_boundaries():
    assert dungeon_gen.clamp_chance(0.0) == 0.0
    assert dungeon_gen.clamp_chance(1.0) == 1.0


def test_chance_at_depth_zero():
    result = dungeon_gen.chance_at_depth(1.0, 0.1, 0)
    assert result == 1.0


def test_chance_at_depth_decreases():
    depth0 = dungeon_gen.chance_at_depth(1.0, 0.1, 0)
    depth1 = dungeon_gen.chance_at_depth(1.0, 0.1, 1)
    depth2 = dungeon_gen.chance_at_depth(1.0, 0.1, 2)
    assert depth0 > depth1
    assert depth1 > depth2


def test_chance_at_depth_with_decay():
    result = dungeon_gen.chance_at_depth(1.0, 0.1, 5)
    assert result == 0.5


def test_chance_at_depth_clamped():
    result = dungeon_gen.chance_at_depth(0.5, 0.2, 10)
    assert result == 0.0


def test_rect_creation():
    rect = dungeon_gen.Rect(10, 20, 30, 40)
    assert rect.x == 10
    assert rect.y == 20
    assert rect.w == 30
    assert rect.h == 40


def test_rect_right_property():
    rect = dungeon_gen.Rect(10, 20, 30, 40)
    assert rect.right == 39


def test_rect_bottom_property():
    rect = dungeon_gen.Rect(10, 20, 30, 40)
    assert rect.bottom == 59


def test_rect_center_property():
    rect = dungeon_gen.Rect(0, 0, 10, 10)
    cx, cy = rect.center
    assert cx == 5
    assert cy == 5


def test_room_creation():
    rect = dungeon_gen.Rect(0, 0, 10, 10)
    room = dungeon_gen.Room(rect, 5)
    assert room.prefab_id == 5
    assert room.rect == rect
    assert room.doors == []


def test_room_center_property():
    rect = dungeon_gen.Rect(0, 0, 10, 10)
    room = dungeon_gen.Room(rect, None)
    cx, cy = room.center
    assert cx == 5
    assert cy == 5


def test_no_overlap_empty_tiles():
    tiles = {}
    rect = dungeon_gen.Rect(0, 0, 5, 5)
    assert not dungeon_gen.room_overlaps(tiles, rect)


def test_overlap_with_room():
    tiles = {(0, 0): ".", (1, 1): "."}
    rect = dungeon_gen.Rect(0, 0, 5, 5)
    assert dungeon_gen.room_overlaps(tiles, rect)


def test_no_overlap_with_hallway():
    tiles = {(0, 0): "h", (1, 1): "h"}
    rect = dungeon_gen.Rect(0, 0, 5, 5)
    assert not dungeon_gen.room_overlaps(tiles, rect)


def test_overlap_partial():
    tiles = {(4, 4): "."}
    rect = dungeon_gen.Rect(0, 0, 5, 5)
    assert dungeon_gen.room_overlaps(tiles, rect)


def test_generate_layout_basic():
    tiles, rooms = dungeon_gen.generate_layout(seed=42)
    assert isinstance(tiles, dict)
    assert isinstance(rooms, list)
    assert len(tiles) > 0
    assert len(rooms) > 0


def test_generate_layout_with_seed_reproducible():
    tiles1, rooms1 = dungeon_gen.generate_layout(seed=12345)
    tiles2, rooms2 = dungeon_gen.generate_layout(seed=12345)
    assert len(tiles1) == len(tiles2)
    assert len(rooms1) == len(rooms2)


def test_generate_layout_different_seeds():
    tiles1, rooms1 = dungeon_gen.generate_layout(seed=111)
    tiles2, rooms2 = dungeon_gen.generate_layout(seed=222)
    assert len(tiles1) != len(tiles2) or len(rooms1) != len(rooms2)


def test_generate_layout_has_base_room():
    tiles, rooms = dungeon_gen.generate_layout(seed=42)
    base_rooms = [r for r in rooms if r.prefab_id is None]
    assert len(base_rooms) == 1


def test_generate_layout_vertical_first_toggle():
    tiles1, rooms1 = dungeon_gen.generate_layout(seed=42, generate_vertical_first=False)
    tiles2, rooms2 = dungeon_gen.generate_layout(seed=42, generate_vertical_first=True)
    assert len(rooms1) != len(rooms2) or len(tiles1) != len(tiles2)


def test_generate_layout_hallway_penetration():
    tiles1, rooms1 = dungeon_gen.generate_layout(seed=42, allow_hallway_through_rooms=False)
    tiles2, rooms2 = dungeon_gen.generate_layout(seed=42, allow_hallway_through_rooms=True)
    assert tiles1 is not None
    assert tiles2 is not None


def test_generate_layout_custom_parameters():
    tiles, rooms = dungeon_gen.generate_layout(side_start_chance=0.8, side_decay=0.05, seed=42)
    assert len(rooms) > 0


def test_generate_layout_high_decay():
    tiles_low, rooms_low = dungeon_gen.generate_layout(side_decay=0.01, seed=42)
    tiles_high, rooms_high = dungeon_gen.generate_layout(side_decay=0.5, seed=42)
    assert len(rooms_high) <= len(rooms_low)


def test_generate_layout_zero_chance():
    tiles, rooms = dungeon_gen.generate_layout(
        side_start_chance=0.0,
        top_bottom_start_chance=0.0,
        branch_from_side_start_chance=0.0,
        branch_from_top_bottom_start_chance=0.0,
        seed=42
    )
    assert len(rooms) == 1


def test_carve_basic():
    tiles = {}
    rect = dungeon_gen.Rect(0, 0, 3, 3)
    dungeon_gen.carve_rect(tiles, rect, ".")
    assert len(tiles) == 9
    assert all(v == "." for v in tiles.values())


def test_carve_hallway_skips_rooms():
    tiles = {(0, 0): ".", (1, 1): "."}
    rect = dungeon_gen.Rect(0, 0, 3, 3)
    dungeon_gen.carve_rect(tiles, rect, "h")
    assert tiles[(0, 0)] == "."
    assert tiles[(1, 1)] == "."


def main():
    print("Running tests...")
    print()
    
    test_load_valid_preset()
    print("test_load_valid_preset")
    
    test_load_preset_with_comments()
    print("test_load_preset_with_comments")
    
    test_load_preset_with_booleans()
    print("test_load_preset_with_booleans")
    
    test_load_preset_with_integers()
    print("test_load_preset_with_integers")
    
    test_load_preset_nonexistent_file()
    print("test_load_preset_nonexistent_file")
    
    test_load_preset_with_empty_lines()
    print("test_load_preset_with_empty_lines")
    
    test_find_presets_basic()
    print("test_find_presets_basic")
    
    test_find_presets_excludes_readme()
    print("test_find_presets_excludes_readme")
    
    test_find_presets_excludes_gen_presets()
    print("test_find_presets_excludes_gen_presets")
    
    test_find_presets_sorted()
    print("test_find_presets_sorted")
    
    test_find_presets_empty_directory()
    print("test_find_presets_empty_directory")
    
    test_clamp_below_min()
    print("test_clamp_below_min")
    
    test_clamp_above_max()
    print("test_clamp_above_max")
    
    test_clamp_within_range()
    print("test_clamp_within_range")
    
    test_clamp_at_boundaries()
    print("test_clamp_at_boundaries")
    
    test_chance_at_depth_zero()
    print("test_chance_at_depth_zero")
    
    test_chance_at_depth_decreases()
    print("test_chance_at_depth_decreases")
    
    test_chance_at_depth_with_decay()
    print("test_chance_at_depth_with_decay")
    
    test_chance_at_depth_clamped()
    print("test_chance_at_depth_clamped")
    
    test_rect_creation()
    print("test_rect_creation")
    
    test_rect_right_property()
    print("test_rect_right_property")
    
    test_rect_bottom_property()
    print("test_rect_bottom_property")
    
    test_rect_center_property()
    print("test_rect_center_property")
    
    test_room_creation()
    print("test_room_creation")
    
    test_room_center_property()
    print("test_room_center_property")
    
    test_no_overlap_empty_tiles()
    print("test_no_overlap_empty_tiles")
    
    test_overlap_with_room()
    print("test_overlap_with_room")
    
    test_no_overlap_with_hallway()
    print("test_no_overlap_with_hallway")
    
    test_overlap_partial()
    print("test_overlap_partial")
    
    test_generate_layout_basic()
    print("test_generate_layout_basic")
    
    test_generate_layout_with_seed_reproducible()
    print("test_generate_layout_with_seed_reproducible")
    
    test_generate_layout_different_seeds()
    print("test_generate_layout_different_seeds")
    
    test_generate_layout_has_base_room()
    print("test_generate_layout_has_base_room")
    
    test_generate_layout_vertical_first_toggle()
    print("test_generate_layout_vertical_first_toggle")
    
    test_generate_layout_hallway_penetration()
    print("test_generate_layout_hallway_penetration")
    
    test_generate_layout_custom_parameters()
    print("test_generate_layout_custom_parameters")
    
    test_generate_layout_high_decay()
    print("test_generate_layout_high_decay")
    
    test_generate_layout_zero_chance()
    print("test_generate_layout_zero_chance")
    
    test_carve_basic()
    print("test_carve_basic")
    
    test_carve_hallway_skips_rooms()
    print("test_carve_hallway_skips_rooms")
    
    print()
    print("All tests passed!")


if __name__ == '__main__':
    main()
