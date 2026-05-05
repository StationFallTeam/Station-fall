import pygame
from src.damageable import Damageable
from src.assets import resolve_asset_path
from src.enemy_scaling import scale_enemy_damage, scale_enemy_health
from src.pathfinding import astar, world_to_tile, tile_to_world_center

class Enemy:
    def __init__(self, x, y, dungeon_runs=0):

        self.x = x
        self.y = y

        self.drawWidth = 48
        self.drawHeight = 48
        self.width = 32
        self.height = 32
        self.speed = 1.5

        # Load sprite sheet
        self.sprite_sheet = pygame.image.load(resolve_asset_path("sprites/enemy_human_sheet.png")).convert_alpha()

        self.animations = {
            "down": [],
            "left": [],
            "right": [],
            "up": []
        }

        self._load_animations()

        self.direction = "down"
        self.frame_index = 0.0
        self.anim_speed = 0.1
        self.moving = True
        self.contact_damage = scale_enemy_damage(10, dungeon_runs)

        self.drawRect = pygame.Rect(self.x, self.y, self.drawWidth, self.drawHeight)    
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.damageable = Damageable(scale_enemy_health(15, dungeon_runs))

        self.path = []
        self.path_index = 0
        self.last_goal_tile = None
        self.nav_mode = "direct"
        self.nav_mode_until = 0 

    @staticmethod
    def base_stats(dungeon_runs=0):
        return {
            'health': scale_enemy_health(15, dungeon_runs),
            'contact_damage': scale_enemy_damage(10, dungeon_runs),
        }

    def _get_frame(self, x, y):
        frame = pygame.Surface((self.drawWidth, self.drawHeight), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), (x, y, self.drawWidth, self.drawHeight))
        return frame.copy()

    def _load_animations(self):
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            for col in range(4):
                frame = self._get_frame(
                    col * self.drawWidth,
                    row * self.drawHeight
                )
                self.animations[direction].append(frame)

    def update(self, player_rect, walls, collision_map, tile_size):
        self.moving = False

        enemy_tile = world_to_tile(self.rect.centerx, self.rect.centery, tile_size)
        player_tile = world_to_tile(player_rect.centerx, player_rect.centery, tile_size)
        now = pygame.time.get_ticks()

        to_x = player_rect.centerx - self.rect.centerx
        to_y = player_rect.centery - self.rect.centery

        if self.nav_mode == "path" and now < self.nav_mode_until:
            if (
                not self.path
                or self.path_index >= len(self.path)
                or self.last_goal_tile != player_tile
            ):
                self.path = astar(collision_map, enemy_tile, player_tile)
                self.path_index = 1
                self.last_goal_tile = player_tile

            if self.path and self.path_index < len(self.path):
                next_tile = self.path[self.path_index]
                target_x, target_y = tile_to_world_center(next_tile[0], next_tile[1], tile_size)
                to_x = target_x - self.rect.centerx
                to_y = target_y - self.rect.centery

                if abs(to_x) < 8 and abs(to_y) < 8:
                    self.path_index += 1
                    if self.path_index < len(self.path):
                        next_tile = self.path[self.path_index]
                        target_x, target_y = tile_to_world_center(next_tile[0], next_tile[1], tile_size)
                        to_x = target_x - self.rect.centerx
                        to_y = target_y - self.rect.centery
            else:
                self.nav_mode = "direct"
                
        dist = (to_x * to_x + to_y * to_y) ** 0.5
        dx, dy = 0.0, 0.0

        if dist > 0:
            dx = (to_x / dist) * self.speed
            dy = (to_y / dist) * self.speed

            test_rect = self.rect.copy()
            test_rect.x += dx
            test_rect.y += dy
            blocked_diag = any(test_rect.colliderect(w) for w in walls)

            if blocked_diag:
                if self.path and self.path_index < len(self.path):
                        next_tile = self.path[self.path_index]
                        target_x, target_y = tile_to_world_center(next_tile[0], next_tile[1], tile_size)
                        to_x = target_x - self.rect.centerx
                        to_y = target_y - self.rect.centery
                        dist = (to_x * to_x + to_y * to_y) ** 0.5
                        if dist > 0:
                            dx = (to_x / dist) * self.speed
                            dy = (to_y / dist) * self.speed
                if self.path_index >= len(self.path):
                    self.path = astar(collision_map, enemy_tile, player_tile)
                    self.path_index = 1
                if self.nav_mode != "path":
                    self.nav_mode = "path"
                    self.nav_mode_until = now + 500
                    self.path = astar(collision_map, enemy_tile, player_tile)
                    self.path_index = 1
                    self.last_goal_tile = player_tile
                test_rect = self.rect.copy()
                test_rect.x += dx
                blocked_x = any(test_rect.colliderect(w) for w in walls)

                test_rect = self.rect.copy()
                test_rect.y += dy
                blocked_y = any(test_rect.colliderect(w) for w in walls)
                if blocked_x:
                    dx = 0
                if blocked_y:
                    dy = 0
            else:
                if now >= self.nav_mode_until:
                    self.nav_mode = "direct"

            self.moving = (dx != 0 or dy != 0)

            if abs(dx) > abs(dy) + 0.2:
                self.direction = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) + 0.2:
                self.direction = "down" if dy > 0 else "up"

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

    def draw(self, screen, camera):
        frame = self.animations[self.direction][int(self.frame_index)]
        screen.blit(frame, camera.apply(self.drawRect))

    def get_rect(self):
        return self.rect
    
    def take_damage(self, amount: int):
        self.damageable.take_damage(amount)

    @property
    def health(self):
        return self.damageable.health
    
    @property
    def max_health(self):
        return self.damageable.max_health
        
    @property 
    def is_dead(self):
        return self.damageable.health <= 0
    
    @property
    def max_health(self):
        return self.damageable.max_health
    
    @property
    def is_dead(self):
        return self.health <= 0
    
    def _would_collide(self, x, y, handle_all_collisions):
        test_rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        
        for wall in handle_all_collisions:
            if test_rect.colliderect(wall):
                return True
        return False