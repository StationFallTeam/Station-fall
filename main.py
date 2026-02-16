import pygame
import asyncio

from player import Player
from enemy import Enemy
from render import draw_objects
from camera import Camera          # Added for camera - Meheraj
from background import SpaceBackground # Added for parallax background - Meheraj

async def main():
    pygame.init()
    pygame.mixer.init()

    screen_width = 1000
    screen_height = 1000
    world_height = 3000
    world_width = 3000
    win = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Station Fall Playtest")

    clock = pygame.time.Clock()

    player = Player(100, 100)
    enemies = [Enemy(300, 300)]
    
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

        keys = pygame.key.get_pressed()

        player.update(keys, world_width, world_height)
        
        # Make the camera follow the player - Meheraj
        camera.update(player)

        for enemy in enemies:
            enemy.update(player.get_rect())

        # Removed win.fill because background.update_and_draw handles it - Meheraj
        draw_objects(win, player, enemies, camera, background, world_width, world_height) # Updated to pass camera and background - Meheraj

        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())