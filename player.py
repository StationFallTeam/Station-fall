import pygame

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.width = 48
        self.height = 48
        self.speed = 5

        # Load spritesheet (root-relative for pygbag)
        self.sprite_sheet = pygame.image.load("player_sheet.png").convert_alpha()

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

        self.max_health = 100
        self.health = self.max_health

        self.invincible = False
        self.invincibility_duration = 1000
        self.last_hit_time = 0

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

    def update(self, keys, world_width, world_height):
        self.moving = False

        if keys[pygame.K_a]:
            self.x -= self.speed
            self.direction = "left"
            self.moving = True
        if keys[pygame.K_d]:
            self.x += self.speed
            self.direction = "right"
            self.moving = True
        if keys[pygame.K_w]:
            self.y -= self.speed
            self.direction = "up"
            self.moving = True
        if keys[pygame.K_s]:
            self.y += self.speed
            self.direction = "down"
            self.moving = True

        # Update world coordinates
        self.x = max(0, min(self.x, world_width - self.width))
        self.y = max(0, min(self.y, world_height - self.height))

        # Sync the rect with the new coordinates - Meheraj
        self.rect.topleft = (self.x, self.y)

        if self.moving:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0

        self.update_invincibility()

    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        draw_pos = camera.apply(self.rect)

        if self.invincible:
            # create a red tinted copy
            flash = frame.copy()
            flash.fill((225, 0, 0, 120), special_flags = pygame.BLEND_RGBA_ADD)
            screen.blit(flash, draw_pos)
        else:
            screen.blit(frame, draw_pos)


    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()

        if not self.invincible:
            self.health -= amount
            self.health = max(0, self.health)

            self.invincible = True
            self.last_hit_time = current_time

            print("We've been hit! Health:", self.health)
    
    def update_invincibility(self):
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_hit_time >= self.invincibility_duration:
                self.invincible = False