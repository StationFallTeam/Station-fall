import pygame

class Damageable:
    def __init__(self, max_health):
        self.max_health = max_health
        self.health = max_health
        self.is_alive = True
        self.invulnerable_timer = 0

    def take_damage(self, amount):
        if self.invulnerable_timer > 0 or not self.is_alive:
            return
        
        self.health -= amount
        self.invulnerable_timer = 20

        if self.health <= 0:
            self.health = 0
            self.is_alive = False

    def update_damageable(self):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1