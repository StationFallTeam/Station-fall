import random
import sys
import time

import pygame

# Left and right of start room
SIDE_START_CHANCE = 1.0
SIDE_DECAY = 0.01

# Branching up and down from side rooms
BRANCH_FROM_SIDE_START_CHANCE = 1.0
BRANCH_FROM_SIDE_DECAY = 0.01

# 2 top and 2 bottom of start room
TOP_BOTTOM_START_CHANCE = 1.0
TOP_BOTTOM_DECAY = 0.01

# Branching left or right from top and bottom rooms
BRANCH_FROM_TOP_BOTTOM_START_CHANCE = 1.0
BRANCH_FROM_TOP_BOTTOM_DECAY = 0.01

MIN_BRANCH_CHANCE = 0.0
MAX_BRANCHING_DEPTH = 100

# Toggle: if True, generate vertical branches first, then horizontal
# if False (default), generate horizontal branches first, then vertical
GENERATE_VERTICAL_FIRST = False

# Toggle: if True, hallways can pass through existing rooms without stopping
# The room won't be placed if it overlaps, but the hallway continues branching
ALLOW_HALLWAY_THROUGH_ROOMS = False

# Rendering settings
SCREEN_W = 1700
SCREEN_H = 900
TILE_SIZE_START = 4
TILE_SIZE_MIN = 1
TILE_SIZE_MAX = 32
CAMERA_SPEED = 18

# Layout settings
BASE_ROOM_SIZE = (20, 8)
ROOM_SIZE = (8, 8)
HALL_LENGTH = 4
HALL_THICKNESS = 2

# Prefab settings
NUMBER_OF_ROOM_PREFABS = 20

# Will print results of generation
DEBUG_VALIDATE_OVERLAPS = True

# Colors
COLOR_BG = (8, 8, 8)
COLOR_ROOM = (77, 155, 255)
COLOR_HALL = (173, 209, 255)
COLOR_GRID = (255, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_FURTHEST = (255, 200, 0)
COLOR_DOOR_DOT = (255, 0, 0)

TileMap = dict[tuple[int, int], str]

class Rect:
    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @property
    def right(self) -> int:
        return self.x + self.w - 1

    @property
    def bottom(self) -> int:
        return self.y + self.h - 1

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)


class Room:
    def __init__(self, rect: Rect, prefab_id: int | None) -> None:
        self.rect = rect
        self.prefab_id = prefab_id
        self.doors: list[tuple[int, int]] = []

    @property
    def center(self) -> tuple[int, int]:
        return self.rect.center


# Geometry helpers
def carve_rect(tiles: TileMap, rect: Rect, tile: str = ".") -> None:
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            if tile == "h" and tiles.get((x, y)) == ".":
                continue
            tiles[(x, y)] = tile



def hallway_rect_from(door: tuple[int, int], direction: str, length: int, thickness: int) -> Rect:
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
    half_w = room.w // 2
    half_center = (half_w - 1) // 2
    left_cx = room.x + half_center
    right_cx = room.x + half_w + half_center
    cy = room.y + (room.h - 1) // 2
    return {
        "top_left": (left_cx, room.y),
        "top_right": (right_cx, room.y),
        "bottom_left": (left_cx, room.bottom),
        "bottom_right": (right_cx, room.bottom),
        "left": (room.x, cy),
        "right": (room.right, cy),
    }


def clamp_chance(value: float) -> float:
    if value > 1.0:
        return 1.0
    if value < MIN_BRANCH_CHANCE:
        return MIN_BRANCH_CHANCE
    return value


def chance_at_depth(start: float, decay: float, depth: int) -> float:
    return clamp_chance(start - (decay * depth))


