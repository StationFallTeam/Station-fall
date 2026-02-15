import pygame

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width, self.height = width, height

    def apply(self, entity):
        # If we pass a Rect directly, move it by the camera offset
        if isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        # Otherwise, move the entity's rect attribute
        return entity.rect.move(self.camera.topleft)

    def apply_pos(self, pos):
        return (pos[0] + self.camera.x, pos[1] + self.camera.y)

    def update(self, target):
        # Center the camera on the target (usually the player)
        x = -target.x + int(self.width / 2)
        y = -target.y + int(self.height / 2)
        
        # Smooth camera movement (Lerp)
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1