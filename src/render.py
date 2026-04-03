import pygame
from src.ui import draw_health_bar, draw_money
from dungeongen.classes import CombatRoom

def draw_objects(win, player, enemies, bullets, camera, background, coins, floating_texts, dungeon, tile_size):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # 2. Draw dungeon or walls
    if dungeon and dungeon.draw:
        # Use dungeon rendering pipeline instead of manual walls
        # Use provided tile_size or fall back to dungeon's tile_size
        render_tile_size = tile_size or dungeon.tile_size
        dungeon.draw(
            surface=win,
            tile_size=render_tile_size,
            cam_x=-camera.camera.x,
            cam_y=-camera.camera.y,
            show_grid=False,
            show_sprites=True,
        )
    
    if dungeon and dungeon.rooms and tile_size:
        # Let each combat room draw its own spawn warnings
        for room in dungeon.rooms:
            if isinstance(room, CombatRoom):
                room.draw_spawn_warnings(win, camera, tile_size)

    # 3. Draw entities relative to camera
    for coin in coins:
        coin.draw(win, camera)

    for bullet in bullets: 
        bullet.draw(win, camera)

    for enemy in enemies:
        enemy.draw(win, camera)

    # 4. Draw the player (passing camera for offset)
    player.draw(win, camera)

    # 5. Draw Floating Action Text (Damage numbers, etc.)
    # We draw these after entities so they appear on top of characters
    for ft in floating_texts:
        ft.draw(win, camera)

    # 6. Draw Fixed HUD elements (Screen Space)
    # Player HUD health bar
    draw_health_bar(win, player.health, player.max_health, 20, 20, 250, 18)
    draw_money(win, player.money, 20, 50)

    # 7. Draw hovering enemy health bars (World Space)
    for enemy in enemies:
        screen_rect = camera.apply(enemy.rect)
        
        draw_health_bar(
            win,
            enemy.health,
            enemy.max_health,
            screen_rect.x,
            screen_rect.y - 10,
            screen_rect.width,
            6,
            border=1
        )

def apply_brightness(win, brightness):
    if brightness >= 1.0:
        return
    
    darkness = int((1.0 - brightness) * 255)
    
    overlay = pygame.Surface(win.get_size())
    overlay.fill((0, 0, 0))
    overlay.set_alpha(darkness)

    win.blit(overlay, (0, 0))