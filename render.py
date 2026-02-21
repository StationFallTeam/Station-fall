import pygame

def draw_objects(win, player, enemies, camera, background, world_width, world_height):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # New: Draw a white boundary rectangle relative to the camera - Meheraj
    world_border = pygame.Rect(0, 0, world_width, world_height)
    pygame.draw.rect(win, (255, 255, 255), camera.apply(world_border), 5)

    # 2. Draw the player (passing camera for offset)
    player.draw(win, camera)

    # 3. Draw enemies relative to camera
    for enemy in enemies:
        enemy.draw(win, camera)