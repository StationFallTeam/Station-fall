import pygame

class Camera:
    def __init__(self, width, height):
        # This Rect represents the camera's view in the world
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        # This shifts the world coordinates to screen coordinates
        return entity_rect.move(self.camera.topleft)

    def update(self, target):
        # Calculate centering: (Screen Center) - (Target Center)
        x = -target.x + int(self.width / 2)
        y = -target.y + int(self.height / 2)

        # Smooth follow (Lerp): 0.1 is the delay/smoothness factor
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1