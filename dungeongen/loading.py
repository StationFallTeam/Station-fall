"""Loading functions for prefabs, sprites, and presets."""

import os
import pygame
from classes import Prefab
from config import BASE_ROOM_SIZE, ROOM_SIZE, HALL_LENGTH, HALL_THICKNESS, WALL_HEIGHT


def load_prefab(filepath: str) -> Prefab | None:
    """Load a prefab from a .prefab file.
    
    File format:
    [COLLISION]
    lines of characters
    [OBSTACLE]
    lines of characters
    [BASE] for room prefabs or [WALL] for wall prefabs
    lines of characters
    
    Rule: Wall prefabs MUST use [WALL], room prefabs MUST use [BASE].
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
        
        sections = {}
        current_section = None
        current_data = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                if current_section:
                    sections[current_section] = current_data
                current_section = line[1:-1]
                current_data = []
            elif line and current_section:
                current_data.append(line)
        
        if current_section:
            sections[current_section] = current_data
        
        # Enforce syntax rules based on file location
        is_wall_prefab = 'wall_prefab' in filepath.lower()
        
        if is_wall_prefab:
            # Wall prefabs MUST use [WALL]
            if 'BASE' in sections:
                print(f"Syntax error in {filepath}: Wall prefabs must use [WALL], not [BASE]")
                return None
            if 'WALL' not in sections:
                print(f"Syntax error in {filepath}: Wall prefabs must have [WALL] section")
                return None
        else:
            # Room prefabs MUST use [BASE]
            if 'WALL' in sections:
                print(f"Syntax error in {filepath}: Room prefabs must use [BASE], not [WALL]")
                return None
            if 'BASE' not in sections:
                print(f"Syntax error in {filepath}: Room prefabs must have [BASE] section")
                return None
        
        # Determine which layer to use
        base_layer = sections.get('BASE') or sections.get('WALL')
        
        # Fill in missing sections with empty grids
        if base_layer:
            size = len(base_layer)
            width = len(base_layer[0]) if base_layer else 0
        else:
            size = 9
            width = 9
        
        if 'COLLISION' not in sections or len(sections['COLLISION']) == 0:
            sections['COLLISION'] = ['.' * width for _ in range(size)]
        if 'OBSTACLE' not in sections or len(sections['OBSTACLE']) == 0:
            sections['OBSTACLE'] = ['.' * width for _ in range(size)]
        
        # Map to BASE for the Prefab class
        if 'WALL' in sections and 'BASE' not in sections:
            sections['BASE'] = sections['WALL']
        
        return Prefab(
            sections['COLLISION'],
            sections['OBSTACLE'],
            sections['BASE']
        )
    except Exception as e:
        print(f"Failed to load prefab {filepath}: {e}")
        return None


def validate_dungeon_type(dungeon_type: str, base_path: str = "dungeon_types") -> bool:
    """Validate that a dungeon type has all required folders and valid files."""
    type_path = os.path.join(base_path, dungeon_type)
    
    # Check required prefab directories
    required_prefab_dirs = [
        'prefabs/room_prefabs',
        'prefabs/wall_prefabs',
        'prefabs/hallway_prefabs/upways',
        'prefabs/hallway_prefabs/sideways',
        'prefabs/hallway_wall_prefabs/sideways',
    ]
    
    # Check for base room prefabs (either name works)
    has_base_room = (
        os.path.isdir(os.path.join(type_path, 'prefabs/base_room_prefabs')) or
        os.path.isdir(os.path.join(type_path, 'prefabs/main_room_prefabs'))
    )
    
    # Check for base room wall prefabs (either name works)
    has_base_room_walls = (
        os.path.isdir(os.path.join(type_path, 'prefabs/base_room_wall_prefabs')) or
        os.path.isdir(os.path.join(type_path, 'prefabs/main_room_wall_prefabs'))
    )
    
    if not has_base_room or not has_base_room_walls:
        return False
    
    for dir_path in required_prefab_dirs:
        full_path = os.path.join(type_path, dir_path)
        if not os.path.isdir(full_path):
            return False
    
    # Check required sprite directories
    required_sprite_dirs = ['sprites/obstacles', 'sprites/bases', 'sprites/walls']
    for dir_path in required_sprite_dirs:
        full_path = os.path.join(type_path, dir_path)
        if not os.path.isdir(full_path):
            return False
    
    # Collect all tile characters used in prefabs and validate dimensions
    used_tiles = set()
    prefab_checks = [
        ('prefabs/room_prefabs', ROOM_SIZE),
        ('prefabs/wall_prefabs', (ROOM_SIZE[0], WALL_HEIGHT)),
        ('prefabs/hallway_prefabs/upways', (HALL_THICKNESS, HALL_LENGTH)),
        ('prefabs/hallway_prefabs/sideways', (HALL_LENGTH, HALL_THICKNESS)),
        ('prefabs/hallway_wall_prefabs/sideways', (HALL_LENGTH, WALL_HEIGHT)),
    ]
    
    # Add base room directories with their expected dimensions
    base_room_checks = []
    if os.path.isdir(os.path.join(type_path, 'prefabs/base_room_prefabs')):
        base_room_checks.append(('prefabs/base_room_prefabs', BASE_ROOM_SIZE))
    if os.path.isdir(os.path.join(type_path, 'prefabs/main_room_prefabs')):
        base_room_checks.append(('prefabs/main_room_prefabs', BASE_ROOM_SIZE))
    if os.path.isdir(os.path.join(type_path, 'prefabs/base_room_wall_prefabs')):
        base_room_checks.append(('prefabs/base_room_wall_prefabs', (BASE_ROOM_SIZE[0], WALL_HEIGHT)))
    if os.path.isdir(os.path.join(type_path, 'prefabs/main_room_wall_prefabs')):
        base_room_checks.append(('prefabs/main_room_wall_prefabs', (BASE_ROOM_SIZE[0], WALL_HEIGHT)))
    
    # Validate all prefabs
    for prefab_dir, expected_size in prefab_checks + base_room_checks:
        prefab_path = os.path.join(type_path, prefab_dir)
        try:
            for filename in os.listdir(prefab_path):
                if filename.endswith('.prefab'):
                    filepath = os.path.join(prefab_path, filename)
                    prefab = load_prefab(filepath)
                    if prefab is None:
                        return False  # Invalid prefab file format
                    
                    # Validate dimensions
                    height = len(prefab.base)
                    width = len(prefab.base[0]) if prefab.base else 0
                    if (width, height) != expected_size:
                        print(f"Invalid dimensions in {filepath}: expected {expected_size}, got ({width}, {height})")
                        return False
                    
                    # All layers must have same dimensions
                    for layer in [prefab.collision, prefab.obstacle]:
                        layer_height = len(layer)
                        layer_width = len(layer[0]) if layer else 0
                        if (layer_width, layer_height) != expected_size:
                            print(f"Mismatched layer dimensions in {filepath}")
                            return False
                    
                    # Collect all non-empty tile characters from all layers
                    for layer in [prefab.collision, prefab.obstacle, prefab.base]:
                        for row in layer:
                            for char in row:
                                if char not in ('.', ' ', ''):
                                    used_tiles.add(char)
        except OSError:
            return False
    
    # Load available sprites
    available_sprites = set()
    for sprite_dir in ['sprites/obstacles', 'sprites/bases', 'sprites/walls']:
        sprite_path = os.path.join(type_path, sprite_dir)
        try:
            for filename in os.listdir(sprite_path):
                if filename.endswith('.png') or filename.endswith('.jpg'):
                    sprite_id = filename.rsplit('.', 1)[0]
                    available_sprites.add(sprite_id)
        except OSError:
            return False
    
    # Check that all used tiles have corresponding sprites
    for tile in used_tiles:
        if tile not in available_sprites:
            print(f"Missing sprite for tile '{tile}' in dungeon type '{dungeon_type}'")
            return False
    
    return True


def find_dungeon_types(base_path: str = "dungeon_types") -> list[str]:
    """Find all valid dungeon types with complete assets."""
    types = []
    try:
        if os.path.isdir(base_path):
            for item in sorted(os.listdir(base_path)):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    if validate_dungeon_type(item, base_path):
                        types.append(item)
    except OSError:
        pass
    return types


def load_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load all room prefabs from a dungeon type."""
    prefabs = []
    prefabs_path = os.path.join(base_path, dungeon_type, 'prefabs', 'room_prefabs')
    
    try:
        for filename in sorted(os.listdir(prefabs_path)):
            if filename.endswith('.prefab'):
                filepath = os.path.join(prefabs_path, filename)
                prefab = load_prefab(filepath)
                if prefab:
                    prefabs.append(prefab)
    except OSError:
        pass
    
    return prefabs


