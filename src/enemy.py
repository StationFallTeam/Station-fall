import pygame

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 40
        self.speed = 2 # Note: If player speed is 5, player is faster!
        self.color = (200, 50, 50)
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def update(self, player_rect):
        # Move towards player's center in World Space
        if player_rect.centerx > self.rect.centerx:
            self.x += self.speed
        elif player_rect.centerx < self.rect.centerx:
            self.x -= self.speed
            
        if player_rect.centery > self.rect.centery:
            self.y += self.speed
        elif player_rect.centery < self.rect.centery:
            self.y -= self.speed

        # Update the rect used for drawing and collisions
        self.rect.topleft = (self.x, self.y)

    def draw(self, win, camera):
        # This is handled by render.py now, but keeping for reference
        win.blit(self.image, camera.apply(self.rect))