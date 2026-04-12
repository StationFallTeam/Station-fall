import pygame
import random

class CollisionSystem:
    # Handles all collision detection
    
    def __init__(self):
        self.walls = []
        self.temporary_walls = []  # For doors and other dynamic walls
        self.triggers = {}  # Dictionary of triggers to rects
        
    def update_walls(self, walls):
        self.walls = walls
        
    def add_temporary_walls(self, wall_rects):
        self.temporary_walls.extend(wall_rects)
        
    def remove_temporary_walls(self, wall_rects):
        for rect in wall_rects:
            if rect in self.temporary_walls:
                self.temporary_walls.remove(rect)
                
    def clear_temporary_walls(self):
        self.temporary_walls.clear()
        
    def add_triggers(self, trigger_dict):
        self.triggers.update(trigger_dict)
        
    def clear_triggers(self):
        self.triggers.clear()
        
    def is_in_trigger(self, player, trigger_name):
        if trigger_name not in self.triggers:
            return False
            
        player_rect = player.rect
        trigger_rects = self.triggers[trigger_name]
        
        for trigger_rect in trigger_rects:
            if player_rect.colliderect(trigger_rect):
                return True
        return False
        
    def get_all_walls(self):
        return self.walls + self.temporary_walls
    
    def handle_all_collisions(self, player, enemies, bullets, floating_texts=None, coins=None):
        if floating_texts is None:
            floating_texts = []
        if coins is None:
            coins = []
            
        # Single iteration over walls for all wall-based collision checks
        self._check_wall_collisions(player, enemies, bullets)
        
        # Check entity-to-entity collisions (separate from walls)
        self._check_entity_collisions(player, enemies, bullets, floating_texts, coins)
    
    def _check_wall_collisions(self, player, enemies, bullets):
        all_walls = self.get_all_walls()
        
        # Player collision with proper axis separation
        self._resolve_player_wall_collision_proper(player, all_walls)
        
        # Enemy vs wall collisions
        for enemy in enemies:
            for wall in all_walls:
                if enemy.rect.colliderect(wall):
                    self._resolve_enemy_wall_collision(enemy, wall)
        
        # Bullet vs wall collisions
        for bullet in bullets[:]:
            bullet_rect = bullet.get_rect()
            for wall in all_walls:
                if bullet_rect.colliderect(wall):
                    bullets.remove(bullet)
                    break
    
    def _check_entity_collisions(self, player, enemies, bullets, floating_texts, coins):
        player_rect = player.rect
        
        # Enemy vs enemy collision (prevent overlap)
        for i, enemy1 in enumerate(enemies):
            enemy1_rect = enemy1.rect
            for j, enemy2 in enumerate(enemies[i+1:], i+1):
                enemy2_rect = enemy2.rect
                if enemy1_rect.colliderect(enemy2_rect):
                    # Push enemies apart
                    self._resolve_enemy_enemy_collision(enemy1, enemy2)
        
        # Player vs enemies collision
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect):
                self._handle_player_enemy_collision(player, enemy, floating_texts)
        
        # Bullets vs enemies collision
        for bullet in bullets[:]:
            bullet_rect = bullet.get_rect()
            
            for enemy in enemies[:]:
                if bullet_rect.colliderect(enemy.rect):
                    # Handle bullet hitting enemy
                    damage_dealt = self._handle_bullet_enemy_collision(bullet, enemy, floating_texts)
                    
                    # Remove bullet after hit
                    if bullet in bullets:
                        bullets.remove(bullet)
                    
                    # Check if enemy died and handle death
                    if enemy.health <= 0:
                        self._handle_enemy_death(enemy, enemies, floating_texts, coins)
                    
                    break  # Bullet can only hit one enemy

        # Enemy bullets vs player collision
        for bullet in bullets[:]:
            # Only process bullets fired by enemies
            if not hasattr(bullet, '_shooter') or bullet._shooter not in enemies:
                continue
            
            bullet_rect = bullet.get_rect()
            if bullet_rect.colliderect(player_rect):
                if not player.is_invincible:
                    damage = bullet.damage
                    player.take_damage(damage)
                    
                    from src.floating_texts import FloatingText
                    floating_texts.append(
                        FloatingText(player.x, player.y - 20, f"-{damage}", color=(255, 0, 0))
                    )
                
                if bullet in bullets:
                    bullets.remove(bullet)
                    
    def _resolve_player_wall_collision_proper(self, player, walls):
        dx = player._last_dx
        dy = player._last_dy
        
        if dx == 0 and dy == 0:
            return  # No movement, no collision to resolve
            
        # Store original position
        original_x = player.x - dx
        original_y = player.y - dy
        
        # Test X movement first
        player.x = original_x + dx
        player.y = original_y  # Keep Y at original position
        player.rect.x = player.x
        player.rect.y = player.y
        
        # Check for X-axis collision
        x_collision = False
        for wall in walls:
            if player.rect.colliderect(wall):
                x_collision = True
                break
                
        if x_collision:
            # Revert X movement, keep original X
            player.x = original_x
            player.rect.x = player.x
            
        # Test Y movement
        player.y = original_y + dy
        player.rect.y = player.y
        
        # Check for Y-axis collision  
        y_collision = False
        for wall in walls:
            if player.rect.colliderect(wall):
                y_collision = True
                break
                
        if y_collision:
            # Revert Y movement, keep original Y
            player.y = original_y
            player.rect.y = player.y
            
        # Update draw rect to match collision rect
        player.drawRect.midbottom = player.rect.midbottom
    
    def _resolve_enemy_wall_collision(self, enemy, wall):
        # Simple push-back resolution for enemies
        # Calculate overlap and push enemy back
        overlap_x = min(enemy.rect.right - wall.left, wall.right - enemy.rect.left)
        overlap_y = min(enemy.rect.bottom - wall.top, wall.bottom - enemy.rect.top)
        
        if overlap_x < overlap_y:
            # Horizontal collision - push enemy horizontally
            if enemy.rect.centerx < wall.centerx:
                enemy.rect.right = wall.left
            else:
                enemy.rect.left = wall.right
        else:
            # Vertical collision - push enemy vertically
            if enemy.rect.centery < wall.centery:
                enemy.rect.bottom = wall.top
            else:
                enemy.rect.top = wall.bottom
        
        # Update enemy position to match rect
        enemy.x = enemy.rect.x
        enemy.y = enemy.rect.y
    
    def _resolve_enemy_enemy_collision(self, enemy1, enemy2):
        # Calculate direction to push enemies apart
        center1_x = enemy1.rect.centerx
        center1_y = enemy1.rect.centery
        center2_x = enemy2.rect.centerx
        center2_y = enemy2.rect.centery
        
        # Calculate push direction
        dx = center1_x - center2_x
        dy = center1_y - center2_y
        
        # Prevent division by zero
        distance = max(1, (dx * dx + dy * dy) ** 0.5)
        
        # Normalize and apply push force
        push_distance = 2  # Minimum separation
        push_x = (dx / distance) * push_distance
        push_y = (dy / distance) * push_distance
        
        # Push both enemies apart equally
        enemy1.rect.centerx += push_x
        enemy1.rect.centery += push_y
        enemy2.rect.centerx -= push_x
        enemy2.rect.centery -= push_y
        
        # Update enemy positions
        enemy1.x = enemy1.rect.x
        enemy1.y = enemy1.rect.y
        enemy2.x = enemy2.rect.x
        enemy2.y = enemy2.rect.y
    

    
    def _handle_player_enemy_collision(self, player, enemy, floating_texts):
        # Check if player can take damage (not invincible)
        if player.is_invincible:
            return
            
        damage = 10  # Default enemy damage
        player.take_damage(damage)
        
        # Add damage text
        from src.floating_texts import FloatingText
        floating_texts.append(
            FloatingText(player.x, player.y - 20, f"-{damage}", color=(255, 0, 0))
        )
    
    def _handle_bullet_enemy_collision(self, bullet, enemy, floating_texts):
        damage = bullet.damage
        
        # Apply damage to enemy
        before_health = enemy.health
        enemy.take_damage(damage)
        after_health = enemy.health
        actual_damage = before_health - after_health
        
        # Add damage text if damage was actually dealt
        if actual_damage > 0:
            from src.floating_texts import FloatingText
            floating_texts.append(
                FloatingText(enemy.x, enemy.y - 20, f"-{actual_damage}", color=(255, 255, 0))
            )
            
        return actual_damage
    
    def _handle_enemy_death(self, enemy, enemies, floating_texts, coins):
        if enemy in enemies:
            # Create coin at enemy location
            from src.coin import Coin
            from src.health_drop import HealthDrop

            coin_value = 3
            coin = Coin(enemy.rect.centerx, enemy.rect.centery, value=coin_value)
            coins.append(coin)

            if random.randint(1, 5) == 1:
                health = HealthDrop(enemy.rect.centerx + 10, enemy.rect.centery, heal_amount=20)
                coins.append(health) 
            
            enemies.remove(enemy)


# Global collision system instance
collision_system = CollisionSystem()


def update_collision_walls(walls):
    collision_system.update_walls(walls)


def clear_temporary_walls():
    collision_system.clear_temporary_walls()


def add_triggers(trigger_dict):
    collision_system.add_triggers(trigger_dict)


def clear_triggers():
    collision_system.clear_triggers()


def is_in_trigger(player, trigger_name):
    return collision_system.is_in_trigger(player, trigger_name)


def handle_all_collisions(player, enemies, bullets, floating_texts=None, coins=None):
    return collision_system.handle_all_collisions(player, enemies, bullets, floating_texts, coins)