import pygame

def draw_objects(win, player, enemies):
    player.draw(win)

    for enemy in enemies:
        enemy.draw(win)
