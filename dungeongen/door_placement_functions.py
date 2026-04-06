import pygame

def place_doors_for_room(room, dungeon_context):
    hallways = dungeon_context.hallways
    dungeon_gen = dungeon_context.dungeon_gen
    
    if not dungeon_gen:
        print("No dungeon generator available for door placement")
        return
        
    collision_map = dungeon_context.collision_map
    
    for i, hallway in enumerate(hallways):
        if _hallway_connects_to_room(hallway, room):
            prefab = _get_hallway_prefab(dungeon_gen, hallway)
            
            if prefab and prefab.doors:
                _place_doors_from_prefab(room, hallway, prefab, collision_map, i)
    
    _update_collision_system(room, dungeon_context)


def remove_doors_for_room(room, dungeon_context):
    if not room.door_positions:
        return
        
    tile_size = dungeon_context.tile_size
    door_rects = _create_merged_door_rects(room, tile_size)
        
    # Restore original collision map values
    collision_map = dungeon_context.collision_map
    for door_data in room.door_positions:
        x, y, hallway_idx, local_x, local_y, original_value = door_data
        collision_map[(x, y)] = original_value
    
    # Remove from collision system
    from src.collision import collision_system
    collision_system.remove_temporary_walls(door_rects)
            
    room.door_positions.clear()
    room.locked = False


def _hallway_connects_to_room(hallway, room):
    hall_rect = hallway.rect
    room_rect = room.rect
    
    # Check if hallway is adjacent to room (overlaps or touches edges)
    return not (hall_rect.x + hall_rect.w < room_rect.x or
               hall_rect.x > room_rect.x + room_rect.w or
               hall_rect.y + hall_rect.h < room_rect.y or
               hall_rect.y > room_rect.y + room_rect.h)


def _get_hallway_prefab(dungeon_gen, hallway):
    if hallway.prefab_id is None:
        return None
        
    if hallway.direction == "upways":
        prefabs = dungeon_gen.hallway_prefabs_upways
    else:
        prefabs = dungeon_gen.hallway_prefabs_sideways
        
    if 0 <= hallway.prefab_id < len(prefabs):
        return prefabs[hallway.prefab_id]
    return None


def _place_doors_from_prefab(room, hallway, prefab, collision_map, hallway_index):
    for local_y, row in enumerate(prefab.doors):
        for local_x, cell in enumerate(row):
            if cell and cell != '.':
                world_x = hallway.rect.x + local_x
                world_y = hallway.rect.y + local_y
                
                # Store original value before overwriting
                original_value = collision_map.get((world_x, world_y), ".")
                # Use simple "#" for door collision
                collision_map[(world_x, world_y)] = "#"
                
                # Store door position for later removal
                room.door_positions.append((world_x, world_y, hallway_index, local_x, local_y, original_value))


def _update_collision_system(room, dungeon_context):
    tile_size = dungeon_context.tile_size
    door_rects = _create_merged_door_rects(room, tile_size)
    
    if door_rects:
        from src.collision import collision_system
        collision_system.add_temporary_walls(door_rects)


def _create_merged_door_rects(room, tile_size):
    if not room.door_positions:
        return []
        
    # Group door positions by adjacency
    door_groups = []
    processed = set()
    
    for i, door_data in enumerate(room.door_positions):
        if i in processed:
            continue
            
        x, y = door_data[0], door_data[1]
        current_group = [(x, y)]
        processed.add(i)
        
        # Find all adjacent doors and merge them
        for j, other_data in enumerate(room.door_positions):
            if j in processed:
                continue
                
            other_x, other_y = other_data[0], other_data[1]
            
            # Check if this door is adjacent to any door in current group
            is_adjacent = False
            for gx, gy in current_group:
                if (abs(other_x - gx) == 1 and other_y == gy) or (abs(other_y - gy) == 1 and other_x == gx):
                    is_adjacent = True
                    break
                    
            if is_adjacent:
                current_group.append((other_x, other_y))
                processed.add(j)
                
        door_groups.append(current_group)
    
    # Create merged rectangles from door groups
    merged_rects = []
    for group in door_groups:
        if len(group) == 1:
            # Single door piece
            x, y = group[0]
            merged_rects.append(pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size))
        else:
            # Multiple connected pieces - create bounding rectangle
            min_x = min(pos[0] for pos in group)
            max_x = max(pos[0] for pos in group) 
            min_y = min(pos[1] for pos in group)
            max_y = max(pos[1] for pos in group)
            
            rect = pygame.Rect(
                min_x * tile_size, 
                min_y * tile_size,
                (max_x - min_x + 1) * tile_size,
                (max_y - min_y + 1) * tile_size
            )
            merged_rects.append(rect)
    
    return merged_rects