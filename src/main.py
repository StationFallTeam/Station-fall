import pygame
import asyncio

from .player import Player
from .enemy import Enemy
from .render import draw_objects
from .camera import Camera          # Added for camera - Meheraj
from .background import SpaceBackground # Added for parallax background - Meheraj
from .world import World

async def main():
    
    pygame.init()
    pygame.mixer.init()

    screen_width = 1000
    screen_height = 1000
    world_height = 3000
    world_width = 3000

    win = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Station Fall Playtest")   

    world = World(world_width, world_height)
    clock = pygame.time.Clock()
    
    player = Player(100, 100)
    enemies = [Enemy(300, 300)]
    bullets = []

    # Create the camera and background objects - Meheraj
    camera = Camera(screen_width, screen_height)
    background = SpaceBackground(screen_width, screen_height)

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                mouse_screen = pygame.mouse.get_pos()
                mouse_world = camera.screen_to_world(mouse_screen)
                bullet = player.shoot(mouse_world)
                if bullet: 
                    bullets.append(bullet)

        keys = pygame.key.get_pressed()
        player.update(keys, world.walls)
        # Make the camera follow the player - Meheraj
        camera.update(player)

        player.rect = player.get_rect()

        for enemy in enemies:
            enemy.update(player.rect)
            if enemy.rect.colliderect(player.rect):
                player.take_damage(10)
        for bullet in bullets[:]:
            bullet.update()
            
        # Removed win.fill because background.update_and_draw handles it - Meheraj
        draw_objects(win, player, enemies, bullets, world.walls, camera, background) # Updated to pass camera and background - Meheraj
        pygame.display.flip()
        await asyncio.sleep(0)
        
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())