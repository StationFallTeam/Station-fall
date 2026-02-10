import pygame
from enemy import Enemy
from player import Player

pygame.init()
pygame.mixer.init()

screen_width = 500
screen_height = 500
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Clean Game Structure")

clock = pygame.time.Clock()

player = Player(100, 100)
enemy = Enemy(300, 300)

run = True
while run:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()

    # Update player
    player.update(keys, screen_width, screen_height)

    # Update enemy using player's rect
    enemy.update(player.get_rect())

    # Draw everything
    win.fill((0, 0, 0))
    player.draw(win)
    enemy.draw(win)

    pygame.display.update()

pygame.quit()
