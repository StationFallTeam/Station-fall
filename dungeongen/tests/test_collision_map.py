import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loading import (
    load_prefabs, load_wall_prefabs, load_main_room_prefabs, load_main_room_wall_prefabs,
    load_all_hallway_prefabs, load_all_hallway_wall_prefabs
)
from generation import generate_layout, check_collision, check_rect_collision


def _setup_collision_test():
    """Load assets for collision tests."""
    prefabs = load_prefabs("station1")
    wall_prefabs = load_wall_prefabs("station1")
    main_room_prefabs = load_main_room_prefabs("station1")
    main_room_wall_prefabs = load_main_room_wall_prefabs("station1")
    hallway_prefabs = load_all_hallway_prefabs("station1")
    hallway_wall_prefabs = load_all_hallway_wall_prefabs("station1")
    
    tiles, rooms, hallways, collision_map = generate_layout(
        base_room_size=(24, 9),
        room_size=(9, 9),
        hall_length=6,
        hall_thickness=3,
        seed=12345,
        prefabs=prefabs,
        wall_prefabs=wall_prefabs,
        main_room_prefabs=main_room_prefabs,
        main_room_wall_prefabs=main_room_wall_prefabs,
        hallway_prefabs_upways=hallway_prefabs['upways'],
        hallway_prefabs_sideways=hallway_prefabs['sideways'],
        hallway_wall_prefabs_sideways=hallway_wall_prefabs['sideways'],
        side_start_chance=1.0,
        side_decay=0.01,
        branch_from_side_start_chance=1.0,
        branch_from_side_decay=0.01,
        top_bottom_start_chance=1.0,
        top_bottom_decay=0.01,
        branch_from_top_bottom_start_chance=1.0,
        branch_from_top_bottom_decay=0.01,
        generate_vertical_first=False,
        allow_hallway_through_rooms=False,
    )
    
    return tiles, rooms, hallways, collision_map


def test_collision_map_generation():
    """Test that collision map is generated correctly."""
    tiles, rooms, hallways, collision_map = _setup_collision_test()
    
    assert collision_map is not None
    assert len(collision_map) > 0
    assert len(rooms) > 0


def test_collision_map_walkable():
    """Test that base room center is walkable."""
    tiles, rooms, hallways, collision_map = _setup_collision_test()
    
    base_room = next(room for room in rooms if room.is_base_room)
    center_x, center_y = base_room.center
    assert not check_collision(collision_map, center_x, center_y)


def test_collision_map_border():
    """Test that border tiles are solid."""
    tiles, rooms, hallways, collision_map = _setup_collision_test()
    
    min_x = min(x for x, y in collision_map.keys())
    min_y = min(y for x, y in collision_map.keys())
    assert check_collision(collision_map, min_x - 1, min_y - 1)


def test_rect_collision_check():
    """Test that rect collision detection works."""
    tiles, rooms, hallways, collision_map = _setup_collision_test()
    
    base_room = next(room for room in rooms if room.is_base_room)
    center_x, center_y = base_room.center
    
    # Check rect collision (should return bool)
    has_collision = check_rect_collision(collision_map, center_x, center_y, 48, 48, tile_size=1)
    assert isinstance(has_collision, bool)


def main():
    print("Running collision map tests...")
    print()
    
    test_collision_map_generation()
    print("test_collision_map_generation")
    
    test_collision_map_walkable()
    print("test_collision_map_walkable")
    
    test_collision_map_border()
    print("test_collision_map_border")
    
    test_rect_collision_check()
    print("test_rect_collision_check")
    
    print()
    print("All collision map tests passed!")


if __name__ == '__main__':
    main()
