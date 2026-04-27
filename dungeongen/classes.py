import random
import time
import os

import pygame

# Context object for passing dungeon state to rooms for combat mechanics 
class DungeonContext:
    def __init__(self, tile_size=40, dungeon_runs=0):
        self.enemies = []
        self.collision_map = {}
        self.tile_size = tile_size
        self.dungeon_runs = max(0, int(dungeon_runs))
        self.rooms = []
        self.hallways = []
        self.dungeon_gen = None


# Rectangle class for generation
class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.right = self.x + self.w - 1
        self.bottom = self.y + self.h - 1
        self.center = (self.x + self.w // 2, self.y + self.h // 2)
    
    @property
    def width(self):
        return self.w
    
    @property 
    def height(self):
        return self.h

# Prefab class for generation
class Prefab:
    def __init__(self, collision, obstacle, base, name=None, doors=None, enemy=None, trigger=None):
        self.collision = collision
        self.obstacle = obstacle
        self.base = base
        self.name = name
        self.doors = doors or []
        self.enemy = enemy or []
        self.trigger = trigger or []

# Base Room Class
class BaseRoom:
    def __init__(self, rect, prefab_id=None):
        self.rect = rect
        self.prefab_id = prefab_id
        self.wall_prefab_id = None
        self.doors = []
        self.center = rect.center
        
        # Create trigger rect - one tile smaller on all sides, centered
        margin = 1
        self.triggerRect = Rect(
            rect.x + margin,
            rect.y + margin,
            max(1, rect.w - 2 * margin),
            max(1, rect.h - 2 * margin)
        )

    @property 
    def is_base_room(self):
        return isinstance(self, HubRoom)

# Hub Rooms
class HubRoom(BaseRoom):
    def __init__(self, rect, prefab_id=None):
        super().__init__(rect, prefab_id)
        
        # Trigger areas parsed from prefab
        self.trigger_areas = {}  # Dictionary of {trigger_name: [pygame.Rect, ...]}

# Combat Rooms
class CombatRoom(BaseRoom):
    def __init__(self, rect, prefab_id=None):
        super().__init__(rect, prefab_id)
        
        # Combat and entry tracking
        self.visited = False
        self.locked = False
        self.enemies_spawned = []
        self.spawn_timer = 0
        self.unlock_timer = 0
        
        # Spawn warning visual effects
        self.spawn_warnings = []  # List of (tile_x, tile_y, flash_timer) tuples
        
        # Door positions for locking room - will be populated when doors are placed
        self.door_positions = []  # List of (world_x, world_y, hallway_index, local_x, local_y, original_value) tuples
        
        # Enemy spawn data parsed from prefab
        self.enemy_spawn_data = []

    def on_enter(self, dungeon_context):
        if self.visited:
            return
        
        self.visited = True
        self.locked = True
        self.spawn_timer = 90  # 1.5 seconds at 60fps for visual effect
        
        # Setup spawn warning visual effects
        self.spawn_warnings = []
        for enemy_type, local_x, local_y in self.enemy_spawn_data:
            world_tile_x = self.rect.x + local_x
            world_tile_y = self.rect.y + local_y
            self.spawn_warnings.append([world_tile_x, world_tile_y, 90])  # 90 frames = 1.5 seconds
        
        # Place doors to lock room
        self.place_doors(dungeon_context)

    def place_doors(self, dungeon_context):
        from dungeongen.door_placement_functions import place_doors_for_room
        place_doors_for_room(self, dungeon_context)

        # music set to combat
        pygame.mixer.music.stop()
        music_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.load('sound/magnetic-march.ogg')
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)

    def unplace_doors(self, dungeon_context):
        from dungeongen.door_placement_functions import remove_doors_for_room
        remove_doors_for_room(self, dungeon_context)

        # music reset to normal
        pygame.mixer.music.stop()
        music_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.load('sound/peace-in-void.ogg')
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)

    def update(self, dungeon_context):
        if not self.visited:
            return
            
        # Update spawn warning effects
        for warning in self.spawn_warnings[:]:
            warning[2] -= 1  # Decrease flash timer
            if warning[2] <= 0:
                self.spawn_warnings.remove(warning)
            
        # Handle spawn delay
        if self.locked and self.spawn_timer > 0:
            self.spawn_timer -= 1
            if self.spawn_timer == 0:
                self.spawn_enemies(dungeon_context)
                
        # Check if all enemies defeated
        if self.locked and self.enemies_spawned:
            alive_enemies = [e for e in self.enemies_spawned if e.health > 0]
            self.enemies_spawned = alive_enemies
            
            if not alive_enemies and self.unlock_timer <= 0:
                self.unlock_timer = 60  # 1 second delay
                
        # Handle unlock delay
        if self.unlock_timer > 0:
            self.unlock_timer -= 1
            if self.unlock_timer == 0:
                self.unplace_doors(dungeon_context)

    def _create_enemy_by_type(self, enemy_type, world_x, world_y, dungeon_runs=0):
        from src.enemy import Enemy
        from src.ranged_enemy import RangedEnemy
        from src.boss import Boss
        
        # For now, all enemy types create the same Enemy class
        # This can be extended later to handle different enemy types
        if enemy_type in ["enemy"]:
            return Enemy(world_x, world_y, dungeon_runs=dungeon_runs)
        elif enemy_type in ["rangedEnemy"]:
            return RangedEnemy(world_x, world_y)
        elif enemy_type in ["boss"]:
            return Boss(world_x, world_y)
        
        # Return None for unknown enemy types
        print(f"Warning: Unknown enemy type '{enemy_type}', skipping spawn")
        return None

    def spawn_enemies(self, dungeon_context):
        if not self.enemy_spawn_data:
            return
            
        # Clear spawn warnings when actually spawning
        self.spawn_warnings.clear()
        
        # Spawn enemies from parsed prefab data
        enemies = dungeon_context.enemies
        tile_size = dungeon_context.tile_size
        dungeon_runs = getattr(dungeon_context, "dungeon_runs", 0)
        
        for enemy_type, local_x, local_y in self.enemy_spawn_data:
            # Convert local room coordinates to world coordinates
            world_x = (self.rect.x + local_x) * tile_size
            world_y = (self.rect.y + local_y) * tile_size
            
            # Create enemy at world coordinates
            enemy = self._create_enemy_by_type(enemy_type, world_x, world_y, dungeon_runs=dungeon_runs)
            if enemy:
                enemies.append(enemy)
                self.enemies_spawned.append(enemy)

    def draw_spawn_warnings(self, surface, camera, tile_size):
        for warning in self.spawn_warnings:
            tile_x, tile_y, flash_timer = warning
      
            # Calculate opacity based on countdown (starts at 0, goes to 255)
            max_timer = 90  # Should match the initial timer value in on_enter
            opacity = int(((max_timer - flash_timer) / max_timer) * 255)
            opacity = max(0, min(255, opacity))  # Clamp to 0-255
            
            # Calculate screen position (center of tile)
            world_x = (tile_x * tile_size) + (tile_size // 2)
            world_y = (tile_y * tile_size) + (tile_size // 2)
            screen_pos = camera.apply(pygame.Rect(world_x, world_y, 1, 1)).center
            
            # Draw circle with increasing opacity
            circle_radius = tile_size // 3
            circle_color = (255, 0, 0, opacity)
            
            # Create a surface for the circle with per-pixel alpha
            circle_surface = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, circle_color, (circle_radius, circle_radius), circle_radius)
            
            # Blit the circle surface to the main surface
            circle_rect = circle_surface.get_rect(center=screen_pos)
            surface.blit(circle_surface, circle_rect)

# Convenience aliases for backwards compatibility 
Room = BaseRoom  # For existing code that expects Room class


# Hallway class for generation
class Hallway:
    def __init__(self, rect, direction, prefab_id=None):
        self.rect = rect
        self.direction = direction
        self.prefab_id = prefab_id
        self.wall_prefab_id = None

TileMap = dict


def _build_sprite_aware_collision_rects(
    collision_map,
    rooms,
    hallways,
    room_prefabs,
    main_room_prefabs,
    hallway_prefabs_upways,
    hallway_prefabs_sideways,
    sprites,
    tile_size,
):
    walls = []
    if not collision_map:
        return walls

    # Map world tile -> obstacle sprite id for tiles where both collision and obstacle are present.
    obstacle_on_collision = {}

    def stamp_prefab_overlap(prefab, anchor_x, anchor_y):
        if prefab is None:
            return
        for local_y in range(len(prefab.collision)):
            for local_x in range(len(prefab.collision[local_y])):
                if prefab.collision[local_y][local_x] == ".":
                    continue
                if local_y >= len(prefab.obstacle) or local_x >= len(prefab.obstacle[local_y]):
                    continue
                obstacle_id = prefab.obstacle[local_y][local_x]
                if obstacle_id == ".":
                    continue
                world_pos = (anchor_x + local_x, anchor_y + local_y)
                obstacle_on_collision[world_pos] = obstacle_id

    for room in rooms:
        if room.is_base_room:
            prefab_list = main_room_prefabs or []
        else:
            prefab_list = room_prefabs or []
        if room.prefab_id is None or room.prefab_id < 0 or room.prefab_id >= len(prefab_list):
            continue
        stamp_prefab_overlap(prefab_list[room.prefab_id], room.rect.x, room.rect.y)

    for hallway in hallways:
        if hallway.direction == "upways":
            prefab_list = hallway_prefabs_upways or []
        else:
            prefab_list = hallway_prefabs_sideways or []
        if hallway.prefab_id is None or hallway.prefab_id < 0 or hallway.prefab_id >= len(prefab_list):
            continue
        stamp_prefab_overlap(prefab_list[hallway.prefab_id], hallway.rect.x, hallway.rect.y)

    obstacle_sprites = {}
    if sprites and "obstacles" in sprites:
        obstacle_sprites = sprites["obstacles"]
    mask_cache = {}

    for (tile_x, tile_y), value in collision_map.items():
        if value == ".":
            continue

        # Force simple collision for door tiles (marked with "#")
        if value == "#":
            walls.append(pygame.Rect(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size))
            continue

        obstacle_id = obstacle_on_collision.get((tile_x, tile_y))
        sprite = obstacle_sprites.get(obstacle_id) if obstacle_id else None
        if sprite is None:
            walls.append(pygame.Rect(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size))
            continue

        mask = mask_cache.get(obstacle_id)
        if mask is None:
            mask = pygame.mask.from_surface(sprite)
            mask_cache[obstacle_id] = mask

        mask_w, mask_h = mask.get_size()
        if mask_w <= 0 or mask_h <= 0:
            walls.append(pygame.Rect(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size))
            continue

        # Build colliders from opaque pixels only, scaled to tile size.
        has_opaque = False
        for py in range(mask_h):
            run_start = None
            for px in range(mask_w):
                opaque = mask.get_at((px, py)) != 0
                if opaque and run_start is None:
                    run_start = px
                if (not opaque) and run_start is not None:
                    has_opaque = True
                    x0 = (tile_x * tile_size) + (run_start * tile_size) // mask_w
                    x1 = (tile_x * tile_size) + (px * tile_size) // mask_w
                    y0 = (tile_y * tile_size) + (py * tile_size) // mask_h
                    y1 = (tile_y * tile_size) + ((py + 1) * tile_size) // mask_h
                    if x1 > x0 and y1 > y0:
                        walls.append(pygame.Rect(x0, y0, x1 - x0, y1 - y0))
                    run_start = None

            if run_start is not None:
                has_opaque = True
                x0 = (tile_x * tile_size) + (run_start * tile_size) // mask_w
                x1 = (tile_x * tile_size) + (mask_w * tile_size) // mask_w
                y0 = (tile_y * tile_size) + (py * tile_size) // mask_h
                y1 = (tile_y * tile_size) + ((py + 1) * tile_size) // mask_h
                if x1 > x0 and y1 > y0:
                    walls.append(pygame.Rect(x0, y0, x1 - x0, y1 - y0))

        if not has_opaque:
            # Fully transparent obstacle sprite should not create a blocker.
            continue

    return walls

# API for Generating Dungeons
class DungeonGen:
    PRESET_KEYS = [
        "SIDE_START_CHANCE",
        "SIDE_DECAY",
        "BRANCH_FROM_SIDE_START_CHANCE",
        "BRANCH_FROM_SIDE_DECAY",
        "TOP_BOTTOM_START_CHANCE",
        "TOP_BOTTOM_DECAY",
        "BRANCH_FROM_TOP_BOTTOM_START_CHANCE",
        "BRANCH_FROM_TOP_BOTTOM_DECAY",
        "GENERATE_VERTICAL_FIRST",
        "ALLOW_HALLWAY_THROUGH_ROOMS",
    ]

    def __init__(self, dungeon_type=None, preset_name=None, base_path="dungeon_types", preset_directory="dungeon_gen_presets"):
        self.base_path = base_path
        self.preset_directory = preset_directory

        self.dungeon_type = dungeon_type
        self.preset_name = preset_name

        self.available_dungeon_types = []
        self.available_presets = []
        self.assets_by_type = {}

        self.params = self._default_params()

        self.prefabs = []
        self.wall_prefabs = []
        self.main_room_prefabs = []
        self.main_room_wall_prefabs = []
        self.hallway_prefabs_upways = []
        self.hallway_prefabs_sideways = []
        self.hallway_wall_prefabs_sideways = []
        self.sprites = None

        self.tiles = {}
        self.rooms = []
        self.hallways = []
        self.collision_map = {}

        self.seed = None
        self.tile_size = self._default_tile_size()
        self.cam_x = 0
        self.cam_y = 0

        self.loaded = False
        self.generated = False

    def _default_params(self):
        from dungeongen.config import (
            ALLOW_HALLWAY_THROUGH_ROOMS,
            BRANCH_FROM_SIDE_DECAY,
            BRANCH_FROM_SIDE_START_CHANCE,
            BRANCH_FROM_TOP_BOTTOM_DECAY,
            BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
            GENERATE_VERTICAL_FIRST,
            SIDE_DECAY,
            SIDE_START_CHANCE,
            TOP_BOTTOM_DECAY,
            TOP_BOTTOM_START_CHANCE,
        )

        params = {}
        params["SIDE_START_CHANCE"] = SIDE_START_CHANCE
        params["SIDE_DECAY"] = SIDE_DECAY
        params["BRANCH_FROM_SIDE_START_CHANCE"] = BRANCH_FROM_SIDE_START_CHANCE
        params["BRANCH_FROM_SIDE_DECAY"] = BRANCH_FROM_SIDE_DECAY
        params["TOP_BOTTOM_START_CHANCE"] = TOP_BOTTOM_START_CHANCE
        params["TOP_BOTTOM_DECAY"] = TOP_BOTTOM_DECAY
        params["BRANCH_FROM_TOP_BOTTOM_START_CHANCE"] = BRANCH_FROM_TOP_BOTTOM_START_CHANCE
        params["BRANCH_FROM_TOP_BOTTOM_DECAY"] = BRANCH_FROM_TOP_BOTTOM_DECAY
        params["GENERATE_VERTICAL_FIRST"] = GENERATE_VERTICAL_FIRST
        params["ALLOW_HALLWAY_THROUGH_ROOMS"] = ALLOW_HALLWAY_THROUGH_ROOMS
        return params

    def _default_tile_size(self):
        from dungeongen.config import TILE_SIZE_START

        return TILE_SIZE_START

    def _reset_generation(self):
        self.tiles = {}
        self.rooms = []
        self.hallways = []
        self.collision_map = {}
        self.seed = None
        self.cam_x = 0
        self.cam_y = 0
        self.generated = False

    def _apply_preset(self, preset):
        self.params = self._default_params()
        if not preset:
            return

        for key in self.PRESET_KEYS:
            if key in preset:
                self.params[key] = preset[key]

    def _activate_type_assets(self, dungeon_type):
        if dungeon_type not in self.assets_by_type:
            print("Unknown dungeon type:", dungeon_type)
            return False

        assets = self.assets_by_type[dungeon_type]
        self.dungeon_type = dungeon_type
        self.prefabs = assets["prefabs"]
        self.wall_prefabs = assets["wall_prefabs"]
        self.main_room_prefabs = assets["main_room_prefabs"]
        self.main_room_wall_prefabs = assets["main_room_wall_prefabs"]
        self.hallway_prefabs_upways = assets["hallway_prefabs_upways"]
        self.hallway_prefabs_sideways = assets["hallway_prefabs_sideways"]
        self.hallway_wall_prefabs_sideways = assets["hallway_wall_prefabs_sideways"]
        self.sprites = assets["sprites"]
        return True

    def _generate_current_selection(self, seed=None):
        from dungeongen.config import BASE_ROOM_SIZE, HALL_LENGTH, HALL_THICKNESS, ROOM_SIZE, SCREEN_H, SCREEN_W
        from dungeongen.generation import generate_layout

        if self.dungeon_type is None:
            print("No dungeon type selected.")
            return

        if seed is None:
            self.seed = time.time_ns()
        else:
            self.seed = seed

        self.tiles, self.rooms, self.hallways, self.collision_map = generate_layout(
            base_room_size=BASE_ROOM_SIZE,
            room_size=ROOM_SIZE,
            hall_length=HALL_LENGTH,
            hall_thickness=HALL_THICKNESS,
            side_start_chance=self.params["SIDE_START_CHANCE"],
            side_decay=self.params["SIDE_DECAY"],
            top_bottom_start_chance=self.params["TOP_BOTTOM_START_CHANCE"],
            top_bottom_decay=self.params["TOP_BOTTOM_DECAY"],
            branch_from_top_bottom_start_chance=self.params["BRANCH_FROM_TOP_BOTTOM_START_CHANCE"],
            branch_from_top_bottom_decay=self.params["BRANCH_FROM_TOP_BOTTOM_DECAY"],
            branch_from_side_start_chance=self.params["BRANCH_FROM_SIDE_START_CHANCE"],
            branch_from_side_decay=self.params["BRANCH_FROM_SIDE_DECAY"],
            allow_hallway_through_rooms=self.params["ALLOW_HALLWAY_THROUGH_ROOMS"],
            generate_vertical_first=self.params["GENERATE_VERTICAL_FIRST"],
            prefabs=self.prefabs,
            wall_prefabs=self.wall_prefabs,
            main_room_prefabs=self.main_room_prefabs,
            main_room_wall_prefabs=self.main_room_wall_prefabs,
            hallway_prefabs_upways=self.hallway_prefabs_upways,
            hallway_prefabs_sideways=self.hallway_prefabs_sideways,
            hallway_wall_prefabs_sideways=self.hallway_wall_prefabs_sideways,
            seed=self.seed,
        )

        self.generated = True
        self.center_camera(SCREEN_W, SCREEN_H)

    def load_complete(self, tile_size):
        # Complete loading and setup for gameplay
        if not self.loaded:
            self.load_all_assets()
            
        self.generate_dungeon_random()
        
        # Handle all collision and trigger setup
        from src.collision import clear_temporary_walls, clear_triggers, update_collision_walls
        from dungeongen.loading import parse_all_prefab_data
        
        clear_temporary_walls()
        clear_triggers()
        
        # Parse and setup triggers/enemies
        parse_all_prefab_data(self, tile_size)
        
        # Get collision walls and update collision system
        walls = self.get_collision_rects(tile_size=tile_size)
        update_collision_walls(walls)
        
        # Get spawn position
        spawn = self._get_spawn_position(tile_size)
        
        # Create and setup dungeon context
        dungeon_context = self._create_dungeon_context(tile_size)
        
        return spawn, dungeon_context
    
    def _get_spawn_position(self, tile_size):
        base_room = next((r for r in self.rooms if r.is_base_room), None)
        if base_room is None:
            return (0, 0)
        
        center_x, center_y = base_room.center
        spawn_x = center_x * tile_size
        spawn_y = (center_y + 1) * tile_size  # Move down 1 tile from center
        return (spawn_x, spawn_y)
    
    def _create_dungeon_context(self, tile_size):
        dungeon_context = DungeonContext(tile_size)
        dungeon_context.enemies = []
        dungeon_context.collision_map = self.collision_map
        dungeon_context.rooms = self.rooms
        dungeon_context.hallways = self.hallways
        dungeon_context.dungeon_gen = self
        return dungeon_context
    
    def get_room_counts(self):        
        total_rooms = sum(1 for room in self.rooms if not room.is_base_room)
        completed_rooms = sum(1 for room in self.rooms 
                             if not room.is_base_room and room.visited and not room.locked)
        return total_rooms, completed_rooms

    def load_all_assets(self):
        from dungeongen.loading import (
            find_dungeon_types,
            find_presets,
            load_all_hallway_prefabs,
            load_all_hallway_wall_prefabs,
            load_main_room_prefabs,
            load_main_room_wall_prefabs,
            load_prefabs,
            load_sprites_for_dungeon_type,
            load_wall_prefabs,
        )

        self.available_dungeon_types = find_dungeon_types(self.base_path)
        self.available_presets = find_presets(self.preset_directory)
        self.assets_by_type = {}

        for dungeon_type in self.available_dungeon_types:
            hallway_prefabs = load_all_hallway_prefabs(dungeon_type, self.base_path)
            hallway_wall_prefabs = load_all_hallway_wall_prefabs(dungeon_type, self.base_path)
            data = {}
            data["prefabs"] = load_prefabs(dungeon_type, self.base_path)
            data["wall_prefabs"] = load_wall_prefabs(dungeon_type, self.base_path)
            data["main_room_prefabs"] = load_main_room_prefabs(dungeon_type, self.base_path)
            data["main_room_wall_prefabs"] = load_main_room_wall_prefabs(dungeon_type, self.base_path)
            data["hallway_prefabs_upways"] = hallway_prefabs.get("upways", [])
            data["hallway_prefabs_sideways"] = hallway_prefabs.get("sideways", [])
            data["hallway_wall_prefabs_sideways"] = hallway_wall_prefabs.get("sideways", [])
            data["sprites"] = load_sprites_for_dungeon_type(dungeon_type, self.base_path)
            self.assets_by_type[dungeon_type] = data

        self.loaded = True

    def _load_preset_values(self, preset_name):
        if preset_name is None:
            return None
        from dungeongen.loading import load_preset

        return load_preset(preset_name, self.preset_directory)

    def generate_dungeon_of_type(self, dungeon_type, seed=None):
        if not self.loaded:
            self.load_all_assets()

        if dungeon_type not in self.assets_by_type:
            print("Unknown dungeon type:", dungeon_type)
            return

        self._reset_generation()
        ok = self._activate_type_assets(dungeon_type)
        if not ok:
            return

        if self.available_presets:
            self.preset_name = random.choice(self.available_presets)
        else:
            self.preset_name = None

        self._apply_preset(self._load_preset_values(self.preset_name))
        self._generate_current_selection(seed)

    def generate_dungeon_of_preset(self, preset_name, seed=None):
        if not self.loaded:
            self.load_all_assets()

        if not self.available_dungeon_types:
            print("No valid dungeon types found.")
            return

        if preset_name not in self.available_presets:
            print("Unknown preset:", preset_name)
            return

        dungeon_type = random.choice(self.available_dungeon_types)
        self._reset_generation()
        ok = self._activate_type_assets(dungeon_type)
        if not ok:
            return

        self.preset_name = preset_name
        self._apply_preset(self._load_preset_values(self.preset_name))
        self._generate_current_selection(seed)

    def generate_dungeon_specific(self, dungeon_type, preset_name, seed=None):
        if not self.loaded:
            self.load_all_assets()

        if dungeon_type not in self.assets_by_type:
            print("Unknown dungeon type:", dungeon_type)
            return

        if preset_name is not None and preset_name not in self.available_presets:
            print("Unknown preset:", preset_name)
            return

        self._reset_generation()
        ok = self._activate_type_assets(dungeon_type)
        if not ok:
            return

        self.preset_name = preset_name
        self._apply_preset(self._load_preset_values(self.preset_name))
        self._generate_current_selection(seed)

    def generate_dungeon_random(self, seed=None):
        if not self.loaded:
            self.load_all_assets()

        if not self.available_dungeon_types:
            print("No valid dungeon types found.")
            return

        dungeon_type = random.choice(self.available_dungeon_types)
        if self.available_presets:
            self.preset_name = random.choice(self.available_presets)
        else:
            self.preset_name = None

        self._reset_generation()
        ok = self._activate_type_assets(dungeon_type)
        if not ok:
            return

        self._apply_preset(self._load_preset_values(self.preset_name))
        self._generate_current_selection(seed)

    def center_camera(self, screen_w, screen_h, tile_size=None):
        if not self.generated:
            return

        if tile_size is None:
            active_tile_size = self.tile_size
        else:
            active_tile_size = tile_size

        base_room = None
        for room in self.rooms:
            if room.is_base_room:
                base_room = room
                break

        if base_room is None:
            self.cam_x = 0
            self.cam_y = 0
            return

        self.cam_x = base_room.center[0] * active_tile_size - screen_w // 2
        self.cam_y = base_room.center[1] * active_tile_size - screen_h // 2

    def draw(self, surface=None, tile_size=None, cam_x=None, cam_y=None, show_sprites=True, show_collision_map=False, show_grid=False):
        from dungeongen.rendering import draw_grid

        if not self.generated:
            print("No dungeon has been generated yet.")
            return

        if surface is None:
            target_surface = pygame.display.get_surface()
        else:
            target_surface = surface

        if target_surface is None:
            print("No pygame surface to draw on.")
            return

        if tile_size is None:
            active_tile_size = self.tile_size
        else:
            active_tile_size = tile_size

        if cam_x is None:
            active_cam_x = self.cam_x
        else:
            active_cam_x = cam_x

        if cam_y is None:
            active_cam_y = self.cam_y
        else:
            active_cam_y = cam_y

        self.tile_size = active_tile_size
        self.cam_x = active_cam_x
        self.cam_y = active_cam_y

        draw_grid(
            target_surface,
            self.tiles,
            active_tile_size,
            active_cam_x,
            active_cam_y,
            show_grid,
            target_surface.get_width(),
            target_surface.get_height(),
            self.rooms,
            self.hallways,
            self.prefabs,
            self.wall_prefabs,
            self.main_room_prefabs,
            self.main_room_wall_prefabs,
            self.hallway_prefabs_upways,
            self.hallway_prefabs_sideways,
            self.hallway_wall_prefabs_sideways,
            self.sprites,
            show_sprites,
        )

        if not show_collision_map:
            return

        start_x = active_cam_x // active_tile_size
        start_y = active_cam_y // active_tile_size
        end_x = (active_cam_x + target_surface.get_width()) // active_tile_size + 1
        end_y = (active_cam_y + target_surface.get_height()) // active_tile_size + 1

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if (x, y) not in self.collision_map:
                    continue
                if self.collision_map[(x, y)] == ".":
                    continue

                rect = pygame.Rect(
                    x * active_tile_size - active_cam_x,
                    y * active_tile_size - active_cam_y,
                    active_tile_size,
                    active_tile_size,
                )
                pygame.draw.rect(target_surface, (255, 0, 0, 128), rect)

    def get_collision_rects(self, tile_size=None):
        if tile_size is None:
            active_tile_size = self.tile_size
        else:
            active_tile_size = tile_size

        return _build_sprite_aware_collision_rects(
            self.collision_map,
            self.rooms,
            self.hallways,
            self.prefabs,
            self.main_room_prefabs,
            self.hallway_prefabs_upways,
            self.hallway_prefabs_sideways,
            self.sprites,
            active_tile_size,
        )


# API for Generating Hub
class HubGen:
    def __init__(self, hub_path="hub"):
        self.hub_path = hub_path
        self.loaded = False
        self.generated = False

        self.room_prefabs = []
        self.wall_prefabs = []
        self.sprites = {"obstacles": {}, "bases": {}, "walls": {}}

        self.tiles = {}
        self.rooms = []
        self.hallways = []
        self.collision_map = {}

        self.tile_size = 4
        self.cam_x = 0
        self.cam_y = 0

    def _resolve_hub_path(self):
        if os.path.isdir(self.hub_path):
            return self.hub_path

        alt_path = os.path.join("dungeon_types", self.hub_path)
        if os.path.isdir(alt_path):
            return alt_path

        return None

    def _load_sprites(self, root_path):
        from dungeongen.loading import load_sprite

        sprites = {"obstacles": {}, "bases": {}, "walls": {}}
        for layer in sprites.keys():
            layer_path = os.path.join(root_path, "sprites", layer)
            if not os.path.isdir(layer_path):
                continue
            for filename in sorted(os.listdir(layer_path)):
                if not (filename.endswith(".png") or filename.endswith(".jpg")):
                    continue
                sprite_id = filename.rsplit(".", 1)[0]
                sprite = load_sprite(os.path.join(layer_path, filename))
                if sprite is not None:
                    sprites[layer][sprite_id] = sprite
        return sprites

    def load_hub_assets(self):
        from dungeongen.loading import load_prefab

        resolved = self._resolve_hub_path()
        if resolved is None:
            print("Hub path not found:", self.hub_path)
            return

        self.room_prefabs = []
        self.wall_prefabs = []

        # Prefer base_room_prefabs (large hub-style rooms); fall back to room_prefabs.
        room_prefab_dir = os.path.join(resolved, "prefabs", "base_room_prefabs")
        if not os.path.isdir(room_prefab_dir):
            room_prefab_dir = os.path.join(resolved, "prefabs", "room_prefabs")
        wall_prefab_dir = os.path.join(resolved, "prefabs", "base_room_wall_prefabs")
        if not os.path.isdir(wall_prefab_dir):
            wall_prefab_dir = os.path.join(resolved, "prefabs", "wall_prefabs")

        if os.path.isdir(room_prefab_dir):
            for filename in sorted(os.listdir(room_prefab_dir)):
                if filename.endswith(".prefab"):
                    prefab = load_prefab(os.path.join(room_prefab_dir, filename))
                    if prefab is not None:
                        self.room_prefabs.append(prefab)

        if os.path.isdir(wall_prefab_dir):
            for filename in sorted(os.listdir(wall_prefab_dir)):
                if filename.endswith(".prefab"):
                    prefab = load_prefab(os.path.join(wall_prefab_dir, filename))
                    if prefab is not None:
                        self.wall_prefabs.append(prefab)

        self.sprites = self._load_sprites(resolved)
        self.loaded = True

    def load_all_assets(self):
        self.load_hub_assets()

    def _build_collision_map(self, room, room_prefab):
        collision_map = {}

        if room_prefab is None:
            return collision_map

        # Build floor footprint from BASE so collision follows real shape (supports notches/holes).
        footprint = set()
        for local_y in range(len(room_prefab.base)):
            for local_x in range(len(room_prefab.base[local_y])):
                if room_prefab.base[local_y][local_x] == ".":
                    continue
                world_x = room.rect.x + local_x
                world_y = room.rect.y + local_y
                footprint.add((world_x, world_y))
                collision_map[(world_x, world_y)] = "."

        # Apply collision-layer blockers only where floor actually exists.
        for local_y in range(len(room_prefab.collision)):
            for local_x in range(len(room_prefab.collision[local_y])):
                world_x = room.rect.x + local_x
                world_y = room.rect.y + local_y
                if (world_x, world_y) not in footprint:
                    continue
                cell = room_prefab.collision[local_y][local_x]
                if cell != ".":
                    collision_map[(world_x, world_y)] = cell

        # Outline the footprint with blocking border tiles.
        border_tiles = set()
        for (x, y) in footprint:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in footprint:
                    border_tiles.add(neighbor)

        for x, y in border_tiles:
            collision_map[(x, y)] = "#"

        return collision_map

    def form_room(self, room_prefab_index=0, wall_prefab_index=0):
        if not self.loaded:
            self.load_hub_assets()

        if not self.room_prefabs:
            print("No room prefabs found for hub.")
            return

        if room_prefab_index < 0 or room_prefab_index >= len(self.room_prefabs):
            room_prefab_index = 0

        room_prefab = self.room_prefabs[room_prefab_index]
        room_h = len(room_prefab.base)
        room_w = len(room_prefab.base[0]) if room_h > 0 else 1

        # Use positive coordinates instead of negative center positioning
        room_rect = Rect(0, 0, room_w, room_h)
        room = HubRoom(room_rect, prefab_id=room_prefab_index)

        if self.wall_prefabs:
            if wall_prefab_index < 0 or wall_prefab_index >= len(self.wall_prefabs):
                wall_prefab_index = 0
            room.wall_prefab_id = wall_prefab_index

        self.tiles = {}
        for y in range(room_rect.y, room_rect.y + room_rect.h):
            for x in range(room_rect.x, room_rect.x + room_rect.w):
                self.tiles[(x, y)] = "."

        self.rooms = [room]
        self.hallways = []
        self.collision_map = self._build_collision_map(room, room_prefab)

        self.generated = True
        from dungeongen.config import SCREEN_W, SCREEN_H
        # Center camera on the room center for positive coordinates
        self.cam_x = room.center[0] * self.tile_size - SCREEN_W // 2
        self.cam_y = room.center[1] * self.tile_size - SCREEN_H // 2

    def load_complete(self, tile_size):
        # Complete loading and setup for gameplay
        if not self.loaded:
            self.load_all_assets()
        
        self.generate_hub_room()
        
        # Handle all collision and trigger setup
        from src.collision import clear_temporary_walls, update_collision_walls
        from dungeongen.loading import parse_triggers_from_prefab
        
        clear_temporary_walls()
        
        # Parse triggers from room prefabs (all hub rooms are base rooms)
        for room in self.rooms:
            if room.prefab_id is not None:
                if room.prefab_id < len(self.room_prefabs):
                    prefab = self.room_prefabs[room.prefab_id]
                    parse_triggers_from_prefab(room, prefab, tile_size)
        
        # Get collision walls and update collision system
        walls = self.get_collision_rects(tile_size=tile_size)
        update_collision_walls(walls)
        
        # Get spawn position
        if self.rooms:
            cx, cy = self.rooms[0].center  
            spawn = (cx * tile_size, cy * tile_size)
        else:
            spawn = (0, 0)
            
        return spawn

    def generate_hub_room(self, room_prefab_index=0, wall_prefab_index=0):
        self.form_room(room_prefab_index, wall_prefab_index)

    def draw(self, surface=None, tile_size=None, cam_x=None, cam_y=None, show_sprites=True, show_collision_map=False, show_grid=False):
        from dungeongen.rendering import draw_grid

        if not self.generated:
            print("Hub room has not been formed yet.")
            return

        if surface is None:
            target_surface = pygame.display.get_surface()
        else:
            target_surface = surface

        if target_surface is None:
            print("No pygame surface to draw on.")
            return

        if tile_size is None:
            active_tile_size = self.tile_size
        else:
            active_tile_size = tile_size

        if cam_x is None:
            active_cam_x = self.cam_x
        else:
            active_cam_x = cam_x

        if cam_y is None:
            active_cam_y = self.cam_y
        else:
            active_cam_y = cam_y

        self.tile_size = active_tile_size
        self.cam_x = active_cam_x
        self.cam_y = active_cam_y

        draw_grid(
            target_surface,
            self.tiles,
            active_tile_size,
            active_cam_x,
            active_cam_y,
            show_grid,
            target_surface.get_width(),
            target_surface.get_height(),
            self.rooms,
            self.hallways,
            None,  # prefabs (for non-base rooms)
            None,  # wall_prefabs (for non-base rooms)
            self.room_prefabs,  # main_room_prefabs (for base rooms)
            self.wall_prefabs,  # main_room_wall_prefabs (for base rooms)
            None,
            None,
            None,
            self.sprites,
            show_sprites,
        )

        if not show_collision_map:
            return

        start_x = active_cam_x // active_tile_size
        start_y = active_cam_y // active_tile_size
        end_x = (active_cam_x + target_surface.get_width()) // active_tile_size + 1
        end_y = (active_cam_y + target_surface.get_height()) // active_tile_size + 1

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if (x, y) not in self.collision_map:
                    continue
                if self.collision_map[(x, y)] == ".":
                    continue

                rect = pygame.Rect(
                    x * active_tile_size - active_cam_x,
                    y * active_tile_size - active_cam_y,
                    active_tile_size,
                    active_tile_size,
                )
                pygame.draw.rect(target_surface, (255, 0, 0, 128), rect)

    def get_collision_rects(self, tile_size=None):
        if tile_size is None:
            active_tile_size = self.tile_size
        else:
            active_tile_size = tile_size

        return _build_sprite_aware_collision_rects(
            self.collision_map,
            self.rooms,
            self.hallways,
            self.room_prefabs,
            [],
            [],
            [],
            self.sprites,
            active_tile_size,
        )
