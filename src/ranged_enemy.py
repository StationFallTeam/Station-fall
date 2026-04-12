import pygame
import math
from src.damageable import Damageable
from src.projectile import Projectile 

PREFERRED_DISTANCE = 180   # px — tries to stay this far away
INNER_DEADZONE     = 130   # closer than this → flee
OUTER_DEADZONE     = 230   # farther than this → approach
SHOOT_COOLDOWN_MS  = 1800  # time between shots
PROJECTILE_SPEED   = 4.0

class RangedEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.drawWidth  = 48
        self.drawHeight = 48
        self.width      = 32
        self.height     = 32
        self.speed      = 1.2

        self.sprite_sheet = pygame.image.load(
            "sprites/enemy_human_range_sheet.png"
        ).convert_alpha()

        self.animations = {"down": [], "left": [], "right": [], "up": []}
        self._load_animations()

        self.direction   = "down"
        self.frame_index = 0.0
        self.anim_speed  = 0.08
        self.moving      = False

        self.drawRect = pygame.Rect(self.x, self.y, self.drawWidth, self.drawHeight)
        self.rect     = pygame.Rect(self.x, self.y, self.width, self.height)
        self.damageable = Damageable(10)   # squishier than melee

        self._last_dx = 0
        self._last_dy = 0

        self._shoot_timer = 0              
        self._pending_projectiles = [] 

    def _get_frame(self, x, y):
        frame = pygame.Surface((self.drawWidth, self.drawHeight), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), (x, y, self.drawWidth, self.drawHeight))
        return frame.copy()

    def _load_animations(self):
        directions = ["down", "left", "right", "up"]
        for row, direction in enumerate(directions):
            for col in range(4):
                frame = self._get_frame(col * self.drawWidth, row * self.drawHeight)
                self.animations[direction].append(frame)

    def update(self, player_rect):
        self._pending_projectiles.clear()
        self.moving = False

        px = player_rect.centerx - (self.x + self.width  // 2)
        py = player_rect.centery - (self.y + self.height // 2)
        dist = math.hypot(px, py)

        dx, dy = 0.0, 0.0

        if dist > 0:
            norm_x = px / dist
            norm_y = py / dist

            if dist < INNER_DEADZONE:
                # Too close — back away
                dx = -norm_x * self.speed
                dy = -norm_y * self.speed
                self.moving = True
            elif dist > OUTER_DEADZONE:
                # Too far — close in
                dx = norm_x * self.speed
                dy = norm_y * self.speed
                self.moving = True

            self._update_facing(norm_x, norm_y)

            if dist <= OUTER_DEADZONE:
                self._try_shoot(norm_x, norm_y)

        self.x += dx
        self.y += dy
        self._last_dx = dx
        self._last_dy = dy

        self.rect.topleft     = (self.x, self.y)
        self.drawRect.midbottom = self.rect.midbottom

        if self.moving:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.animations[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0

        self.damageable.update()

    def _update_facing(self, norm_x, norm_y):
        """Pick cardinal direction based on dominant axis toward player."""
        if abs(norm_x) >= abs(norm_y):
            self.direction = "right" if norm_x > 0 else "left"
        else:
            self.direction = "down" if norm_y > 0 else "up"

    def _try_shoot(self, norm_x, norm_y):
        now = pygame.time.get_ticks()
        if now - self._shoot_timer >= SHOOT_COOLDOWN_MS:
            self._shoot_timer = now
            spawn_offset = 20
            origin = (
                self.x + self.width  // 2 + norm_x * spawn_offset,
                self.y + self.height // 2 + norm_y * spawn_offset,
            )
            vel = (norm_x * PROJECTILE_SPEED, norm_y * PROJECTILE_SPEED)
            proj = Projectile(origin, vel, 5, (80, 200, 255), 1400, 8)
            proj._shooter = self
            self._pending_projectiles.append(proj)

    def pop_projectiles(self):
        """Call this from your game/room loop to collect newly fired projectiles."""
        result = list(self._pending_projectiles)
        self._pending_projectiles.clear()
        return result

    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        screen.blit(frame, camera.apply(self.drawRect))

    def get_rect(self):
        return self.rect

    def take_damage(self, amount: int):
        self.damageable.take_damage(amount)

    @property
    def health(self):       return self.damageable.health
    @property
    def max_health(self):   return self.damageable.max_health
    @property
    def is_dead(self):      return self.damageable.health <= 0