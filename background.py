import pygame
import random

class SpaceBackground:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.bg_color = (5, 5, 15)
        self.layers = [
            {"speed": 0.2, "stars": self._gen(50, (1, 3))},
            {"speed": 0.5, "stars": self._gen(100, (1, 2))}
        ]

    def _gen(self, count, size_range):
        return [[random.randint(0, self.width), random.randint(0, self.height), 
                 random.randint(*size_range), (random.randint(150, 255),)*3] for _ in range(count)]

    def update_and_draw(self, surface, camera_pos):
        surface.fill(self.bg_color)
        for layer in self.layers:
            off_x = (camera_pos[0] * layer["speed"]) % self.width
            off_y = (camera_pos[1] * layer["speed"]) % self.height
            for s in layer["stars"]:
                pygame.draw.circle(surface, s[3], (int((s[0]-off_x)%self.width), int((s[1]-off_y)%self.height)), s[2])
