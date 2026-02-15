import pygame
from background import SpaceBackground
from camera import Camera
from enemy import Enemy
from player import Player
from render import draw_objects

pygame.init()
pygame.mixer.init()

# Get the current display size for fullscreen mode
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# Use pygame.FULLSCREEN for a true big-screen experience
# Or use pygame.RESIZABLE if you want a window you can maximize
win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Station Fall Playtest")

clock = pygame.time.Clock()

# Define a large world size for the player to explore
world_width = 5000
world_height = 5000

camera = Camera(screen_width, screen_height)
space_bg = SpaceBackground(screen_width, screen_height)

player = Player(100, 100)
enemies = [Enemy(300, 300), Enemy(800, 600)]

run = True
while run:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Allow quitting with ESC key
                run = False

    keys = pygame.key.get_pressed()

    # Update player with world boundaries
    player.update(keys, world_width, world_height)

    # Update camera to follow player
    camera.update(player)

    # Update enemies
    for enemy in enemies:
        enemy.update(player.get_rect())

    # Clear the screen and draw everything
    # Draw the background first, using the camera position for parallax effect
    space_bg.update_and_draw(win, camera.camera.topleft)

    # Then draw the player and enemies on top
    draw_objects(win, player, enemies, camera)

    pygame.display.update()

pygame.quit()