import pygame
from src.damageable import Damageable
from src.assets import resolve_asset_path

class Enemy:
    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.drawWidth = 48
        self.drawHeight = 48
        self.width = 32
        self.height = 32
        self.speed = 1.5

        # Load sprite sheet
        self.sprite_sheet = pygame.image.load(resolve_asset_path("sprites/enemy_human_sheet.png")).convert_alpha()

        self.animations = {
            "down": [],
            "left": [],
            "right": [],
            "up": []
        }

        self._load_animations()

        self.direction = "down"
        self.frame_index = 0.0
        self.anim_speed = 0.1
        self.moving = True

        self.drawRect = pygame.Rect(self.x, self.y, self.drawWidth, self.drawHeight)    
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.damageable = Damageable(15)

    def _get_frame(self, x, y):
        frame = pygame.Surface((self.drawWidth, self.drawHeight), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), (x, y, self.drawWidth, self.drawHeight))
        return frame.copy()

    def _load_animations(self):
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            for col in range(4):
                frame = self._get_frame(
                    col * self.drawWidth,
                    row * self.drawHeight
                )
                self.animations[direction].append(frame)

    def update(self, player_rect):
        self.moving = False

        # Store old position for collision resolution
        old_x, old_y = self.x, self.y
        
        # Movement logic
        dx, dy = 0, 0
        
        if player_rect.x > self.x:
            dx = self.speed
            self.direction = "right"
            self.moving = True
        elif player_rect.x < self.x:
            dx = -self.speed
            self.direction = "left"
            self.moving = True
            
        if player_rect.y > self.y:
            dy = self.speed
            self.direction = "down"
            self.moving = True
        elif player_rect.y < self.y:
            dy = -self.speed
            self.direction = "up"
            self.moving = True

        # Apply movement
        self.x += dx
        self.y += dy
        
        # Store movement deltas for collision resolution
        self._last_dx = dx
        self._last_dy = dy

        self.rect.topleft = (self.x, self.y)
        self.drawRect.midbottom = self.rect.midbottom

        # Animate
        if self.moving:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0
        
        self.damageable.update()

    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        screen.blit(frame, camera.apply(self.drawRect))

    def get_rect(self):
        return self.rect
    
    def take_damage(self, amount: int):
        self.damageable.take_damage(amount)

    @property
    def health(self):
        return self.damageable.health
    
    @property
    def max_health(self):
        return self.damageable.max_health
        
    @property 
    def is_dead(self):
        return self.damageable.health <= 0
    
    @property
    def max_health(self):
        return self.damageable.max_health
    
    @property
    def is_dead(self):
        return self.health <= 0