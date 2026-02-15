import pygame
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'other_folder'))

from enemy import Enemy
from player import Player
from render import draw_objects

pygame.init()
pygame.mixer.init()

screen_width = 500
screen_height = 500
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Station Fall Playtest")

clock = pygame.time.Clock()

player = Player(100, 100)
enemies = [Enemy(300, 300)]

run = True
while run:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False

    keys = pygame.key.get_pressed()

    # Update player
    player.update(keys, screen_width, screen_height)

    # Update enemy using player's rect
    for enemy in enemies:
        enemy.update(player.get_rect())

    # Draw everything
    win.fill((0, 0, 0))
    draw_objects(win, player, enemies)

    pygame.display.update()

pygame.quit()

