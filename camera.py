import pygame

class Camera:
    def __init__(self, width, height):
        # This rect represents the "viewing window" in the world
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """Translates an entity's world rect to a screen rect."""
        if isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        return entity.rect.move(self.camera.topleft)

    # def update(self, target):
    #     """Centers the camera on the target (the player)."""
    #     # Calculate where the camera needs to be to center the player
    #     # Formula: -(Target Center) + (Half of Screen Size)
    #     x = -target.rect.centerx + int(self.width / 2)
    #     y = -target.rect.centery + int(self.height / 2)

    #     # Smooth camera movement (Lerp) - 0.1 makes it 'lag' slightly for a professional feel
    #     self.camera.x += (x - self.camera.x) * 0.1
    #     self.camera.y += (y - self.camera.y) * 0.1

    def update(self, target, world_width, world_height):
        x = -target.rect.centerx + self.width // 2
        y = -target.rect.centery + self.height // 2

        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1

        max_x = 0
        max_y = 0
        min_x = -(world_width - self.width)
        min_y = -(world_height - self.height)

        self.camera.x = max(min_x, min(max_x, self.camera.x))
        self.camera.y = max(min_y, min(max_y, self.camera.y))
