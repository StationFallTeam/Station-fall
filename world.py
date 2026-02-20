# Border walls, wall rects, tilemap, rooms, etc...
import pygame

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = []
        self._create_border()

    def _create_border(self):
        thickness = 8.8

        self.walls.append(pygame.Rect(0, 0, self.width, thickness))
        self.walls.append(pygame.Rect(0, self.height - thickness, self.width, thickness))
        self.walls.append(pygame.Rect(0, 0, thickness, self.height))
        self.walls.append(pygame.Rect(self.width - thickness, 0, thickness, self.height))
