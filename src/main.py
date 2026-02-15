import pygame
from background import SpaceBackground
from camera import Camera
from enemy import Enemy
from player import Player
from render import draw_objects

pygame.init()

screen_width = 500
screen_height = 500
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Station Fall Playtest")

clock = pygame.time.Clock()

# Initialize the Camera and Background systems
camera = Camera(screen_width, screen_height)
space_bg = SpaceBackground(screen_width, screen_height)

player = Player(100, 100)
enemies = [Enemy(300, 300)]

run = True
while run:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()

    # Update Player: I increased the bounds to 5000 so you can move around
    player.update(keys, 5000, 5000)

    # Update Camera to track the player's new position
    camera.update(player)

    # Update Enemies
    for enemy in enemies:
        enemy.update(player.get_rect())

    # --- DRAWING ---
    # Draw Background (Parallax uses the camera's top-left)
    space_bg.update_and_draw(win, camera.camera.topleft)

    # Draw player and enemies using the camera offset
    draw_objects(win, player, enemies, camera)

    pygame.display.update()

pygame.quit()