import pygame

class Damageable:
    def __init__(self, max_health, name = "Entity"):
        self.max_health = max_health
        self.health = max_health
        self.name = name

        self.is_invincible = False
        self.invincibility_duration = 500
        self.last_hit_time = 0

    def take_damage(self, amount):
        if self.is_invincible:
            return
        
        self.health -= amount
        self.health = max(0, self.health)

        self.is_invincible = True
        self.last_hit_time = pygame.time.get_ticks()

        print(f"{self.name} was hit! Health: {self.health}")

        if self.health <= 0:
            print(f"{self.name} died!")

    def update(self):
        if self.is_invincible:
            if pygame.time.get_ticks() - self.last_hit_time >= self.invincibility_duration:
                self.is_invincible = False