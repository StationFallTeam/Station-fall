"""Main entry point for dungeon generation pygame visualization."""

import sys
import time
import pygame

from classes import Room, Hallway, TileMap
from loading import (
    find_dungeon_types, find_presets, 
    load_prefabs, load_wall_prefabs, load_main_room_prefabs, load_main_room_wall_prefabs,
    load_all_hallway_prefabs, load_all_hallway_wall_prefabs,
    load_sprites_for_dungeon_type, load_preset
)
from generation import generate_layout, check_collision, check_rect_collision
from rendering import draw_grid, COLOR_BG, COLOR_TEXT, COLOR_FURTHEST, COLOR_DOOR_DOT
from config import (
    BASE_ROOM_SIZE, ROOM_SIZE, HALL_LENGTH, HALL_THICKNESS,
    SCREEN_W, SCREEN_H, TILE_SIZE_START, TILE_SIZE_MIN, TILE_SIZE_MAX, CAMERA_SPEED,
    SIDE_START_CHANCE, SIDE_DECAY, BRANCH_FROM_SIDE_START_CHANCE, BRANCH_FROM_SIDE_DECAY,
    TOP_BOTTOM_START_CHANCE, TOP_BOTTOM_DECAY, BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
    BRANCH_FROM_TOP_BOTTOM_DECAY, GENERATE_VERTICAL_FIRST, ALLOW_HALLWAY_THROUGH_ROOMS
)


def apply_preset(preset: dict, params: dict) -> None:
    """Apply preset values to parameters dict, overwriting defaults."""
    keys = [
        'SIDE_START_CHANCE', 'SIDE_DECAY', 'BRANCH_FROM_SIDE_START_CHANCE', 'BRANCH_FROM_SIDE_DECAY',
        'TOP_BOTTOM_START_CHANCE', 'TOP_BOTTOM_DECAY', 'BRANCH_FROM_TOP_BOTTOM_START_CHANCE', 'BRANCH_FROM_TOP_BOTTOM_DECAY',
        'GENERATE_VERTICAL_FIRST', 'ALLOW_HALLWAY_THROUGH_ROOMS'
    ]
    for key in keys:
        if key in preset:
            params[key] = preset[key]