def load_preset(filename: str) -> dict:
    """Load a configuration preset from a file."""
    preset = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to parse the value
                    if value.lower() == 'true':
                        preset[key] = True
                    elif value.lower() == 'false':
                        preset[key] = False
                    else:
                        try:
                            # Try int first
                            if '.' not in value:
                                preset[key] = int(value)
                            else:
                                preset[key] = float(value)
                        except ValueError:
                            # Keep as string if conversion fails
                            preset[key] = value
    except FileNotFoundError:
        print(f"Preset file '{filename}' not found")
    return preset


def room_overlaps(tiles: TileMap, rect: Rect) -> bool:
    for y in range(rect.y, rect.y + rect.h):
        for x in range(rect.x, rect.x + rect.w):
            if tiles.get((x, y)) == ".":
                return True
    return False


def generate_layout(
    base_room_size: tuple[int, int] = BASE_ROOM_SIZE,
    room_size: tuple[int, int] = ROOM_SIZE,
    hall_length: int = HALL_LENGTH,
    hall_thickness: int = HALL_THICKNESS,
    side_start_chance: float = SIDE_START_CHANCE,
    side_decay: float = SIDE_DECAY,
    top_bottom_start_chance: float = TOP_BOTTOM_START_CHANCE,
    top_bottom_decay: float = TOP_BOTTOM_DECAY,
    branch_from_top_bottom_start_chance: float = BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
    branch_from_top_bottom_decay: float = BRANCH_FROM_TOP_BOTTOM_DECAY,
    branch_from_side_start_chance: float = BRANCH_FROM_SIDE_START_CHANCE,
    branch_from_side_decay: float = BRANCH_FROM_SIDE_DECAY,
    allow_hallway_through_rooms: bool = ALLOW_HALLWAY_THROUGH_ROOMS,
    generate_vertical_first: bool = GENERATE_VERTICAL_FIRST,
    seed: int | None = None,
) -> tuple[TileMap, list[Room]]:
    if seed is not None:
        random.seed(seed)

    base_w, base_h = base_room_size
    tiles: TileMap = {}
    rooms: list[Room] = []
    base_room = Rect(-base_w // 2, -base_h // 2, base_w, base_h)
    carve_rect(tiles, base_room, ".")
    base_room_obj = Room(base_room, prefab_id=None)
    rooms.append(base_room_obj)

    room_w, room_h = room_size
    doors = door_positions(base_room)
    half_room_center = (room_w - 1) // 2
    right_room_center = room_w // 2
    doors["top_left"] = (base_room.x + half_room_center, base_room.y)
    doors["top_right"] = (base_room.right - right_room_center, base_room.y)
    doors["bottom_left"] = (base_room.x + half_room_center, base_room.bottom)
    doors["bottom_right"] = (base_room.right - right_room_center, base_room.bottom)

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
            add_door(current_room, door)
            if room_overlaps(tiles, room_rect):
                if not allow_hallway_through_rooms:
                    break
                # If allow_hallway_through_rooms is True, skip this room but continue extending the hallway
            else:
                carve_rect(tiles, room_rect, ".")
                new_room = Room(room_rect, random.randint(1, NUMBER_OF_ROOM_PREFABS))
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

    return tiles, rooms


def draw_grid(surface: pygame.Surface, tiles: TileMap, tile_size: int, cam_x: int, cam_y: int, show_grid: bool) -> None:
    start_x = cam_x // tile_size
    start_y = cam_y // tile_size
    end_x = (cam_x + SCREEN_W) // tile_size + 1
    end_y = (cam_y + SCREEN_H) // tile_size + 1

    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            tile = tiles.get((x, y))
            if tile is None:
                continue
            color = COLOR_ROOM if tile == "." else COLOR_HALL
            rect = pygame.Rect(
                x * tile_size - cam_x,
                y * tile_size - cam_y,
                tile_size,
                tile_size,
            )
            pygame.draw.rect(surface, color, rect)
            if show_grid:
                pygame.draw.rect(surface, COLOR_GRID, rect, 1)


def find_presets(directory: str = ".") -> list[str]:
    """Find all .txt preset files in the current directory, excluding README.txt and gen_presets.txt."""
    import os
    presets = []
    try:
        for file in sorted(os.listdir(directory)):
            if file.endswith(".txt") and file not in ["README.txt", "gen_presets.txt"]:
                presets.append(file)
    except OSError:
        pass
    return presets


def apply_preset(preset: dict, params: dict) -> None:
    """Apply preset values to parameters dict, overwriting defaults."""
    keys = [
        'SIDE_START_CHANCE', 'SIDE_DECAY',
        'BRANCH_FROM_SIDE_START_CHANCE', 'BRANCH_FROM_SIDE_DECAY',
        'TOP_BOTTOM_START_CHANCE', 'TOP_BOTTOM_DECAY',
        'BRANCH_FROM_TOP_BOTTOM_START_CHANCE', 'BRANCH_FROM_TOP_BOTTOM_DECAY',
        'GENERATE_VERTICAL_FIRST', 'ALLOW_HALLWAY_THROUGH_ROOMS'
    ]
    for key in keys:
        if key in preset:
            params[key] = preset[key]


def generate_and_center_dungeon(params: dict, tile_size: int) -> tuple[TileMap, list[Room], int, int, int]:
    """Generate layout with given parameters and return tiles, rooms, camera position, and seed."""
    seed = time.time_ns()
    tiles, rooms = generate_layout(
        seed=seed,
        side_start_chance=params['SIDE_START_CHANCE'],
        side_decay=params['SIDE_DECAY'],
        branch_from_side_start_chance=params['BRANCH_FROM_SIDE_START_CHANCE'],
        branch_from_side_decay=params['BRANCH_FROM_SIDE_DECAY'],
        top_bottom_start_chance=params['TOP_BOTTOM_START_CHANCE'],
        top_bottom_decay=params['TOP_BOTTOM_DECAY'],
        branch_from_top_bottom_start_chance=params['BRANCH_FROM_TOP_BOTTOM_START_CHANCE'],
        branch_from_top_bottom_decay=params['BRANCH_FROM_TOP_BOTTOM_DECAY'],
        generate_vertical_first=params['GENERATE_VERTICAL_FIRST'],
        allow_hallway_through_rooms=params['ALLOW_HALLWAY_THROUGH_ROOMS'],
    )
    
    base_room = next((room for room in rooms if room.prefab_id is None), None)
    if base_room is not None:
        cam_x = base_room.center[0] * tile_size - SCREEN_W // 2
        cam_y = base_room.center[1] * tile_size - SCREEN_H // 2
    else:
        cam_x = 0
        cam_y = 0
    
    return tiles, rooms, cam_x, cam_y, seed


def run_pygame() -> None:
    pygame.init()
    pygame.display.set_caption("Dungeon Layout")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 18)
    tile_size = TILE_SIZE_START
    show_grid = False
    show_debug = False
    
    # Initialize parameters
    params = {
        'SIDE_START_CHANCE': SIDE_START_CHANCE,
        'SIDE_DECAY': SIDE_DECAY,
        'BRANCH_FROM_SIDE_START_CHANCE': BRANCH_FROM_SIDE_START_CHANCE,
        'BRANCH_FROM_SIDE_DECAY': BRANCH_FROM_SIDE_DECAY,
        'TOP_BOTTOM_START_CHANCE': TOP_BOTTOM_START_CHANCE,
        'TOP_BOTTOM_DECAY': TOP_BOTTOM_DECAY,
        'BRANCH_FROM_TOP_BOTTOM_START_CHANCE': BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
        'BRANCH_FROM_TOP_BOTTOM_DECAY': BRANCH_FROM_TOP_BOTTOM_DECAY,
        'GENERATE_VERTICAL_FIRST': GENERATE_VERTICAL_FIRST,
        'ALLOW_HALLWAY_THROUGH_ROOMS': ALLOW_HALLWAY_THROUGH_ROOMS,
    }
    
    # Load initial preset
    available_presets = find_presets()
    preset_index = 0
    current_preset = available_presets[preset_index] if available_presets else "long.txt"
    
    preset = load_preset(current_preset)
    if preset:
        apply_preset(preset, params)

    tiles, rooms, cam_x, cam_y, seed = generate_and_center_dungeon(params, tile_size)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    tiles, rooms, cam_x, cam_y, seed = generate_and_center_dungeon(params, tile_size)
                elif event.key == pygame.K_p:
                    params['ALLOW_HALLWAY_THROUGH_ROOMS'] = not params['ALLOW_HALLWAY_THROUGH_ROOMS']
                    tiles, rooms, cam_x, cam_y, seed = generate_and_center_dungeon(params, tile_size)
                elif event.key == pygame.K_v:
                    params['GENERATE_VERTICAL_FIRST'] = not params['GENERATE_VERTICAL_FIRST']
                    tiles, rooms, cam_x, cam_y, seed = generate_and_center_dungeon(params, tile_size)
                elif event.key == pygame.K_l:
                    if available_presets:
                        preset_index = (preset_index + 1) % len(available_presets)
                        current_preset = available_presets[preset_index]
                        preset = load_preset(current_preset)
                        if preset:
                            apply_preset(preset, params)
                        tiles, rooms, cam_x, cam_y, seed = generate_and_center_dungeon(params, tile_size)
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_b:
                    show_debug = not show_debug
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    tile_size = min(TILE_SIZE_MAX, tile_size + 2)
                elif event.key == pygame.K_MINUS:
                    tile_size = max(TILE_SIZE_MIN, tile_size - 2)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            cam_x -= CAMERA_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            cam_x += CAMERA_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            cam_y -= CAMERA_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            cam_y += CAMERA_SPEED

        screen.fill(COLOR_BG)
        draw_grid(screen, tiles, tile_size, cam_x, cam_y, show_grid)

        far_room = None
        if show_debug and rooms:
            far_room = max(rooms, key=lambda room: room.center[0] * room.center[0] + room.center[1] * room.center[1])
            fx = far_room.center[0] * tile_size + tile_size // 2 - cam_x
            fy = far_room.center[1] * tile_size + tile_size // 2 - cam_y
            min_room_tiles = min(ROOM_SIZE)
            radius = max(3, (min_room_tiles * tile_size) // 4)
            pygame.draw.circle(screen, COLOR_FURTHEST, (fx, fy), radius)

        if show_debug:
            for room in rooms:
                if room.prefab_id is None and room is not far_room:
                    continue
                label_id = 0 if room is far_room else room.prefab_id
                px = room.center[0] * tile_size + tile_size // 2 - cam_x
                py = room.center[1] * tile_size + tile_size // 2 - cam_y
                label = font.render(str(label_id), True, COLOR_TEXT)
                rect = label.get_rect(center=(px, py))
                screen.blit(label, rect)

                for dx, dy in room.doors:
                    dot_x = dx * tile_size + tile_size // 2 - cam_x
                    dot_y = dy * tile_size + tile_size // 2 - cam_y
                    pygame.draw.circle(screen, COLOR_DOOR_DOT, (dot_x, dot_y), max(2, tile_size // 5))

        room_count = sum(1 for room in rooms if room.prefab_id is not None)
        gen_order = "vertical→horizontal" if params['GENERATE_VERTICAL_FIRST'] else "horizontal→vertical"
        hallway_mode = "through" if params['ALLOW_HALLWAY_THROUGH_ROOMS'] else "stop"
        info = (
            f"seed {seed} | rooms {room_count} | tile {tile_size}px | {gen_order} | hallway {hallway_mode} | preset {current_preset} | "
            "R regen  L preset  V order  P penetrate  G grid  B debug  +/- zoom  arrows/WASD move"
        )
        text = font.render(info, True, COLOR_TEXT)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)


def main() -> None:
    run_pygame()


if __name__ == "__main__":
    main()