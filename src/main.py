# main menu
import pygame
import asyncio
import math

from .player import Player
from .enemy import Enemy
from .render import draw_objects
from .camera import Camera          # Added for camera - Meheraj
from .background import SpaceBackground # Added for parallax background - Meheraj
from .world import World

# NOTE:
# When debugging pygbag web crashes, temporarily wrap main() in a try/except
# with traceback.print_exc() to surface errors in the browser console.

# Start Menu - Loy
MENU = "menu"
GAME = "game"

def draw_menu(win, screen_width, screen_height, truck_img, float_time):

    title_font = pygame.font.SysFont(None, 90)
    small_font = pygame.font.SysFont(None, 32)
    btn_font = pygame.font.SysFont(None, 48)

    # Title
    title = title_font.render("STATION FALL", True, (255, 255, 255))
    win.blit(title, title.get_rect(center=(screen_width // 2, screen_height // 2 - 180)))

    hint = small_font.render("Press ENTER to start", True, (200, 200, 200))
    win.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height // 2 - 120)))

    #ship
    float_offset = math.sin(float_time) * 15
    truck_rect = truck_img.get_rect()
    truck_rect.center = (screen_width // 2, screen_height // 2 + float_offset)
    win.blit(truck_img, truck_rect)

    # Buttons
    btn_w, btn_h = 260, 60
    start_rect = pygame.Rect(0, 0, btn_w, btn_h)
    start_rect.center = (screen_width // 2, screen_height // 2 +120)

    quit_rect = pygame.Rect(0, 0, btn_w, btn_h)
    quit_rect.center = (screen_width // 2, screen_height // 2 + 210)

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
    bullets = []

    #load menu image
    truck_img = pygame.image.load("sprites/truck.png").convert_alpha()
    truck_img = pygame.transform.smoothscale(truck_img, (400, 250))
    float_time = 0
    menu_camera_x = 0
    menu_camera_y = 0

    # Create the camera and background objects - Meheraj
    camera = Camera(screen_width, screen_height)
    background = SpaceBackground(screen_width, screen_height)

    #music
    pygame.mixer.music.load("sound/starfield.ogg")
    pygame.mixer.music.play(-1)

    # Start Menu System - Loy
    state = MENU
    running = True

    while running:
        clock.tick(60)
        float_time += 0.05
        menu_camera_x -= 4  # speed of star movement

        # Draw Menu - Loy
        if state == MENU:
            background.update_and_draw(win, (menu_camera_x, menu_camera_y))
            start_rect, quit_rect = draw_menu(win, screen_width, screen_height, truck_img, float_time)
            

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
                    if start_rect.collidepoint(event.pos):
                        state = GAME
                    elif quit_rect.collidepoint(event.pos):
                        running = False

            # Game Input - Loy
            elif state == GAME:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU

                # Click-to-shoot ONLY in GAME
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
                    if bullet:
                        bullets.append(bullet)

        
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
                    
            for bullet in bullets[:]:
                bullet.update()

                bullet_rect = pygame.Rect (
                    bullet.pos.x - bullet.radius,
                    bullet.pos.y - bullet.radius,
                    bullet.radius * 2,
                    bullet.radius * 2
                )

                for enemy in enemies [:]:
                    if bullet_rect.colliderect(enemy.rect):
                        enemy.take_damage(10) 

                        if bullet in bullets:
                            bullets.remove(bullet)

                        if enemy.health <= 0:
                            enemies.remove(enemy)
                        
                        break

            # Removed win.fill because background.update_and_draw handles it - Meheraj
            draw_objects(win, player, enemies, bullets, world.walls, camera, background)  # Updated to pass camera and background - Meheraj

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())


