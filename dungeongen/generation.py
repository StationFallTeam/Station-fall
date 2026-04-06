import random
from dungeongen.classes import Rect, BaseRoom, HubRoom, CombatRoom, Hallway, TileMap, Prefab
from dungeongen.config import MIN_BRANCH_CHANCE, MAX_BRANCHING_DEPTH

# Carve a rectangle
def carve_rect(tiles: TileMap, rect: Rect, tile: str = "."):
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            if tile == "h" and tiles.get((x, y)) == ".":
                continue
            tiles[(x, y)] = tile

# Branch a hallway from a room
def hallway_rect_from(door: tuple[int, int], direction: str, length: int, thickness: int):
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


def door_positions(room: Rect):
    half_w = room.w // 2
    half_center = (half_w - 1) // 2
    left_cx = room.x + half_center
    right_cx = room.x + half_w + half_center
    cy = room.y + (room.h - 1)
    
    positions = [
        (left_cx, room.y),      # top_left
        (right_cx, room.y),     # top_right
        (left_cx, room.bottom), # bottom_left
        (right_cx, room.bottom), # bottom_right
        (room.x, cy),           # left
        (room.right, cy),       # right
    ]
    
    return positions


def clamp_chance(value: float):
    if value > 1.0:
        return 1.0
    if value < MIN_BRANCH_CHANCE:
        return MIN_BRANCH_CHANCE
    return value


def chance_at_depth(start: float, decay: float, depth: int):
    return clamp_chance(start * ((1 - decay) ** depth))


def room_overlaps(tiles: TileMap, rect: Rect):
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            tile = tiles.get((x, y))
            # Check for any non-empty tile that represents room/wall content
            if tile is not None and tile != "." and tile != "":
                return True
    return False


def hallway_direction(direction: str):
    if direction in ("up", "down"):
        return "upways"
    else:
        return "sideways"


def lowest_top_edge(prefab):
    if not prefab or not prefab.base:
        return 0
    num_rows = len(prefab.base)
    num_cols = len(prefab.base[0]) if num_rows > 0 else 0
    lowest = 0
    for col in range(num_cols):
        for row in range(num_rows):
            if prefab.base[row][col] != '.':
                if row > lowest:
                    lowest = row
                break
    return lowest


def aligned_wall_y(floor_prefab, wall_prefab, anchor_y):
    if not wall_prefab or not wall_prefab.base:
        return anchor_y
    wall_height = len(wall_prefab.base)
    return anchor_y + lowest_top_edge(floor_prefab) - wall_height


def _choose_matching_wall_index(floor_prefab, wall_prefabs):
    if floor_prefab is None or not wall_prefabs:
        return None

    floor_name = getattr(floor_prefab, "name", None)
    if not floor_name:
        return None

    for idx in range(len(wall_prefabs)):
        wall_name = getattr(wall_prefabs[idx], "name", None)
        if wall_name == floor_name:
            return idx

    return None


def _prefab_open_sides(prefab):
    sides = set()
    if prefab is None or not prefab.base:
        return sides

    h = len(prefab.base)
    w = len(prefab.base[0]) if h > 0 else 0
    if h == 0 or w == 0:
        return sides

    if any(prefab.base[0][x] != '.' for x in range(w)):
        sides.add("top")
    if any(prefab.base[h - 1][x] != '.' for x in range(w)):
        sides.add("bottom")
    if any(prefab.base[y][0] != '.' for y in range(h)):
        sides.add("left")
    if any(prefab.base[y][w - 1] != '.' for y in range(h)):
        sides.add("right")

    return sides


def _required_room_sides(room):
    needed = set()
    for dx, dy in room.doors:
        if not _is_point_on_room_edge(room.rect, (dx, dy)):
            continue
        if dy == room.rect.y:
            needed.add("top")
        if dy == room.rect.bottom:
            needed.add("bottom")
        if dx == room.rect.x:
            needed.add("left")
        if dx == room.rect.right:
            needed.add("right")
    return needed