def generate_and_center_dungeon(
    params: dict,
    tile_size: int,
    prefabs,
    wall_prefabs,
    main_room_prefabs,
    main_room_wall_prefabs,
    hallway_prefabs_upways,
    hallway_prefabs_sideways,
    hallway_wall_prefabs_sideways,
):
    """Generate layout with given parameters and return tiles, rooms, hallways, collision map, camera position, and seed."""
    seed = time.time_ns()
    tiles, rooms, hallways, collision_map = generate_layout(
        base_room_size=BASE_ROOM_SIZE,
        room_size=ROOM_SIZE,
        hall_length=HALL_LENGTH,
        hall_thickness=HALL_THICKNESS,
        seed=seed,
        prefabs=prefabs,
        wall_prefabs=wall_prefabs,
        main_room_prefabs=main_room_prefabs,
        main_room_wall_prefabs=main_room_wall_prefabs,
        hallway_prefabs_upways=hallway_prefabs_upways,
        hallway_prefabs_sideways=hallway_prefabs_sideways,
        hallway_wall_prefabs_sideways=hallway_wall_prefabs_sideways,
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
    
    base_room = next((room for room in rooms if room.is_base_room), None)
    if base_room is not None:
        cam_x = base_room.center[0] * tile_size - SCREEN_W // 2
        cam_y = base_room.center[1] * tile_size - SCREEN_H // 2
    else:
        cam_x = 0
        cam_y = 0
    
    return tiles, rooms, hallways, collision_map, cam_x, cam_y, seed


def run_pygame() -> None:
    """Main pygame loop."""
    pygame.init()
    pygame.display.set_caption("Dungeon Layout")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)
    tile_size = TILE_SIZE_START
    show_grid = False
    show_debug = False
    show_collision = False
    show_sprites = True
    
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
    
    # Load dungeon types and prefabs
    available_dungeon_types = find_dungeon_types()
    dungeon_type_index = 0
    current_dungeon_type = available_dungeon_types[dungeon_type_index] if available_dungeon_types else "station"
    prefabs = load_prefabs(current_dungeon_type)
    wall_prefabs = load_wall_prefabs(current_dungeon_type)
    main_room_prefabs = load_main_room_prefabs(current_dungeon_type)
    main_room_wall_prefabs = load_main_room_wall_prefabs(current_dungeon_type)
    hallway_prefabs = load_all_hallway_prefabs(current_dungeon_type)
    hallway_prefabs_upways = hallway_prefabs['upways']
    hallway_prefabs_sideways = hallway_prefabs['sideways']
    hallway_wall_prefabs = load_all_hallway_wall_prefabs(current_dungeon_type)
    hallway_wall_prefabs_sideways = hallway_wall_prefabs['sideways']
    sprites = load_sprites_for_dungeon_type(current_dungeon_type)
    
    print(f"Loaded dungeon type: {current_dungeon_type}")
    print(f"  Room prefabs: {len(prefabs)}")
    print(f"  Wall prefabs: {len(wall_prefabs)}")
    print(f"  Base room prefabs: {len(main_room_prefabs)}")
    print(f"  Base room wall prefabs: {len(main_room_wall_prefabs)}")
    print(f"  Upways hallway prefabs: {len(hallway_prefabs_upways)}")
    print(f"  Sideways hallway prefabs: {len(hallway_prefabs_sideways)}")
    print(f"  Sideways hallway wall prefabs: {len(hallway_wall_prefabs_sideways)}")
    
    # Load initial preset
    available_presets = find_presets()
    preset_index = 0
    current_preset = available_presets[preset_index] if available_presets else "long.txt"
    
    preset = load_preset(current_preset)
    if preset:
        apply_preset(preset, params)

    tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
        params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
        hallway_prefabs_upways, hallway_prefabs_sideways,
        hallway_wall_prefabs_sideways
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
                        params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
                        hallway_prefabs_upways, hallway_prefabs_sideways,
                        hallway_wall_prefabs_sideways
                    )
                elif event.key == pygame.K_p:
                    params['ALLOW_HALLWAY_THROUGH_ROOMS'] = not params['ALLOW_HALLWAY_THROUGH_ROOMS']
                    tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
                        params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
                        hallway_prefabs_upways, hallway_prefabs_sideways,
                        hallway_wall_prefabs_sideways
                    )
                elif event.key == pygame.K_v:
                    params['GENERATE_VERTICAL_FIRST'] = not params['GENERATE_VERTICAL_FIRST']
                    tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
                        params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
                        hallway_prefabs_upways, hallway_prefabs_sideways,
                        hallway_wall_prefabs_sideways
                    )
                elif event.key == pygame.K_l:
                    if available_presets:
                        preset_index = (preset_index + 1) % len(available_presets)
                        current_preset = available_presets[preset_index]
                        preset = load_preset(current_preset)
                        if preset:
                            apply_preset(preset, params)
                        tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
                            params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
                            hallway_prefabs_upways, hallway_prefabs_sideways,
                            hallway_wall_prefabs_sideways
                        )
                elif event.key == pygame.K_t:
                    if available_dungeon_types:
                        dungeon_type_index = (dungeon_type_index + 1) % len(available_dungeon_types)
                        current_dungeon_type = available_dungeon_types[dungeon_type_index]
                        prefabs = load_prefabs(current_dungeon_type)
                        wall_prefabs = load_wall_prefabs(current_dungeon_type)
                        main_room_prefabs = load_main_room_prefabs(current_dungeon_type)
                        main_room_wall_prefabs = load_main_room_wall_prefabs(current_dungeon_type)
                        hallway_prefabs = load_all_hallway_prefabs(current_dungeon_type)
                        hallway_prefabs_upways = hallway_prefabs['upways']
                        hallway_prefabs_sideways = hallway_prefabs['sideways']
                        hallway_wall_prefabs = load_all_hallway_wall_prefabs(current_dungeon_type)
                        hallway_wall_prefabs_sideways = hallway_wall_prefabs['sideways']
                        sprites = load_sprites_for_dungeon_type(current_dungeon_type)
                        print(f"Loaded dungeon type: {current_dungeon_type}")
                        print(f"  Room prefabs: {len(prefabs)}")
                        print(f"  Wall prefabs: {len(wall_prefabs)}")
                        print(f"  Base room prefabs: {len(main_room_prefabs)}")
                        print(f"  Base room wall prefabs: {len(main_room_wall_prefabs)}")
                        print(f"  Upways hallway prefabs: {len(hallway_prefabs_upways)}")
                        print(f"  Sideways hallway prefabs: {len(hallway_prefabs_sideways)}")
                        print(f"  Sideways hallway wall prefabs: {len(hallway_wall_prefabs_sideways)}")
                        tiles, rooms, hallways, collision_map, cam_x, cam_y, seed = generate_and_center_dungeon(
                            params, tile_size, prefabs, wall_prefabs, main_room_prefabs, main_room_wall_prefabs,
                            hallway_prefabs_upways, hallway_prefabs_sideways,
                            hallway_wall_prefabs_sideways
                        )
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_b:
                    show_debug = not show_debug
                elif event.key == pygame.K_c:
                    show_collision = not show_collision
                elif event.key == pygame.K_s:
                    show_sprites = not show_sprites
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    tile_size = min(TILE_SIZE_MAX, tile_size + 2)
                elif event.key == pygame.K_MINUS:
                    tile_size = max(TILE_SIZE_MIN, tile_size - 2)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            cam_x -= CAMERA_SPEED
        if keys[pygame.K_RIGHT]:
            cam_x += CAMERA_SPEED
        if keys[pygame.K_UP]:
            cam_y -= CAMERA_SPEED
        if keys[pygame.K_DOWN]:
            cam_y += CAMERA_SPEED

        screen.fill(COLOR_BG)
        draw_grid(
            screen, tiles, tile_size, cam_x, cam_y, show_grid, SCREEN_W, SCREEN_H,
            rooms, hallways, prefabs, wall_prefabs, 
            main_room_prefabs, main_room_wall_prefabs,
            hallway_prefabs_upways, hallway_prefabs_sideways,
            hallway_wall_prefabs_sideways, sprites, show_sprites
        )

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
                if room.is_base_room and room is not far_room:
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

        # Collision map visualization
        if show_collision:
            start_x = cam_x // tile_size
            start_y = cam_y // tile_size
            end_x = (cam_x + SCREEN_W) // tile_size + 1
            end_y = (cam_y + SCREEN_H) // tile_size + 1
            
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if (x, y) in collision_map:  # Only visualize tiles in the map
                        collision_value = collision_map[(x, y)]
                        if collision_value != '.':  # Solid/collision tiles
                            rect = pygame.Rect(
                                x * tile_size - cam_x,
                                y * tile_size - cam_y,
                                tile_size,
                                tile_size,
                            )
                            # Draw semi-transparent red overlay for solid tiles
                            pygame.draw.rect(screen, (255, 0, 0, 128), rect)

        room_count = sum(1 for room in rooms if not room.is_base_room)
        hallway_count = len(hallways)
        gen_order = "vertical→horizontal" if params['GENERATE_VERTICAL_FIRST'] else "horizontal→vertical"
        hallway_mode = "through" if params['ALLOW_HALLWAY_THROUGH_ROOMS'] else "stop"
        
        # Render info on multiple lines
        info_line1 = f"seed {seed} | rooms {room_count} | hallways {hallway_count} | tile {tile_size}px | {gen_order}"
        info_line2 = f"hallway {hallway_mode} | preset {current_preset} | type {current_dungeon_type}"
        info_line3 = "R regen  L preset  T type  V order  P penetrate  G grid  S sprites  B debug  C collision  +/- zoom  arrows move"
        
        text1 = font.render(info_line1, True, COLOR_TEXT)
        text2 = font.render(info_line2, True, COLOR_TEXT)
        text3 = font.render(info_line3, True, COLOR_TEXT)
        
        screen.blit(text1, (10, 10))
        screen.blit(text2, (10, 32))
        screen.blit(text3, (10, 54))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)


def main() -> None:
    """Entry point."""
    run_pygame()


if __name__ == "__main__":
    main()
