"""Dungeon layout generation logic.

Standard room and hallway dimensions are defined in config.py.
These values should match all prefab asset dimensions.
"""

import random
from classes import Rect, Room, Hallway, TileMap, Prefab
from config import MIN_BRANCH_CHANCE, MAX_BRANCHING_DEPTH

# Will print results of generation
DEBUG_VALIDATE_OVERLAPS = True


def carve_rect(tiles: TileMap, rect: Rect, tile: str = ".") -> None:
    """Carve a rectangular area into the tilemap."""
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            if tile == "h" and tiles.get((x, y)) == ".":
                continue
            tiles[(x, y)] = tile


def hallway_rect_from(door: tuple[int, int], direction: str, length: int, thickness: int) -> Rect:
    """Create a hallway rectangle from a door in a given direction."""
    dx, dy = door
    if direction == "up":
        x0 = dx - (thickness - 1) // 2
        y0 = dy - length
        return Rect(x0, y0, thickness, length)
    if direction == "down":
        x0 = dx - (thickness - 1) // 2
        y0 = dy + 1
        return Rect(x0, y0, thickness, length)
    if direction == "left":
        x0 = dx - length
        y0 = dy - (thickness - 1) // 2
        return Rect(x0, y0, length, thickness)
    x0 = dx + 1
    y0 = dy - (thickness - 1) // 2
    return Rect(x0, y0, length, thickness)


def door_positions(room: Rect) -> dict[str, tuple[int, int]]:
    """Get all possible door positions for a room."""
    half_w = room.w // 2
    half_center = (half_w - 1) // 2
    left_cx = room.x + half_center
    right_cx = room.x + half_w + half_center
    cy = room.y + (room.h - 1)
    return {
        "top_left": (left_cx, room.y),
        "top_right": (right_cx, room.y),
        "bottom_left": (left_cx, room.bottom),
        "bottom_right": (right_cx, room.bottom),
        "left": (room.x, cy),
        "right": (room.right, cy),
    }


def clamp_chance(value: float) -> float:
    """Clamp a chance value between MIN_BRANCH_CHANCE and 1.0."""
    if value > 1.0:
        return 1.0
    if value < MIN_BRANCH_CHANCE:
        return MIN_BRANCH_CHANCE
    return value


def chance_at_depth(start: float, decay: float, depth: int) -> float:
    """Calculate branch chance at a given depth."""
    return clamp_chance(start - (decay * depth))


def room_overlaps(tiles: TileMap, rect: Rect) -> bool:
    """Check if a room rectangle overlaps with existing rooms."""
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            if tiles.get((x, y)) == ".":
                return True
    return False


def hallway_direction(direction: str) -> str:
    """Convert direction string to hallway type (upways or sideways)."""
    if direction in ("up", "down"):
        return "upways"
    else:
        return "sideways"


def build_collision_map(
    rooms: list[Room],
    hallways: list[Hallway],
    room_prefabs: list[Prefab] | None,
    main_room_prefabs: list[Prefab] | None,
    hallway_prefabs_upways: list[Prefab] | None,
    hallway_prefabs_sideways: list[Prefab] | None,
    border_width: int = 1,
) -> dict[tuple[int, int], str]:
    """
    Build a global collision map from all rooms and hallways.
    
    Stamps each room/hallway's prefab collision data into world coordinates.
    Adds a tight border around the dungeon perimeter (only adjacent to actual dungeon tiles).
    
    Returns:
        dict mapping (x, y) tile coordinates to collision values:
        - '.' = walkable
        - '#' or '0' = solid/wall (collision)
    """
    collision_map: dict[tuple[int, int], str] = {}
    
    # Stamp room collision data
    for room in rooms:
        # Get the appropriate prefab list
        if room.is_base_room:
            prefabs_list = main_room_prefabs or []
        else:
            prefabs_list = room_prefabs or []
        
        # Get the prefab if valid
        if room.prefab_id is not None and 0 <= room.prefab_id < len(prefabs_list):
            prefab = prefabs_list[room.prefab_id]
            
            # Stamp collision data into world coordinates
            for local_y in range(len(prefab.collision)):
                for local_x in range(len(prefab.collision[local_y])):
                    world_x = room.rect.x + local_x
                    world_y = room.rect.y + local_y
                    collision_value = prefab.collision[local_y][local_x]
                    collision_map[(world_x, world_y)] = collision_value
    
    # Stamp hallway collision data
    for hallway in hallways:
        # Get the appropriate prefab list
        if hallway.direction == "upways" and hallway_prefabs_upways:
            prefabs_list = hallway_prefabs_upways
        elif hallway.direction == "sideways" and hallway_prefabs_sideways:
            prefabs_list = hallway_prefabs_sideways
        else:
            continue
        
        # Get the prefab if valid
        if hallway.prefab_id is not None and 0 <= hallway.prefab_id < len(prefabs_list):
            prefab = prefabs_list[hallway.prefab_id]
            
            # Stamp collision data into world coordinates
            for local_y in range(len(prefab.collision)):
                for local_x in range(len(prefab.collision[local_y])):
                    world_x = hallway.rect.x + local_x
                    world_y = hallway.rect.y + local_y
                    collision_value = prefab.collision[local_y][local_x]
                    collision_map[(world_x, world_y)] = collision_value
    
    # Add a tight border around the dungeon perimeter
    # Check all edges of the dungeon and add collision tiles just outside
    border_tiles: set[tuple[int, int]] = set()
    
    for (x, y) in collision_map.keys():
        # Check all 4 cardinal directions
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x + dx, y + dy)
            # If neighbor is not in collision map, it's outside dungeon - mark as border
            if neighbor not in collision_map:
                border_tiles.add(neighbor)
    
    # Add border tiles to collision map
    for x, y in border_tiles:
        collision_map[(x, y)] = '#'
    
    return collision_map