def _is_point_on_room_edge(room_rect: Rect, point: tuple[int, int]):
    x, y = point
    in_bounds = room_rect.x <= x <= room_rect.right and room_rect.y <= y <= room_rect.bottom
    if not in_bounds:
        return False
    return x == room_rect.x or x == room_rect.right or y == room_rect.y or y == room_rect.bottom


def _choose_room_prefab_for_doors(room, room_prefabs):
    if not room_prefabs:
        return None

    needed = _required_room_sides(room)
    compatible = []
    for idx in range(len(room_prefabs)):
        open_sides = _prefab_open_sides(room_prefabs[idx])
        if needed.issubset(open_sides):
            compatible.append(idx)

    if compatible:
        return random.choice(compatible)

    # Fallback so generation can continue even if no perfect prefab exists.
    return random.randint(0, len(room_prefabs) - 1)


def _range_overlap(a0: int, a1: int, b0: int, b1: int):
    start = max(a0, b0)
    end = min(a1, b1)
    if start >= end:  # No overlap or just touching (zero-length overlap)
        return None
    return (start, end)


def _add_missing_room_edge_doors_from_hallways(rooms: list[BaseRoom], hallways: list[Hallway]):
    # Ensure room doors stay in sync with carved hallway-room contacts, including penetration mode.
    for hallway in hallways:
        hall_rect = hallway.rect
        for room in rooms:
            room_rect = room.rect

            if hallway.direction == "sideways":
                overlap = _range_overlap(hall_rect.y, hall_rect.bottom, room_rect.y, room_rect.bottom)
                if overlap is None:
                    continue
                overlap_y0, overlap_y1 = overlap
                door_y = (overlap_y0 + overlap_y1) // 2

                if hall_rect.right == room_rect.x - 1:
                    door = (room_rect.x, door_y)
                    if _is_point_on_room_edge(room_rect, door) and door not in room.doors:
                        room.doors.append(door)
                if hall_rect.x == room_rect.right + 1:
                    door = (room_rect.right, door_y)
                    if _is_point_on_room_edge(room_rect, door) and door not in room.doors:
                        room.doors.append(door)

            if hallway.direction == "upways":
                overlap = _range_overlap(hall_rect.x, hall_rect.right, room_rect.x, room_rect.right)
                if overlap is None:
                    continue
                overlap_x0, overlap_x1 = overlap
                door_x = (overlap_x0 + overlap_x1) // 2

                if hall_rect.bottom == room_rect.y - 1:
                    door = (door_x, room_rect.y)
                    if _is_point_on_room_edge(room_rect, door) and door not in room.doors:
                        room.doors.append(door)
                if hall_rect.y == room_rect.bottom + 1:
                    door = (door_x, room_rect.bottom)
                    if _is_point_on_room_edge(room_rect, door) and door not in room.doors:
                        room.doors.append(door)


def build_collision_map(
    rooms: list[BaseRoom],
    hallways: list[Hallway],
    room_prefabs: list[Prefab] | None,
    main_room_prefabs: list[Prefab] | None,
    hallway_prefabs_upways: list[Prefab] | None,
    hallway_prefabs_sideways: list[Prefab] | None,
    border_width: int = 1,
):
    collision_map: dict[tuple[int, int], str] = {}
    footprint: set[tuple[int, int]] = set()

    def stamp_prefab(prefab, anchor_x, anchor_y):
        if prefab is None:
            return

        # Build footprint from BASE so collision follows real shape (supports notches).
        local_footprint = set()
        for local_y in range(len(prefab.base)):
            for local_x in range(len(prefab.base[local_y])):
                if prefab.base[local_y][local_x] == ".":
                    continue
                world_x = anchor_x + local_x
                world_y = anchor_y + local_y
                local_footprint.add((world_x, world_y))
                footprint.add((world_x, world_y))
                collision_map[(world_x, world_y)] = "."

        # Apply prefab COLLISION data only where BASE exists.
        for local_y in range(len(prefab.collision)):
            for local_x in range(len(prefab.collision[local_y])):
                world_x = anchor_x + local_x
                world_y = anchor_y + local_y
                if (world_x, world_y) not in local_footprint:
                    continue
                collision_value = prefab.collision[local_y][local_x]
                if collision_value != ".":
                    collision_map[(world_x, world_y)] = collision_value
    
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
            stamp_prefab(prefab, room.rect.x, room.rect.y)
    
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
            stamp_prefab(prefab, hallway.rect.x, hallway.rect.y)
    
    # Add a tight border around the dungeon perimeter
    # Check all edges of the dungeon and add collision tiles just outside
    border_tiles: set[tuple[int, int]] = set()
    
    for (x, y) in footprint:
        # Check all 4 cardinal directions
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x + dx, y + dy)
            # If neighbor is outside footprint, mark as border
            if neighbor not in footprint:
                border_tiles.add(neighbor)
    
    # Add border tiles to collision map
    for x, y in border_tiles:
        collision_map[(x, y)] = '#'
    
    return collision_map


