import pygame
from .ui import draw_health_bar

def draw_objects(win, player, enemies, walls, camera, background):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # Draw walls
    for wall in walls:
        pygame.draw.rect(win, (180, 160, 70), camera.apply(wall))

    # 2. Draw the player (passing camera for offset)
    player.draw(win, camera)

    # 3. Draw enemies relative to camera
    for enemy in enemies:
        enemy.draw(win, camera)

    # Player HUD health bar (fixed on screen)
    draw_health_bar(win, player.health, player.max_health, 20, 20, 250, 18)

    # draw hovering enemy health bars
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