def check_collision(collision_map: dict[tuple[int, int], str], x: int, y: int) -> bool:
    """
    Check if a tile position has collision.
    
    Args:
        collision_map: The global collision map
        x: Tile x coordinate
        y: Tile y coordinate
    
    Returns:
        True if the position is solid (collision), False if walkable or out of bounds
    """
    tile_value = collision_map.get((x, y), '#')  # Default to solid if not in map
    return tile_value != '.'


def check_rect_collision(
    collision_map: dict[tuple[int, int], str],
    x: float,
    y: float,
    width: int,
    height: int,
    tile_size: int = 1,
) -> bool:
    """
    Check if a rect (in pixel coordinates) collides with the collision map.
    
    Args:
        collision_map: The global collision map
        x: Pixel x coordinate (top-left)
        y: Pixel y coordinate (top-left)
        width: Width in pixels
        height: Height in pixels
        tile_size: Size of each tile in pixels
    
    Returns:
        True if any part of the rect is colliding
    """
    # Convert pixel coordinates to tile coordinates
    tile_x1 = int(x // tile_size)
    tile_y1 = int(y // tile_size)
    tile_x2 = int((x + width - 1) // tile_size)
    tile_y2 = int((y + height - 1) // tile_size)
    
    # Check all tiles the rect overlaps
    for ty in range(tile_y1, tile_y2 + 1):
        for tx in range(tile_x1, tile_x2 + 1):
            if check_collision(collision_map, tx, ty):
                return True
    
    return False


def generate_layout(
    base_room_size: tuple[int, int],
    room_size: tuple[int, int],
    hall_length: int,
    hall_thickness: int,
    side_start_chance: float,
    side_decay: float,
    top_bottom_start_chance: float,
    top_bottom_decay: float,
    branch_from_top_bottom_start_chance: float,
    branch_from_top_bottom_decay: float,
    branch_from_side_start_chance: float,
    branch_from_side_decay: float,
    allow_hallway_through_rooms: bool,
    generate_vertical_first: bool,
    prefabs: list[Prefab] | None = None,
    wall_prefabs: list[Prefab] | None = None,
    main_room_prefabs: list[Prefab] | None = None,
    main_room_wall_prefabs: list[Prefab] | None = None,
    hallway_prefabs_upways: list[Prefab] | None = None,
    hallway_prefabs_sideways: list[Prefab] | None = None,
    hallway_wall_prefabs_sideways: list[Prefab] | None = None,
    seed: int | None = None,
) -> tuple[TileMap, list[Room], list[Hallway], dict[tuple[int, int], str]]:
    """Generate a dungeon layout with rooms and hallways, including a global collision map."""
    if seed is not None:
        random.seed(seed)
    
    # If no prefabs provided, use empty lists
    if prefabs is None:
        prefabs = []
    if wall_prefabs is None:
        wall_prefabs = []
    if main_room_prefabs is None:
        main_room_prefabs = []
    if main_room_wall_prefabs is None:
        main_room_wall_prefabs = []
    if hallway_prefabs_upways is None:
        hallway_prefabs_upways = []
    if hallway_prefabs_sideways is None:
        hallway_prefabs_sideways = []
    if hallway_wall_prefabs_sideways is None:
        hallway_wall_prefabs_sideways = []

    base_w, base_h = base_room_size
    tiles: TileMap = {}
    rooms: list[Room] = []
    hallways: list[Hallway] = []
    
    base_room = Rect(-base_w // 2, -base_h // 2, base_w, base_h)
    carve_rect(tiles, base_room, ".")
    base_room_prefab_id = None
    if main_room_prefabs:
        base_room_prefab_id = random.randint(0, len(main_room_prefabs) - 1)
    base_room_obj = Room(base_room, prefab_id=base_room_prefab_id, is_base_room=True)
    if main_room_wall_prefabs:
        base_room_obj.wall_prefab_id = random.randint(0, len(main_room_wall_prefabs) - 1)
    rooms.append(base_room_obj)

    room_w, room_h = room_size
    doors = door_positions(base_room)
    half_room_center = (room_w - 1) // 2
    right_room_center = room_w // 2
    doors["top_left"] = (base_room.x + half_room_center, base_room.y)
    doors["top_right"] = (base_room.right - right_room_center, base_room.y)
    doors["bottom_left"] = (base_room.x + half_room_center, base_room.bottom)
    doors["bottom_right"] = (base_room.right - right_room_center, base_room.bottom)
    doors["left"] = (base_room.x, base_room.center[1])
    doors["right"] = (base_room.right, base_room.center[1])

    # Placement helpers
    def edge_point(room_rect: Rect, direction: str) -> tuple[int, int]:
        if direction == "up":
            return (room_rect.x + (room_rect.w - 1) // 2, room_rect.y)
        if direction == "down":
            return (room_rect.x + (room_rect.w - 1) // 2, room_rect.bottom)
        if direction == "left":
            return (room_rect.x, room_rect.y + (room_rect.h - 1) // 2)
        return (room_rect.right, room_rect.y + (room_rect.h - 1) // 2)

    def place_room_from_hall_end(end: tuple[int, int], direction: str, align_x: int | None = None) -> Rect:
        ex, ey = end
        if direction == "up":
            x0 = ex - (room_w - 1) // 2 if align_x is None else align_x
            return Rect(x0, ey - room_h, room_w, room_h)
        if direction == "down":
            x0 = ex - (room_w - 1) // 2 if align_x is None else align_x
            return Rect(x0, ey + 1, room_w, room_h)
        if direction == "left":
            return Rect(ex - room_w, ey - (room_h - 1) // 2, room_w, room_h)
        return Rect(ex + 1, ey - (room_h - 1) // 2, room_w, room_h)

    def hall_end_from_door(door: tuple[int, int], direction: str) -> tuple[int, int]:
        dx, dy = door
        if direction == "up":
            return (dx, dy - hall_length)
        if direction == "down":
            return (dx, dy + hall_length)
        if direction == "left":
            return (dx - hall_length, dy)
        return (dx + hall_length, dy)

    def opposite_direction(direction: str) -> str:
        if direction == "up":
            return "down"
        if direction == "down":
            return "up"
        if direction == "left":
            return "right"
        return "left"

    def add_door(room: Room, door: tuple[int, int]) -> None:
        if door not in room.doors:
            room.doors.append(door)

    def branch_chain(
        direction: str,
        start: tuple[int, int],
        source_room: Room,
        side_dir: str | None = None,
        force: bool = False,
        start_chance_override: float | None = None,
        decay_override: float | None = None,
        allow_side_branches: bool = True,
    ) -> None:
        depth = 0
        sx, sy = start
        current_room = source_room
        while depth < MAX_BRANCHING_DEPTH:
            if start_chance_override is not None and decay_override is not None:
                start_chance = start_chance_override
                decay = decay_override
            elif direction in ("left", "right"):
                start_chance = side_start_chance
                decay = side_decay
            else:
                start_chance = top_bottom_start_chance
                decay = top_bottom_decay
            chance = chance_at_depth(start_chance, decay, depth)
            if chance <= MIN_BRANCH_CHANCE:
                break
            if not force and random.random() > chance:
                break

            door = (sx, sy)
            hall_end = hall_end_from_door(door, direction)
            hall_rect = hallway_rect_from(door, direction, hall_length, hall_thickness)
            align_x = None
            if direction in ("up", "down") and side_dir:
                if side_dir == "left":
                    align_x = base_room.x
                else:
                    align_x = base_room.right - room_w + 1
            room_rect = place_room_from_hall_end(hall_end, direction, align_x=align_x)

            carve_rect(tiles, hall_rect, "h")
            
            # Create Hallway object with appropriate prefab
            hall_dir = hallway_direction(direction)
            hallway_prefab_id = None
            if hall_dir == "upways" and hallway_prefabs_upways:
                hallway_prefab_id = random.randint(0, len(hallway_prefabs_upways) - 1)
            elif hall_dir == "sideways" and hallway_prefabs_sideways:
                hallway_prefab_id = random.randint(0, len(hallway_prefabs_sideways) - 1)
            
            hallway = Hallway(hall_rect, hall_dir, hallway_prefab_id)
            
            # Only assign hallway wall prefab to SIDEWAYS hallways (they can have dead ends)
            # UPWAYS hallways don't need walls - they're part of the main branching chain
            if hall_dir == "sideways" and hallway_wall_prefabs_sideways:
                hallway.wall_prefab_id = random.randint(0, len(hallway_wall_prefabs_sideways) - 1)
            
            hallways.append(hallway)
            
            add_door(current_room, door)
            if room_overlaps(tiles, room_rect):
                if not allow_hallway_through_rooms:
                    break
                # If allow_hallway_through_rooms is True, skip this room but continue extending the hallway
            else:
                carve_rect(tiles, room_rect, ".")
                # Assign a prefab from loaded prefabs
                if prefabs:
                    prefab_id = random.randint(0, len(prefabs) - 1)
                else:
                    # No prefabs loaded - use None as fallback
                    prefab_id = None
                new_room = Room(room_rect, prefab_id)
                
                # Assign a wall prefab for the north face (always assign if walls available)
                if wall_prefabs:
                    new_room.wall_prefab_id = random.randint(0, len(wall_prefabs) - 1)
                else:
                    new_room.wall_prefab_id = 0  # Default wall if none loaded
                
                entry_door = edge_point(room_rect, opposite_direction(direction))
                add_door(new_room, entry_door)
                rooms.append(new_room)
                current_room = new_room

                if direction in ("up", "down") and side_dir:
                    side_start = clamp_chance(branch_from_top_bottom_start_chance)
                    side_door = edge_point(room_rect, side_dir)
                    branch_chain(
                        side_dir,
                        side_door,
                        current_room,
                        start_chance_override=side_start,
                        decay_override=branch_from_top_bottom_decay,
                        side_dir=None,
                        allow_side_branches=False,
                    )
                elif direction in ("left", "right") and allow_side_branches:
                    side_start = clamp_chance(branch_from_side_start_chance)
                    up_door = edge_point(room_rect, "up")
                    down_door = edge_point(room_rect, "down")
                    branch_chain(
                        "up",
                        up_door,
                        current_room,
                        start_chance_override=side_start,
                        decay_override=branch_from_side_decay,
                    )
                    branch_chain(
                        "down",
                        down_door,
                        current_room,
                        start_chance_override=side_start,
                        decay_override=branch_from_side_decay,
                    )

            sx, sy = edge_point(room_rect, direction)
            force = False
            depth += 1

    # Generate branches in order based on toggle
    if generate_vertical_first:
        # Generate vertical branches first, then horizontal
        branch_chain("up", doors["top_left"], base_room_obj, side_dir="left")
        branch_chain("up", doors["top_right"], base_room_obj, side_dir="right")
        branch_chain("down", doors["bottom_left"], base_room_obj, side_dir="left")
        branch_chain("down", doors["bottom_right"], base_room_obj, side_dir="right")
        branch_chain("left", doors["left"], base_room_obj)
        branch_chain("right", doors["right"], base_room_obj)
    else:
        # Generate horizontal branches first, then vertical (default)
        branch_chain("left", doors["left"], base_room_obj)
        branch_chain("right", doors["right"], base_room_obj)
        branch_chain("up", doors["top_left"], base_room_obj, side_dir="left")
        branch_chain("up", doors["top_right"], base_room_obj, side_dir="right")
        branch_chain("down", doors["bottom_left"], base_room_obj, side_dir="left")
        branch_chain("down", doors["bottom_right"], base_room_obj, side_dir="right")

    if DEBUG_VALIDATE_OVERLAPS:
        for i, room_a in enumerate(rooms):
            for room_b in rooms[i + 1 :]:
                if not (
                    room_a.rect.right < room_b.rect.x
                    or room_b.rect.right < room_a.rect.x
                    or room_a.rect.bottom < room_b.rect.y
                    or room_b.rect.bottom < room_a.rect.y
                ):
                    print(
                        "Overlap warning:",
                        f"A=({room_a.rect.x},{room_a.rect.y},{room_a.rect.w},{room_a.rect.h})",
                        f"B=({room_b.rect.x},{room_b.rect.y},{room_b.rect.w},{room_b.rect.h})",
                    )

    # Build global collision map
    collision_map = build_collision_map(
        rooms,
        hallways,
        prefabs,
        main_room_prefabs,
        hallway_prefabs_upways,
        hallway_prefabs_sideways,
    )

    return tiles, rooms, hallways, collision_map