def check_collision(collision_map: dict[tuple[int, int], str], x: int, y: int):
    tile_value = collision_map.get((x, y), '.')  # Default to walkable if not in map
    return tile_value != '.'


def check_rect_collision(
    collision_map: dict[tuple[int, int], str],
    rect_or_x: Rect | float,
    y: float = None,
    width: int = None,
    height: int = None,
    tile_size: int = 1,
):
    # Handle both Rect object and separate coordinate arguments
    if isinstance(rect_or_x, Rect):
        x = rect_or_x.x
        y = rect_or_x.y
        width = rect_or_x.w
        height = rect_or_x.h
    else:
        x = rect_or_x
        if y is None or width is None or height is None:
            raise ValueError("When passing coordinates, y, width, and height are required")
    
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
):
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
    rooms: list[BaseRoom] = []
    hallways: list[Hallway] = []
    
    base_room = Rect(-base_w // 2, -base_h // 2, base_w, base_h)
    carve_rect(tiles, base_room, ".")
    base_room_prefab_id = None
    if main_room_prefabs:
        base_room_prefab_id = random.randint(0, len(main_room_prefabs) - 1)
    base_room_obj = HubRoom(base_room, prefab_id=base_room_prefab_id)
    if main_room_wall_prefabs:
        base_room_prefab = None
        if base_room_prefab_id is not None and 0 <= base_room_prefab_id < len(main_room_prefabs):
            base_room_prefab = main_room_prefabs[base_room_prefab_id]
        base_room_obj.wall_prefab_id = _choose_matching_wall_index(base_room_prefab, main_room_wall_prefabs)
    rooms.append(base_room_obj)

    room_w, room_h = room_size
    doors = door_positions(base_room)  # This returns a list now
    half_room_center = (room_w - 1) // 2
    right_room_center = room_w // 2
    # Use specific coordinates instead of door dict
    door_top_left = (base_room.x + half_room_center, base_room.y)
    door_top_right = (base_room.right - right_room_center, base_room.y)
    door_bottom_left = (base_room.x + half_room_center, base_room.bottom)
    door_bottom_right = (base_room.right - right_room_center, base_room.bottom)
    door_left = (base_room.x, base_room.center[1])
    door_right = (base_room.right, base_room.center[1])
    
    available_doors = [door_top_left, door_top_right, door_bottom_left, 
                      door_bottom_right, door_left, door_right]

    # Placement helpers
    def edge_point(room_rect: Rect, direction: str):
        if direction == "up":
            return (room_rect.x + (room_rect.w - 1) // 2, room_rect.y)
        if direction == "down":
            return (room_rect.x + (room_rect.w - 1) // 2, room_rect.bottom)
        if direction == "left":
            return (room_rect.x, room_rect.y + (room_rect.h - 1) // 2)
        return (room_rect.right, room_rect.y + (room_rect.h - 1) // 2)

    def place_room_from_hall_end(end: tuple[int, int], direction: str, align_x: int | None = None):
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

    def hall_end_from_door(door: tuple[int, int], direction: str):
        dx, dy = door
        if direction == "up":
            return (dx, dy - hall_length)
        if direction == "down":
            return (dx, dy + hall_length)
        if direction == "left":
            return (dx - hall_length, dy)
        return (dx + hall_length, dy)

    def opposite_direction(direction: str):
        if direction == "up":
            return "down"
        if direction == "down":
            return "up"
        if direction == "left":
            return "right"
        return "left"

    def add_door(room: BaseRoom, door: tuple[int, int]):
        if not _is_point_on_room_edge(room.rect, door):
            return
        if door not in room.doors:
            room.doors.append(door)

    def branch_chain(
        direction: str,
        start: tuple[int, int],
        source_room: BaseRoom,
        side_dir: str | None = None,
        force: bool = False,
        start_chance_override: float | None = None,
        decay_override: float | None = None,
        allow_side_branches: bool = True,
    ):
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
            
            if hall_dir == "sideways" and hallway_wall_prefabs_sideways:
                hallway_floor_prefab = None
                if hallway_prefab_id is not None and 0 <= hallway_prefab_id < len(hallway_prefabs_sideways):
                    hallway_floor_prefab = hallway_prefabs_sideways[hallway_prefab_id]
                hallway.wall_prefab_id = _choose_matching_wall_index(hallway_floor_prefab, hallway_wall_prefabs_sideways)
            
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
                new_room = CombatRoom(room_rect, prefab_id)
                
                if wall_prefabs:
                    room_floor_prefab = None
                    if prefab_id is not None and 0 <= prefab_id < len(prefabs):
                        room_floor_prefab = prefabs[prefab_id]
                    new_room.wall_prefab_id = _choose_matching_wall_index(room_floor_prefab, wall_prefabs)
                
                # Check for overlaps with existing rooms before adding
                room_overlaps_existing = False
                for existing_room in rooms:
                    if (room_rect.x == existing_room.rect.x and 
                        room_rect.y == existing_room.rect.y and
                        room_rect.w == existing_room.rect.w and 
                        room_rect.h == existing_room.rect.h):
                        room_overlaps_existing = True
                        break
                
                if not room_overlaps_existing:
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
                else:
                    # Skip duplicate room, end this branch
                    break

            sx, sy = edge_point(room_rect, direction)
            force = False
            depth += 1

    # Generate branches in order based on toggle
    if generate_vertical_first:
        # Generate vertical branches first, then horizontal
        branch_chain("up", door_top_left, base_room_obj, side_dir="left")
        branch_chain("up", door_top_right, base_room_obj, side_dir="right")
        branch_chain("down", door_bottom_left, base_room_obj, side_dir="left")
        branch_chain("down", door_bottom_right, base_room_obj, side_dir="right")
        branch_chain("left", door_left, base_room_obj)
        branch_chain("right", door_right, base_room_obj)
    else:
        # Generate horizontal branches first, then vertical (default)
        branch_chain("left", door_left, base_room_obj)
        branch_chain("right", door_right, base_room_obj)
        branch_chain("up", door_top_left, base_room_obj, side_dir="left")
        branch_chain("up", door_top_right, base_room_obj, side_dir="right")
        branch_chain("down", door_bottom_left, base_room_obj, side_dir="left")
        branch_chain("down", door_bottom_right, base_room_obj, side_dir="right")

    _add_missing_room_edge_doors_from_hallways(rooms, hallways)

    # Finalize room prefab IDs based on actual attached hallway sides, then walls.
    for room in rooms:
        if room.is_base_room:
            room_prefabs_list = main_room_prefabs
            wall_prefabs_list = main_room_wall_prefabs
        else:
            room_prefabs_list = prefabs
            wall_prefabs_list = wall_prefabs

        room.prefab_id = _choose_room_prefab_for_doors(room, room_prefabs_list)

        floor_prefab = None
        if room.prefab_id is not None and 0 <= room.prefab_id < len(room_prefabs_list):
            floor_prefab = room_prefabs_list[room.prefab_id]

        room.wall_prefab_id = _choose_matching_wall_index(floor_prefab, wall_prefabs_list)

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
