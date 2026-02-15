import pygame

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        self.vel = 5

        self.spriteSheet = pygame.image.load("../player_sheet.png").convert_alpha()

        self.animations = {
            "down": [],
            "left": [],
            "right": [],
            "up": []
        }

        self.load_animations()

        self.direction = "down"
        self.frameIndex = 0
        self.animationSpeed = 0.2
        self.moving = False

    def getFrame(self, sheet, x, y, width, height):
        frame = pygame.Surface((width, height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (x, y, width, height))
        return frame

    def load_animations(self):
        directions = ["down", "left", "right", "up"]
        for row in range(4):
            for col in range(4):
                frame = self.getFrame(
                    self.spriteSheet,
                    col * self.width,
                    row * self.height,
                    self.width,
                    self.height
                )
                self.animations[directions[row]].append(frame)

    def update(self, keys, screen_width, screen_height):
        self.moving = False

        if keys[pygame.K_a]:
            self.x -= self.vel
            self.direction = "left"
            self.moving = True
        if keys[pygame.K_d]:
            self.x += self.vel
            self.direction = "right"
            self.moving = True
        if keys[pygame.K_w]:
            self.y -= self.vel
            self.direction = "up"
            self.moving = True
        if keys[pygame.K_s]:
            self.y += self.vel
            self.direction = "down"
            self.moving = True

        # Screen bounds
        self.x = max(0, min(self.x, screen_width - self.width))
        self.y = max(0, min(self.y, screen_height - self.height))

        # Animation update
        if self.moving:
            self.frameIndex += self.animationSpeed
            if self.frameIndex >= len(self.animations[self.direction]):
                self.frameIndex = 0
        else:
            self.frameIndex = 0

    def draw(self, win):
        win.blit(self.animations[self.direction][int(self.frameIndex)], (self.x, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
