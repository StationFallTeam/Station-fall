import os
import pygame
from classes import Prefab
from config import BASE_ROOM_SIZE, ROOM_SIZE, HALL_LENGTH, HALL_THICKNESS, WALL_HEIGHT


def _normalize_tile_token(token):
    token = token.strip()
    if token == "" or token == ".":
        return "."
    lower = token.lower()
    if lower.endswith(".png") or lower.endswith(".jpg"):
        token = token.rsplit('.', 1)[0]
    return token


def _parse_prefab_row(line):
    return [_normalize_tile_token(part) for part in line.split(",")]


def _rectangularize(rows):
    if not rows:
        return rows
    width = max(len(row) for row in rows)
    out = []
    for row in rows:
        if len(row) < width:
            out.append(row + ["."] * (width - len(row)))
        else:
            out.append(row)
    return out


def load_prefab(filepath: str):
    try:
        prefab_name = os.path.splitext(os.path.basename(filepath))[0]
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
                current_data.append(_parse_prefab_row(line))
        
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
        
        # Normalize grids to consistent row width.
        for key in list(sections.keys()):
            sections[key] = _rectangularize(sections[key])

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
            sections['COLLISION'] = [["."] * width for _ in range(size)]
        if 'OBSTACLE' not in sections or len(sections['OBSTACLE']) == 0:
            sections['OBSTACLE'] = [["."] * width for _ in range(size)]
        
        # Map to BASE for the Prefab class
        if 'WALL' in sections and 'BASE' not in sections:
            sections['BASE'] = sections['WALL']
        
        return Prefab(
            sections['COLLISION'],
            sections['OBSTACLE'],
            sections['BASE'],
            prefab_name,
        )
    except Exception as e:
        print(f"Failed to load prefab {filepath}: {e}")
        return None


def validate_dungeon_type(dungeon_type: str, base_path: str = "dungeon_types"):
    type_path = os.path.join(base_path, dungeon_type)
    
    # Check required prefab directories
    required_prefab_dirs = [
        'prefabs/room_prefabs',
        'prefabs/wall_prefabs',
        'prefabs/hallway_prefabs/upways',
        'prefabs/hallway_prefabs/sideways',
        'prefabs/hallway_wall_prefabs/sideways',
    ]
    
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
        ('prefabs/wall_prefabs', None),
        ('prefabs/hallway_prefabs/upways', (HALL_THICKNESS, HALL_LENGTH)),
        ('prefabs/hallway_prefabs/sideways', (HALL_LENGTH, HALL_THICKNESS)),
        ('prefabs/hallway_wall_prefabs/sideways', None),
    ]
    
    # Validate only core dungeon prefabs for type validity.
    # Base-room prefab sets are optional and may contain hub-only tiles.
    for prefab_dir, expected_size in prefab_checks:
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
                    if expected_size is not None and (width, height) != expected_size:
                        print(f"Invalid dimensions in {filepath}: expected {expected_size}, got ({width}, {height})")
                        return False
                    
                    # All layers must have same dimensions
                    for layer in [prefab.collision, prefab.obstacle]:
                        layer_height = len(layer)
                        layer_width = len(layer[0]) if layer else 0
                        if expected_size is not None:
                            if (layer_width, layer_height) != expected_size:
                                print(f"Mismatched layer dimensions in {filepath}")
                                return False
                        else:
                            if (layer_width, layer_height) != (width, height):
                                print(f"Mismatched layer dimensions in {filepath}")
                                return False
                    
                    # Collect non-empty tile characters only from rendered layers.
                    # Collision markers (e.g. X, #) are logic-only and should not require sprites.
                    for layer in [prefab.obstacle, prefab.base]:
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


def find_dungeon_types(base_path: str = "dungeon_types"):
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


def load_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_main_room_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_main_room_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_hallway_prefabs(dungeon_type: str, direction: str, base_path: str = "dungeon_types"):
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


def load_all_hallway_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
    return {
        'upways': load_hallway_prefabs(dungeon_type, 'upways', base_path),
        'sideways': load_hallway_prefabs(dungeon_type, 'sideways', base_path),
    }


def load_hallway_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_all_hallway_wall_prefabs(dungeon_type: str, base_path: str = "dungeon_types"):
    return {
        'sideways': load_hallway_wall_prefabs(dungeon_type, base_path),
    }



def load_sprite(sprite_path: str):
    try:
        return pygame.image.load(sprite_path)
    except Exception as e:
        print(f"Failed to load sprite {sprite_path}: {e}")
        return None


def load_sprites_for_dungeon_type(dungeon_type: str, base_path: str = "dungeon_types"):
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


def load_preset(filename: str, directory: str = "dungeon_gen_presets"):
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


def find_presets(directory: str = "dungeon_gen_presets"):
    presets = []
    try:
        for file in sorted(os.listdir(directory)):
            if file.endswith(".txt") and file not in ["README.txt", "gen_presets.txt"]:
                presets.append(file)
    except OSError:
        pass
    return presets
