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

    def update(self, target):
        """Centers the camera on the target (the player)."""
        # Calculate where the camera needs to be to center the player
        # Formula: -(Target Center) + (Half of Screen Size)
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)

        # Smooth camera movement (Lerp) - 0.1 makes it 'lag' slightly for a professional feel
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1

    def screen_to_world(self, screen_pos):
        return (screen_pos[0] - self.camera.x, screen_pos[1] - self.camera.y)