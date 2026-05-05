import asyncio

import pygame

from dungeongen.loading import (
    get_available_dungeon_types,
    get_available_presets,
    create_hub_generator,
    create_dungeon_generator,
)
from dungeongen.rendering import COLOR_BG, COLOR_TEXT, COLOR_FURTHEST, COLOR_DOOR_DOT, draw_minimap
from dungeongen.config import (
    ROOM_SIZE,
    SCREEN_W,
    SCREEN_H,
    TILE_SIZE_START,
    TILE_SIZE_MIN,
    TILE_SIZE_MAX,
    CAMERA_SPEED,
)

async def main():
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

    # Load dungeon types and presets
    available_dungeon_types = get_available_dungeon_types()
    dungeon_type_index = 0
    current_dungeon_type = available_dungeon_types[dungeon_type_index] if available_dungeon_types else "station"

    available_presets = get_available_presets()
    preset_index = 0
    current_preset = available_presets[preset_index] if available_presets else "long.txt"

    dungeon = create_dungeon_generator()
    dungeon.load_all_assets()

    def print_loaded_assets():
        print(f"Loaded dungeon type: {current_dungeon_type}")
        print(f"  Room prefabs: {len(dungeon.prefabs)}")
        print(f"  Wall prefabs: {len(dungeon.wall_prefabs)}")
        print(f"  Base room prefabs: {len(dungeon.main_room_prefabs)}")
        print(f"  Base room wall prefabs: {len(dungeon.main_room_wall_prefabs)}")
        print(f"  Upways hallway prefabs: {len(dungeon.hallway_prefabs_upways)}")
        print(f"  Sideways hallway prefabs: {len(dungeon.hallway_prefabs_sideways)}")
        print(f"  Sideways hallway wall prefabs: {len(dungeon.hallway_wall_prefabs_sideways)}")

    dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
    print_loaded_assets()
    cam_x, cam_y = dungeon.cam_x, dungeon.cam_y

    hub = create_hub_generator("hub")
    active_generator = dungeon
    active_mode = "dungeon"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    if active_mode == "hub":
                        hub.generate_hub_room()
                        active_generator = hub
                        cam_x, cam_y = hub.cam_x, hub.cam_y
                    else:
                        dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
                        active_generator = dungeon
                        cam_x, cam_y = dungeon.cam_x, dungeon.cam_y
                elif event.key == pygame.K_p:
                    dungeon.params['ALLOW_HALLWAY_THROUGH_ROOMS'] = not dungeon.params['ALLOW_HALLWAY_THROUGH_ROOMS']
                    dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
                    active_generator = dungeon
                    active_mode = "dungeon"
                    cam_x, cam_y = dungeon.cam_x, dungeon.cam_y
                elif event.key == pygame.K_v:
                    dungeon.params['GENERATE_VERTICAL_FIRST'] = not dungeon.params['GENERATE_VERTICAL_FIRST']
                    dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
                    active_generator = dungeon
                    active_mode = "dungeon"
                    cam_x, cam_y = dungeon.cam_x, dungeon.cam_y
                elif event.key == pygame.K_l:
                    if available_presets:
                        preset_index = (preset_index + 1) % len(available_presets)
                        current_preset = available_presets[preset_index]
                        dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
                        active_generator = dungeon
                        active_mode = "dungeon"
                        cam_x, cam_y = dungeon.cam_x, dungeon.cam_y
                elif event.key == pygame.K_t:
                    if available_dungeon_types:
                        dungeon_type_index = (dungeon_type_index + 1) % len(available_dungeon_types)
                        current_dungeon_type = available_dungeon_types[dungeon_type_index]
                        dungeon.generate_dungeon_specific(current_dungeon_type, current_preset)
                        print_loaded_assets()
                        active_generator = dungeon
                        active_mode = "dungeon"
                        cam_x, cam_y = dungeon.cam_x, dungeon.cam_y
                elif event.key == pygame.K_h:
                    hub.generate_hub_room()
                    if hub.generated:
                        active_generator = hub
                        active_mode = "hub"
                        cam_x, cam_y = hub.cam_x, hub.cam_y
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
        active_generator.draw(
            surface=screen,
            tile_size=tile_size,
            cam_x=cam_x,
            cam_y=cam_y,
            show_sprites=show_sprites,
            show_collision_map=show_collision,
            show_grid=show_grid,
              )
        
        
        camera_center_x = cam_x + SCREEN_W / 2
        camera_center_y = cam_y + SCREEN_H / 2
        
        rooms = active_generator.rooms
        hallways = active_generator.hallways
        seed = getattr(active_generator, "seed", None)

        boss_room = next((room for room in rooms if getattr(room, "is_boss_room", False)), None)
        if show_debug and boss_room:
            fx = boss_room.center[0] * tile_size + tile_size // 2 - cam_x
            fy = boss_room.center[1] * tile_size + tile_size // 2 - cam_y
            min_room_tiles = min(ROOM_SIZE)
            radius = max(3, (min_room_tiles * tile_size) // 4)
            pygame.draw.circle(screen, COLOR_FURTHEST, (fx, fy), radius)

        if show_debug:
            for room in rooms:
                for dx, dy in room.doors:
                    dot_x = dx * tile_size + tile_size // 2 - cam_x
                    dot_y = dy * tile_size + tile_size // 2 - cam_y
                    pygame.draw.circle(screen, COLOR_DOOR_DOT, (dot_x, dot_y), max(2, tile_size // 5))

                if room.is_base_room and room is not boss_room:
                    continue
                label_id = 0 if room is boss_room else room.prefab_id
                px = room.center[0] * tile_size + tile_size // 2 - cam_x
                py = room.center[1] * tile_size + tile_size // 2 - cam_y
                label = font.render(str(label_id), True, COLOR_TEXT)
                rect = label.get_rect(center=(px, py))
                screen.blit(label, rect)

        room_count = sum(1 for room in rooms if not room.is_base_room)
        hallway_count = len(hallways)
        if active_mode == "dungeon":
            gen_order = "vertical→horizontal" if dungeon.params['GENERATE_VERTICAL_FIRST'] else "horizontal→vertical"
            hallway_mode = "through" if dungeon.params['ALLOW_HALLWAY_THROUGH_ROOMS'] else "stop"
            mode_text = f"preset {current_preset} | type {current_dungeon_type}"
        else:
            gen_order = "static"
            hallway_mode = "none"
            mode_text = "hub room"
        
        # Render info on multiple lines
        info_line1 = f"seed {seed} | rooms {room_count} | hallways {hallway_count} | tile {tile_size}px | {gen_order}"
        info_line2 = f"mode {active_mode} | hallway {hallway_mode} | {mode_text}"
        info_line3 = "R regen  H hub  L preset  T type  V order  P penetrate  G grid  S sprites  B debug  C collision  +/- zoom  arrows move"
        
        text1 = font.render(info_line1, True, COLOR_TEXT)
        text2 = font.render(info_line2, True, COLOR_TEXT)
        text3 = font.render(info_line3, True, COLOR_TEXT)
        
        screen.blit(text1, (10, 10))
        screen.blit(text2, (10, 32))
        screen.blit(text3, (10, 54))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