def load_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load all wall prefabs from a dungeon type."""
    prefabs = []
    prefabs_path = os.path.join(base_path, dungeon_type, 'prefabs', 'wall_prefabs')
    
    try:
        for filename in sorted(os.listdir(prefabs_path)):
            if filename.endswith('.prefab'):
                filepath = os.path.join(prefabs_path, filename)
                prefab = load_prefab(filepath)
                if prefab:
                    prefabs.append(prefab)
    except OSError:
        pass
    
    return prefabs


def load_main_room_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load all base room prefabs from a dungeon type."""
    prefabs = []
    candidate_dirs = [
        os.path.join(base_path, dungeon_type, 'prefabs', 'base_room_prefabs'),
        os.path.join(base_path, dungeon_type, 'prefabs', 'main_room_prefabs'),
    ]

    for prefabs_path in candidate_dirs:
        try:
            for filename in sorted(os.listdir(prefabs_path)):
                if filename.endswith('.prefab'):
                    filepath = os.path.join(prefabs_path, filename)
                    prefab = load_prefab(filepath)
                    if prefab:
                        prefabs.append(prefab)
            if prefabs:
                break
        except OSError:
            continue

    return prefabs


def load_main_room_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load all base room wall prefabs from a dungeon type."""
    prefabs = []
    candidate_dirs = [
        os.path.join(base_path, dungeon_type, 'prefabs', 'base_room_wall_prefabs'),
        os.path.join(base_path, dungeon_type, 'prefabs', 'main_room_wall_prefabs'),
    ]

    for prefabs_path in candidate_dirs:
        try:
            for filename in sorted(os.listdir(prefabs_path)):
                if filename.endswith('.prefab'):
                    filepath = os.path.join(prefabs_path, filename)
                    prefab = load_prefab(filepath)
                    if prefab:
                        prefabs.append(prefab)
            if prefabs:
                break
        except OSError:
            continue

    return prefabs


def load_hallway_prefabs(dungeon_type: str, direction: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load hallway prefabs for a specific direction (upways or sideways)."""
    prefabs = []
    prefabs_path = os.path.join(base_path, dungeon_type, 'prefabs', 'hallway_prefabs', direction)
    
    try:
        for filename in sorted(os.listdir(prefabs_path)):
            if filename.endswith('.prefab'):
                filepath = os.path.join(prefabs_path, filename)
                prefab = load_prefab(filepath)
                if prefab:
                    prefabs.append(prefab)
    except OSError:
        pass
    
    return prefabs


