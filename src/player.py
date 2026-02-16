import pygame

class Player:
    def __init__(self, x, y):
        # The rect represents the player's position in the "World"
        self.rect = pygame.Rect(x, y, 40, 40)
        self.speed = 5
        self.color = (50, 200, 50)

    def update(self, keys, sw, sh):
        if keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_d]: self.rect.x += self.speed
        if keys[pygame.K_w]: self.rect.y -= self.speed
        if keys[pygame.K_s]: self.rect.y += self.speed

    def get_rect(self):
        return self.rect

    def draw(self, win, camera):
        # camera.apply converts world coordinates to screen coordinates
        pygame.draw.rect(win, self.color, camera.apply(self))