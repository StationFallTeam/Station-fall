# main menu
import pygame
import asyncio

from .player import Player
from .enemy import Enemy
from .render import draw_objects
from .camera import Camera          # Added for camera - Meheraj
from .background import SpaceBackground # Added for parallax background - Meheraj
from .world import World

# Start Menu - Loy
MENU = "menu"
GAME = "game"

def draw_menu(win, screen_width, screen_height):
    win.fill((5, 5, 15))

    title_font = pygame.font.SysFont(None, 90)
    small_font = pygame.font.SysFont(None, 32)
    btn_font = pygame.font.SysFont(None, 48)

    # Title
    title = title_font.render("STATION FALL", True, (255, 255, 255))
    win.blit(title, title.get_rect(center=(screen_width // 2, screen_height // 2 - 180)))

    hint = small_font.render("Press ENTER to start", True, (200, 200, 200))
    win.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height // 2 - 120)))

    # Buttons
    btn_w, btn_h = 260, 60
    start_rect = pygame.Rect(0, 0, btn_w, btn_h)
    start_rect.center = (screen_width // 2, screen_height // 2)

    quit_rect = pygame.Rect(0, 0, btn_w, btn_h)
    quit_rect.center = (screen_width // 2, screen_height // 2 + 90)

    mx, my = pygame.mouse.get_pos()

    def draw_button(rect, text):
        hover = rect.collidepoint(mx, my)
        color = (220, 220, 220) if hover else (170, 170, 170)
        pygame.draw.rect(win, color, rect, border_radius=12)
        pygame.draw.rect(win, (40, 40, 40), rect, 3, border_radius=12)

        label = btn_font.render(text, True, (0, 0, 0))
        win.blit(label, label.get_rect(center=rect.center))

    draw_button(start_rect, "Start")
    draw_button(quit_rect, "Quit")

    return start_rect, quit_rect


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
    
    # Create the camera and background objects - Meheraj
    camera = Camera(screen_width, screen_height)
    background = SpaceBackground(screen_width, screen_height)


    # Start Menu System - Loy
    state = MENU
    running = True

    while running:
        clock.tick(60)

        # Draw Menu - Loy
        if state == MENU:
            start_rect, quit_rect = draw_menu(win, screen_width, screen_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Menu Input - Loy
            if state == MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        state = GAME
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if start_rect.collidepoint(mx, my):
                        state = GAME
                    elif quit_rect.collidepoint(mx, my):
                        running = False

            # Game Input - Loy
            elif state == GAME:
                # ESC returns to menu instead of quitting
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU

        
        # Game Update & Draw (only when playing)
        if state == GAME:
            keys = pygame.key.get_pressed()

            player.update(keys, world.walls)
            
            # Make the camera follow the player - Meheraj
            camera.update(player)

            player.rect = player.get_rect()

            for enemy in enemies:
                enemy.update(player.rect)

                if enemy.rect.colliderect(player.rect):
                    player.take_damage(10)

            # Removed win.fill because background.update_and_draw handles it - Meheraj
            draw_objects(win, player, enemies, world.walls, camera, background)  # Updated to pass camera and background - Meheraj

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())


