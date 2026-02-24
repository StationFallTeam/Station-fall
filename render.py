import pygame

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