def load_all_hallway_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> dict[str, list[Prefab]]:
    """Load all hallway prefabs organized by direction."""
    return {
        'upways': load_hallway_prefabs(dungeon_type, 'upways', base_path),
        'sideways': load_hallway_prefabs(dungeon_type, 'sideways', base_path),
    }


def load_hallway_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> list[Prefab]:
    """Load hallway wall prefabs (sideways-only)."""
    prefabs = []
    prefabs_path = os.path.join(base_path, dungeon_type, 'prefabs', 'hallway_wall_prefabs', 'sideways')
    
    try:
        for filename in sorted(os.listdir(prefabs_path)):
            if filename.endswith('.prefab'):
                filepath = os.path.join(prefabs_path, filename)
                prefab = load_prefab(filepath)
                if prefab:
                    prefabs.append(prefab)
    except OSError:
        pass
    
    return prefabs


def load_all_hallway_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types") -> dict[str, list[Prefab]]:
    """Load hallway wall prefabs (sideways-only)."""
    return {
        'sideways': load_hallway_wall_prefabs(dungeon_type, base_path),
    }



def load_sprite(sprite_path: str) -> pygame.Surface | None:
    """Load a sprite image and return it as a pygame Surface."""
    try:
        return pygame.image.load(sprite_path)
    except Exception as e:
        print(f"Failed to load sprite {sprite_path}: {e}")
        return None


def load_sprites_for_dungeon_type(dungeon_type: str, base_path: str = "dungeon_types") -> dict[str, dict[str, pygame.Surface]]:
    """Load all sprites for a dungeon type. Returns dict with 'obstacles', 'bases', and 'walls' keys."""
    sprites = {'obstacles': {}, 'bases': {}, 'walls': {}}
    
    for layer in sprites.keys():
        layer_path = os.path.join(base_path, dungeon_type, 'sprites', layer)
        if os.path.isdir(layer_path):
            for filename in sorted(os.listdir(layer_path)):
                if filename.endswith('.png') or filename.endswith('.jpg'):
                    sprite_id = filename.rsplit('.', 1)[0]  # Get name without extension
                    sprite_surface = load_sprite(os.path.join(layer_path, filename))
                    if sprite_surface:
                        sprites[layer][sprite_id] = sprite_surface
    
    return sprites


def load_preset(filename: str, directory: str = "dungeon_gen_presets") -> dict:
    """Load a configuration preset from a file."""
    preset = {}
    try:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
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
        print(f"Preset file '{filename}' not found in {directory}")
    return preset


def find_presets(directory: str = "dungeon_gen_presets") -> list[str]:
    """Find all .txt preset files in the dungeon_gen_presets directory, excluding README.txt and gen_presets.txt."""
    presets = []
    try:
        for file in sorted(os.listdir(directory)):
            if file.endswith(".txt") and file not in ["README.txt", "gen_presets.txt"]:
                presets.append(file)
    except OSError:
        pass
    return presets
