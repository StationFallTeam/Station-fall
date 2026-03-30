import pygame
from .ui import draw_health_bar, draw_money

def draw_objects(win, player, enemies, bullets, walls, camera, background, coins, floating_texts):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # 2. Draw walls
    for wall in walls:
        pygame.draw.rect(win, (180, 160, 70), camera.apply(wall))

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