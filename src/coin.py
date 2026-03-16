import pygame

class Coin: 
    def __init__(self, x, y, value = 1):
        self.value = value
        self.radius = 8
        self.color = (255, 215, 0)
        self.pos = pygame.Vector2(x,y)

        self.rect = pygame.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius), 
            self.radius * 2, 
            self.radius * 2
        )

    def update(self):
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, screen, camera):
        screen_pos = camera.apply(self.rect).center

        pygame.draw.circle(screen, (255, 200, 0), screen_pos, self.radius)
        pygame.draw.circle(screen, (255, 240, 120), screen_pos, self.radius-3)
        