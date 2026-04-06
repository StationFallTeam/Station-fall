import pygame

class FloatingText:
    def __init__(self, x, y, text, color=(255, 0, 0), duration_ms=1000):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration_ms
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255
        self.font = pygame.font.SysFont(None, 30)
        self.velocity_y = -1.2  # Pixels per frame, adjust for faster/slower floating

    def update(self):
        # Move the text upwards
        self.y += self.velocity_y
        
        # Calculate how long the text has been alive and update alpha for fading effect
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.duration:
            return False  # Indicates that the text should be removed
        
        self.alpha = max(0, 255 - int((elapsed / self.duration) * 255))
        return True

    def draw(self, screen, camera):
        # Render the text with the current alpha value
        text_surf = self.font.render(self.text, True, self.color).convert_alpha()
        
        # Create a surface to apply the alpha value
        alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        alpha_surf.fill((255, 255, 255, self.alpha))
        text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Calculate the position to draw the text, applying camera transformations
        draw_pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
        screen.blit(text_surf, (draw_pos.x, draw_pos.y))