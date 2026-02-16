import pygame

def draw_objects(win, player, enemies, camera, background):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # 2. Draw the player (passing camera for offset)
    player.draw(win, camera)

    # 3. Draw enemies relative to camera
    for enemy in enemies:
        pygame.draw.rect(win, enemy.color, camera.apply(enemy.rect))