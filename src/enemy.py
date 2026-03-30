import pygame
from damageable import Damageable

class Enemy:
    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 48
        self.height = 48
        self.speed = 2.5

        # Load sprite sheet
        self.sprite_sheet = pygame.image.load("sprites/enemy_human_sheet.png").convert_alpha()

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

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.damageable = Damageable(50)

    def _get_frame(self, x, y):
        frame = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), (x, y, self.width, self.height))
        return frame.copy()

    def _load_animations(self):
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            for col in range(4):
                frame = self._get_frame(
                    col * self.width,
                    row * self.height
                )
                self.animations[direction].append(frame)

    def update(self, player_rect):
        self.moving = False

        # Movement logic
        if player_rect.x > self.x:
            self.x += self.speed
            self.direction = "right"
            self.moving = True
        if player_rect.x < self.x:
            self.x -= self.speed
            self.direction = "left"
            self.moving = True
        if player_rect.y > self.y:
            self.y += self.speed
            self.direction = "down"
            self.moving = True
        if player_rect.y < self.y:
            self.y -= self.speed
            self.direction = "up"
            self.moving = True

        self.rect.topleft = (self.x, self.y)

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
        screen.blit(frame, camera.apply(self.rect))

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
        return self.health <= 0