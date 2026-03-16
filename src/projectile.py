import pygame 

class Projectile:
    def __init__(self, pos, velocity, radius=6, color=(225,50,50), lifetime_ms=1200):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(velocity)
        self.radius = radius
        self.color = color 
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime_ms = lifetime_ms
    def update(self): 
        self.pos += self.vel
        
    def is_dead(self):
        return (pygame.time.get_ticks() - self.spawn_time) > self.lifetime_ms
    
    def draw(self, screen, camera):
        screen_pos = camera.apply(pygame.Rect(self.pos.x, self.pos.y, 1, 1)).center
        pygame.draw.circle(screen, (120,0,0), screen_pos, self.radius + 2)
        pygame.draw.circle(screen, (200,20,20), screen_pos, self.radius + 1)
        pygame.draw.circle(screen, (255,80,0), screen_pos, self.radius)
