import pygame
from .damageable import Damageable
from .projectile import Projectile

class Player(Damageable):
    def __init__(self, x, y):
        super().__init__(max_health=100)

        self.x = x
        self.y = y

        self.width = 48
        self.height = 48
        self.speed = 5

        # Load spritesheet (root-relative for pygbag)
        self.sprite_sheet = pygame.image.load("sprites/player_sheet.png").convert_alpha()

        self.animations = {
            "down": [],
            "left": [],
            "right": [],
            "up": []
        }

        self._load_animations()

        self.direction = "down"
        self.frame_index = 0.0
        self.anim_speed = 0.15
        self.moving = False
        # Create a rect for the camera to track - Meheraj
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
   

    def _get_frame(self, x, y):
        frame = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), (x, y, self.width, self.height))
        return frame.copy()  # REQUIRED for pygbag

    def _load_animations(self):
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            for col in range(4):
                frame = self._get_frame(
                    col * self.width,
                    row * self.height
                )
                self.animations[direction].append(frame)

    def update(self, keys, walls):
        self.moving = False

        dx = 0
        dy = 0

        if keys[pygame.K_a]:
            dx -= self.speed
            self.direction = "left"
            self.moving = True
        if keys[pygame.K_d]:
            dx += self.speed
            self.direction = "right"
            self.moving = True
        if keys[pygame.K_w]:
            dy -= self.speed
            self.direction = "up"
            self.moving = True
        if keys[pygame.K_s]:
            dy += self.speed
            self.direction = "down"
            self.moving = True

        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:
                    self.rect.right = wall.left
                if dx < 0:
                    self.rect.left = wall.right

        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:
                    self.rect.bottom = wall.top
                if dy < 0:
                    self.rect.top = wall.bottom

        self.x = self.rect.x
        self.y = self.rect.y

        # Sync the rect with the new coordinates - Meheraj
        self.rect.topleft = (self.x, self.y)

        if self.moving:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0

        super().update()


    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        draw_pos = camera.apply(self.rect)

        if self.is_invincible:
            # create a red tinted copy
            flash = frame.copy()
            flash.fill((225, 0, 0, 120), special_flags = pygame.BLEND_RGBA_ADD)
            screen.blit(flash, draw_pos)
        else:
            screen.blit(frame, draw_pos)


    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    
    def shoot(self, target_world_pos):
            start = pygame.Vector2(self.rect.center)

            direction = pygame.Vector2(target_world_pos) - start
            if direction.length_squared() == 0:
                return None
            direction = direction.normalize()
            speed = 10
            velocity = direction * speed 
            return Projectile(start, velocity, radius=6, color=(225,50,50), lifetime_ms=1200)
    
    
