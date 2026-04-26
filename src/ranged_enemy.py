import pygame
import math
from src.damageable import Damageable
from src.projectile import Projectile 
from src.pathfinding import astar, world_to_tile, tile_to_world_center

INNER_DEADZONE     = 128   # closer than this → flee
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
        self.speed      = 1.5

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

        self.path = []
        self.path_index = 0
        self.last_goal_tile = None
        self.nav_mode = "direct"
        self.nav_mode_until = 0 
        
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

    def update(self, player_rect, walls, collision_map, tile_size):
        self._pending_projectiles.clear()
        self.moving = False

        enemy_tile = world_to_tile(self.rect.centerx, self.rect.centery, tile_size)
        player_tile = world_to_tile(player_rect.centerx, player_rect.centery, tile_size)
        now = pygame.time.get_ticks()

        player_dx = player_rect.centerx - self.rect.centerx
        player_dy = player_rect.centery - self.rect.centery
        player_dist = (player_dx * player_dx + player_dy * player_dy) ** 0.5

        dx, dy = 0.0, 0.0

        if player_dist > 0:
            norm_x = player_dx / player_dist
            norm_y = player_dy / player_dist

            can_see_player = self.has_line_of_sight(player_rect, walls)
            
            if can_see_player:
                self.nav_mode = "direct"
                self.path = []
                self.path_index = 0

                if player_dist < INNER_DEADZONE:
                    dx = -norm_x * self.speed
                    dy = -norm_y * self.speed

                elif player_dist > OUTER_DEADZONE:
                    dx = norm_x * self.speed
                    dy = norm_y * self.speed

                else:
                    dx = 0.0
                    dy = 0.0
                    
            else:
                if (
                    self.nav_mode != "path"
                    or now >= self.nav_mode_until
                    or not self.path
                    or self.path_index >= len(self.path)
                    or self.last_goal_tile != player_tile
                ):
                    self.nav_mode = "path"
                    self.nav_mode_until = now + 500
                    self.path = astar(collision_map, enemy_tile, player_tile)
                    self.path_index = 1
                    self.last_goal_tile = player_tile

                if self.path and self.path_index < len(self.path):
                    next_tile = self.path[self.path_index]
                    target_x, target_y = tile_to_world_center(
                        next_tile[0],
                        next_tile[1],
                        tile_size
                    )

                    to_x = target_x - self.rect.centerx
                    to_y = target_y - self.rect.centery
                    dist = (to_x * to_x + to_y * to_y) ** 0.5

                    if abs(to_x) < 12 and abs(to_y) < 12:
                        self.path_index += 1

                        if self.path_index < len(self.path):
                            next_tile = self.path[self.path_index]
                            target_x, target_y = tile_to_world_center(
                                next_tile[0],
                                next_tile[1],
                                tile_size
                            )
                            to_x = target_x - self.rect.centerx
                            to_y = target_y - self.rect.centery
                            dist = (to_x * to_x + to_y * to_y) ** 0.5

                    if dist > 0:
                        dx = (to_x / dist) * self.speed
                        dy = (to_y / dist) * self.speed
                        
            if dx != 0 or dy != 0:
                test_rect = self.rect.copy()
                test_rect.x += dx
                test_rect.y += dy
                blocked_diag = any(test_rect.colliderect(w) for w in walls)

                if blocked_diag:
                    original_dx = dx
                    original_dy = dy

                    test_x = self.rect.copy()
                    test_x.x += original_dx
                    blocked_x = any(test_x.colliderect(w) for w in walls)

                    test_y = self.rect.copy()
                    test_y.y += original_dy
                    blocked_y = any(test_y.colliderect(w) for w in walls)

                    if blocked_x:
                        dx = 0.0
                    if blocked_y:
                        dy = 0.0
                        
                    if dx == 0 and dy == 0:
                        slide_x = -norm_y * self.speed
                        slide_y = norm_x * self.speed

                        test_slide = self.rect.copy()
                        test_slide.x += slide_x
                        test_slide.y += slide_y

                        if not any(test_slide.colliderect(w) for w in walls):
                            dx = slide_x
                            dy = slide_y
                        else:
                            slide_x = norm_y * self.speed
                            slide_y = -norm_x * self.speed

                            test_slide = self.rect.copy()
                            test_slide.x += slide_x
                            test_slide.y += slide_y

                            if not any(test_slide.colliderect(w) for w in walls):
                                dx = slide_x
                                dy = slide_y
                            else:
                                dx = 0.0
                                dy = 0.0

            self.moving = (dx != 0 or dy != 0)
            
            self._update_facing(norm_x, norm_y)
            
            if can_see_player and player_dist <= OUTER_DEADZONE:
                self._try_shoot(norm_x, norm_y)

        self.x += dx
        self.y += dy

        self._last_dx = dx
        self._last_dy = dy

        self.rect.topleft = (self.x, self.y)
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

    def has_line_of_sight(self, player_rect, walls):
        line = (self.rect.center, player_rect.center)
        for wall in walls:
            if wall.clipline(line):
                return False
        return True