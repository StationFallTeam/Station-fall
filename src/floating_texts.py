import pygame

class FloatingText:
    def __init__(self, x, y, text, color=(255, 0, 0), duration_ms=1000):
        self.x = x
        self.y = y
        self.duration = duration_ms
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255
        
        # Pre-render the text surface once to save CPU
        font = pygame.font.SysFont(None, 30)
        self.image = font.render(text, True, color).convert_alpha()
        self.velocity_y = -1.2 

    def update(self):
        self.y += self.velocity_y
        elapsed = pygame.time.get_ticks() - self.start_time
        
        if elapsed > self.duration:
            return False
        
        self.alpha = max(0, 255 - int((elapsed / self.duration) * 255))
        return True

    def draw(self, screen, camera):
        # Create a temporary copy to adjust alpha without destroying the original
        temp_surf = self.image.copy()
        temp_surf.set_alpha(self.alpha)
        
        # Apply camera to the world coordinates (x, y)
        draw_pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
        screen.blit(temp_surf, (draw_pos.x, draw_pos.y))