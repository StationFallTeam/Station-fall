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

    def update(self, keys, screen_width, screen_height):
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
        self.x = max(0, min(self.x, screen_width - self.width))
        self.y = max(0, min(self.y, screen_height - self.height))

        # Sync the rect with the new coordinates - Meheraj
        self.rect.topleft = (self.x, self.y)

        if self.moving:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0

    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        # Use camera.apply to draw the player at the correct SCREEN position - Meheraj
        screen.blit(frame, camera.apply(self.rect))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)