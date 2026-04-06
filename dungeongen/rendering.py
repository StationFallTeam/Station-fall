import pygame
from dungeongen.classes import BaseRoom, CombatRoom, Hallway, TileMap, Prefab
from dungeongen.generation import aligned_wall_y

# Colors
COLOR_BG = (8, 8, 8)
COLOR_ROOM = (77, 155, 255)
COLOR_HALL = (173, 209, 255)
COLOR_GRID = (255, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_FURTHEST = (255, 200, 0)
COLOR_DOOR_DOT = (255, 0, 0)

def draw_grid(
    surface: pygame.Surface, 
    tiles: TileMap, 
    tile_size: int, 
    cam_x: int, 
    cam_y: int, 
    show_grid: bool, 
    screen_w: int,
    screen_h: int,
    rooms: list[BaseRoom] | None = None, 
    hallways: list[Hallway] | None = None,
    prefabs: list[Prefab] | None = None, 
    wall_prefabs: list[Prefab] | None = None,
    main_room_prefabs: list[Prefab] | None = None,
    main_room_wall_prefabs: list[Prefab] | None = None,
    hallway_prefabs_upways: list[Prefab] | None = None,
    hallway_prefabs_sideways: list[Prefab] | None = None,
    hallway_wall_prefabs_sideways: list[Prefab] | None = None,
    sprites: dict | None = None,
    show_sprites: bool = True,
):
    start_x = cam_x // tile_size
    start_y = cam_y // tile_size
    end_x = (cam_x + screen_w) // tile_size + 1
    end_y = (cam_y + screen_h) // tile_size + 1

    # Draw background tiles only if NOT rendering sprites (they'd be covered anyway)
    if not show_sprites:
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
    
    # Only render sprites if show_sprites is True
    if show_sprites and sprites:
        # Render room sprites (base and obstacles)
        if rooms:
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    tile = tiles.get((x, y))
                    if tile != ".":
                        continue
                        
                    # Find which room this tile belongs to
                    for room in rooms:
                        if room.rect.x <= x <= room.rect.right and room.rect.y <= y <= room.rect.bottom:
                            if room.is_base_room:
                                room_prefabs_list = main_room_prefabs or []
                            else:
                                room_prefabs_list = prefabs or []

                            # Check if room has a prefab
                            if room.prefab_id is not None and 0 <= room.prefab_id < len(room_prefabs_list):
                                prefab = room_prefabs_list[room.prefab_id]
                                # Calculate position within the room
                                local_x = x - room.rect.x
                                local_y = y - room.rect.y
                                
                                # Render base sprite first
                                if local_x < len(prefab.base[0]) and local_y < len(prefab.base):
                                    base_id = prefab.base[local_y][local_x]
                                    if base_id != '.' and base_id in sprites.get('bases', {}):
                                        sprite_surf = sprites['bases'][base_id]
                                        scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                        rect = pygame.Rect(
                                            x * tile_size - cam_x,
                                            y * tile_size - cam_y,
                                            tile_size,
                                            tile_size,
                                        )
                                        surface.blit(scaled_sprite, (rect.x, rect.y))
                                
                                # Render obstacle sprite on top
                                if local_x < len(prefab.obstacle[0]) and local_y < len(prefab.obstacle):
                                    obstacle_id = prefab.obstacle[local_y][local_x]
                                    if obstacle_id != '.' and obstacle_id in sprites.get('obstacles', {}):
                                        sprite_surf = sprites['obstacles'][obstacle_id]
                                        scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                        rect = pygame.Rect(
                                            x * tile_size - cam_x,
                                            y * tile_size - cam_y,
                                            tile_size,
                                            tile_size,
                                        )
                                        surface.blit(scaled_sprite, (rect.x, rect.y))
                            break  # Found the room, no need to check others
        
        # Render hallway walls
        if hallways:
            for hallway in hallways:
                if hallway.wall_prefab_id is None:
                    continue

                if hallway.direction != "sideways":
                    continue
                
                if not hallway_wall_prefabs_sideways:
                    continue
                wall_prefabs_list = hallway_wall_prefabs_sideways
                
                if hallway.wall_prefab_id >= len(wall_prefabs_list):
                    continue
                
                wall_prefab = wall_prefabs_list[hallway.wall_prefab_id]
                wall_height = len(wall_prefab.base)
                wall_width = len(wall_prefab.base[0]) if wall_prefab.base else 0

                floor_prefabs_list = []
                if hallway.direction == "upways":
                    floor_prefabs_list = hallway_prefabs_upways or []
                elif hallway.direction == "sideways":
                    floor_prefabs_list = hallway_prefabs_sideways or []
                floor_prefab = None
                if hallway.prefab_id is not None and 0 <= hallway.prefab_id < len(floor_prefabs_list):
                    floor_prefab = floor_prefabs_list[hallway.prefab_id]

                wall_y = aligned_wall_y(floor_prefab, wall_prefab, hallway.rect.y)
                wall_x = hallway.rect.x
                
                # Render wall tiles
                for wall_row in range(wall_height):
                    for wall_col in range(wall_width):
                        if wall_col < wall_width:
                            tile_x = wall_x + wall_col
                            tile_y = wall_y + wall_row
                            
                            # Check if on screen
                            if not (start_x <= tile_x <= end_x and start_y <= tile_y <= end_y):
                                continue
                            
                            wall_id = wall_prefab.base[wall_row][wall_col]
                            if wall_id != '.' and wall_id in sprites.get('walls', {}):
                                screen_x = tile_x * tile_size - cam_x
                                screen_y = tile_y * tile_size - cam_y
                                sprite_surf = sprites['walls'][wall_id]
                                scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                surface.blit(scaled_sprite, (screen_x, screen_y))
        
        # Render room walls
        if rooms:
            for room in rooms:
                if room.is_base_room:
                    wall_prefabs_list = main_room_wall_prefabs or []
                    room_prefabs_list = main_room_prefabs or []
                else:
                    wall_prefabs_list = wall_prefabs or []
                    room_prefabs_list = prefabs or []

                if room.wall_prefab_id is not None and 0 <= room.wall_prefab_id < len(wall_prefabs_list):
                    wall_prefab = wall_prefabs_list[room.wall_prefab_id]
                    wall_height = len(wall_prefab.base)
                    wall_width = len(wall_prefab.base[0]) if wall_prefab.base else 0

                    room_prefab = room_prefabs_list[room.prefab_id] if room.prefab_id is not None and 0 <= room.prefab_id < len(room_prefabs_list) else None
                    wall_y = aligned_wall_y(room_prefab, wall_prefab, room.rect.y)

                    for wall_row in range(wall_height):
                        for wall_col in range(wall_width):
                            if wall_col < room.rect.w:
                                wall_x = room.rect.x + wall_col
                                wall_tile_y = wall_y + wall_row

                                if not (start_x <= wall_x <= end_x and start_y <= wall_tile_y <= end_y):
                                    continue

                                wall_id = wall_prefab.base[wall_row][wall_col]
                                if wall_id != '.' and wall_id in sprites.get('walls', {}):
                                    screen_x = wall_x * tile_size - cam_x
                                    screen_y = wall_tile_y * tile_size - cam_y
                                    sprite_surf = sprites['walls'][wall_id]
                                    scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                    surface.blit(scaled_sprite, (screen_x, screen_y))

        # Render hallway sprites last so hallways appear over walls
        if hallways:
            for hallway in hallways:
                if hallway.prefab_id is None:
                    continue

                if hallway.direction == "upways" and hallway_prefabs_upways:
                    prefabs_list = hallway_prefabs_upways
                elif hallway.direction == "sideways" and hallway_prefabs_sideways:
                    prefabs_list = hallway_prefabs_sideways
                else:
                    continue

                if hallway.prefab_id >= len(prefabs_list):
                    continue

                hallway_prefab = prefabs_list[hallway.prefab_id]

                # Render hallway base sprites
                if hallway_prefab.base:
                    for base_row in range(len(hallway_prefab.base)):
                        for base_col in range(len(hallway_prefab.base[base_row])):
                            base_id = hallway_prefab.base[base_row][base_col]
                            if base_id != '.' and base_id in sprites.get('bases', {}):
                                tile_x = hallway.rect.x + base_col
                                tile_y = hallway.rect.y + base_row
                                if start_x <= tile_x <= end_x and start_y <= tile_y <= end_y:
                                    screen_x = tile_x * tile_size - cam_x
                                    screen_y = tile_y * tile_size - cam_y
                                    sprite_surf = sprites['bases'][base_id]
                                    scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                    surface.blit(scaled_sprite, (screen_x, screen_y))

                # Render hallway obstacle sprites
                if hallway_prefab.obstacle:
                    for obs_row in range(len(hallway_prefab.obstacle)):
                        for obs_col in range(len(hallway_prefab.obstacle[obs_row])):
                            obs_id = hallway_prefab.obstacle[obs_row][obs_col]
                            if obs_id != '.' and obs_id in sprites.get('obstacles', {}):
                                tile_x = hallway.rect.x + obs_col
                                tile_y = hallway.rect.y + obs_row
                                if start_x <= tile_x <= end_x and start_y <= tile_y <= end_y:
                                    screen_x = tile_x * tile_size - cam_x
                                    screen_y = tile_y * tile_size - cam_y
                                    sprite_surf = sprites['obstacles'][obs_id]
                                    scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                    surface.blit(scaled_sprite, (screen_x, screen_y))

        # Render door sprites for locked rooms
        if hallways and rooms:
            for hallway in hallways:
                if hallway.prefab_id is None:
                    continue

                if hallway.direction == "upways" and hallway_prefabs_upways:
                    prefabs_list = hallway_prefabs_upways
                elif hallway.direction == "sideways" and hallway_prefabs_sideways:
                    prefabs_list = hallway_prefabs_sideways
                else:
                    continue

                if hallway.prefab_id >= len(prefabs_list):
                    continue

                hallway_prefab = prefabs_list[hallway.prefab_id]
                
                # Check if any combat room is locked and has doors in this hallway
                for room in rooms:
                    # Only combat rooms have locked state and door positions
                    if isinstance(room, CombatRoom) and room.locked and room.door_positions:
                        for door_data in room.door_positions:
                            world_x, world_y, hallway_idx, local_x, local_y, original_value = door_data
                            
                            # Check if this door belongs to the current hallway
                            if hallway_idx == hallways.index(hallway):
                                # Render door sprite from doors attribute
                                door_sprite_id = None
                                if hasattr(hallway_prefab, 'doors') and hallway_prefab.doors:
                                    if local_y < len(hallway_prefab.doors) and local_x < len(hallway_prefab.doors[local_y]):
                                        door_sprite_id = hallway_prefab.doors[local_y][local_x]
                                
                                if door_sprite_id and door_sprite_id != '.' and door_sprite_id in sprites.get('obstacles', {}):
                                    if start_x <= world_x <= end_x and start_y <= world_y <= end_y:
                                        screen_x = world_x * tile_size - cam_x
                                        screen_y = world_y * tile_size - cam_y
                                        sprite_surf = sprites['obstacles'][door_sprite_id]
                                        scaled_sprite = pygame.transform.scale(sprite_surf, (tile_size, tile_size))
                                        surface.blit(scaled_sprite, (screen_x, screen_y))

    # Render grid if requested
    if show_grid:
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = tiles.get((x, y))
                if tile is None:
                    continue
                rect = pygame.Rect(
                    x * tile_size - cam_x,
                    y * tile_size - cam_y,
                    tile_size,
                    tile_size,
                )
                pygame.draw.rect(surface, COLOR_GRID, rect, 1)
