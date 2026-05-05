import pygame

class HealthDrop:
    def __init__(self, x, y, heal_amount):
        self.heal_fraction = max(0, heal_amount) / 100
        self.radius = 8
        self.pos = pygame.Vector2(x, y)

        self.rect = pygame.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def heal_for(self, player):
        return max(1, int(round(player.max_health * self.heal_fraction)))

    def update(self):
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, screen, camera):
        screen_pos = camera.apply(self.rect).center
        # Red cross / pill look
        pygame.draw.circle(screen, (200, 0, 0), screen_pos, self.radius)
        pygame.draw.circle(screen, (255, 80, 80), screen_pos, self.radius - 3)
        # Draw a small white cross on top
        cx, cy = screen_pos
        pygame.draw.rect(screen, (255, 255, 255), (cx - 1, cy - 4, 3, 9))
        pygame.draw.rect(screen, (255, 255, 255), (cx - 4, cy - 1, 9, 3))