import pygame
from background import SpaceBackground
from camera import Camera
from enemy import Enemy
from player import Player
from render import draw_objects

pygame.init()

# Get monitor resolution
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
win = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

clock = pygame.time.Clock()

# Set a large world (e.g., 5000x5000) so there is space to scroll
world_width, world_height = 5000, 5000

camera = Camera(screen_width, screen_height)
space_bg = SpaceBackground(screen_width, screen_height)

player = Player(screen_width // 2, screen_height // 2)
enemies = [Enemy(800, 800), Enemy(1200, 300)]

run = True
while run:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False

    keys = pygame.key.get_pressed()

    # 1. Update World Objects
    player.update(keys, world_width, world_height)
    for enemy in enemies:
        enemy.update(player.get_rect())

    # 2. Update Camera (Follows Player)
    camera.update(player)

    # 3. Render
    # Background uses camera position for the parallax effect
    space_bg.update_and_draw(win, camera.camera.topleft)
    
    # Draw player/enemies through the 'lens' of the camera
    draw_objects(win, player, enemies, camera)

    pygame.display.update()

pygame.quit()