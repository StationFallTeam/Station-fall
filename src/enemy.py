import pygame
import random

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 40
        self.speed = 2
        self.color = (200, 50, 50)

        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def update(self, player_rect):

        if player_rect.x > self.x:
            self.x += self.speed
        if player_rect.x < self.x:
            self.x -= self.speed
        if player_rect.y > self.y:
            self.y += self.speed
        if player_rect.y < self.y:
            self.y -= self.speed

        self.rect.topleft = (self.x, self.y)

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)