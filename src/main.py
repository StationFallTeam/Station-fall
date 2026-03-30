# main menu
import pygame
import asyncio
import sys

from .player import Player
from .enemy import Enemy
from .render import draw_objects, apply_brightness, draw_credits, render_menu_screen, render_inventory_screen, render_game_over_screen
from .camera import Camera          # Added for camera - Meheraj
from .background import SpaceBackground # Added for parallax background - Meheraj
from .world import World
from .coin import Coin
from .inventory_ui import InventoryUI
from .floating_texts import FloatingText  # Added for floating damage text - Meheraj

# NOTE:
# When debugging pygbag web crashes, temporarily wrap main() in a try/except
# with traceback.print_exc() to surface errors in the browser console.

# Start Menu - Loy
MENU = "menu"
GAME = "game"
GAME_OVER = "game_over"
CREDITS = "Credits"
INVENTORY = "inventory"

<<<<<<< HEAD
=======
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

    credits_rect = pygame.Rect(0, 0, btn_w, btn_h)
    credits_rect.center = (screen_width // 2, screen_height // 2 + 210)

    quit_rect = pygame.Rect(0, 0, btn_w, btn_h)
    quit_rect.center = (screen_width // 2, screen_height // 2 + 300)

    mx, my = pygame.mouse.get_pos()

    def draw_button(rect, text):
        hover = rect.collidepoint(mx, my)
        color = (220, 220, 220) if hover else (170, 170, 170)
        pygame.draw.rect(win, color, rect, border_radius=12)
        pygame.draw.rect(win, (40, 40, 40), rect, 3, border_radius=12)

        label = btn_font.render(text, True, (0, 0, 0))
        win.blit(label, label.get_rect(center=rect.center))

    draw_button(start_rect, "Start")
    draw_button(credits_rect, "Credits")
    draw_button(quit_rect, "Quit")

    return start_rect, quit_rect, credits_rect

# Game over screen
def draw_game_over(win, screen_width, screen_height, truck_img, float_time):
    font = pygame.font.SysFont(None, 90)
    small_font = pygame.font.SysFont(None, 32)

    text = font.render("GAME OVER", True, (255, 0, 0))
    hint = small_font.render("Press ENTER to restart or ESC to quit", True, (255, 255, 255))

    win.blit(text, text.get_rect(center=(screen_width//2, screen_height//2 - 50)))
    win.blit(hint, hint.get_rect(center=(screen_width//2, screen_height//2 + 50)))

    # Floating truck (top of screen)
    float_offset = math.sin(float_time) * 15
    truck_rect = truck_img.get_rect()
    truck_rect.midtop = (screen_width // 2, 200 + float_offset)
    win.blit(truck_img, truck_rect)

# Credits screen - Wil
def draw_credits(win, screen_width, screen_height, background, float_time, menu_camera_x, menu_camera_y):
    background.update_and_draw(win, (menu_camera_x, menu_camera_y))

    title_font = pygame.font.SysFont(None, 72)
    name_font = pygame.font.SysFont(None, 42)
    role_font = pygame.font.SysFont(None, 30)
    hint_font = pygame.font.SysFont(None, 28)

    # Title
    title = title_font.render("CREDITS", True, (255, 255, 255))
    win.blit(title, title.get_rect(center=(screen_width // 2, 80)))

    # Divider line
    pygame.draw.line(win, (100, 100, 255), (screen_width // 2 - 200, 120), (screen_width // 2 + 200, 120), 2)

    team = [
        ("Wil Nahra",            "| Developer | Sprite Creation |"),
        ("Simon Halaszi",        "| Developer |"),
        ("Loy Ngo",              "| Developer |"),
        ("Meheraj Khatri",       "| Developer |"),
        ("Rowan",                "| Developer |"),
        ("Sebastian Bentancourt","| Developer |"),
        ("Yusairah Haque",       "| Developer |"),
        ("Zachary Evans",        "| Developer |"),
    ]

    start_y = 170
    spacing = 90

    for i, (name, role) in enumerate(team):
        y = start_y + i * spacing
        float_offset = math.sin(float_time + i * 0.4) * 4

        name_surf = name_font.render(name, True, (220, 220, 255))
        role_surf = role_font.render(role, True, (140, 140, 200))

        win.blit(name_surf, name_surf.get_rect(center=(screen_width // 2, y + float_offset)))
        win.blit(role_surf, role_surf.get_rect(center=(screen_width // 2, y + 32 + float_offset)))

    # ESC hint
    hint = hint_font.render("Press ESC to return", True, (160, 160, 160))
    win.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height - 40)))

>>>>>>> b2e0947da51f3ddadba5509e46e64acdb12c81f2
async def main(): 
    pygame.init()
    if sys.platform != "emscripten":
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
    inventory_ui = InventoryUI(screen_width, screen_height)
    coins = []
    floating_texts = [] # Initialize floating text list

    #load menu image
    truck_img = pygame.image.load("sprites/truck.png").convert_alpha()
    truck_img = pygame.transform.smoothscale(truck_img, (400, 250))
    float_time = 0
    menu_camera_x = 0
    menu_camera_y = 0

    gameOver_img = pygame.image.load("sprites/gameOver.png").convert_alpha()
    gameOver_img = pygame.transform.smoothscale(gameOver_img, (300, 150))

    # Create the camera and background objects - Meheraj
    camera = Camera(screen_width, screen_height)
    background = SpaceBackground(screen_width, screen_height)

    # music
    pygame.mixer.music.load("sound/starfield.ogg")
    #pygame.mixer.music.play(-1)
    music_volume = 0.5
    pygame.mixer.music.set_volume(music_volume)
    VOLUME_STEP = 0.1
    music_started = False

    # brightness
    brightness = 1.0
    BRIGHTNESS_STEP = 0.1

    # Start Menu System - Loy
    state = MENU
    running = True

    while running:
        clock.tick(60)
        float_time += 0.05
        menu_camera_x -= 4

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Global controls
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    music_volume = min(music_volume + VOLUME_STEP, 1.0)
                    pygame.mixer.music.set_volume(music_volume)
                    print(f"Volume increased to: {music_volume*100:.0f}%", flush=True)

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    music_volume = max(music_volume - VOLUME_STEP, 0.0)
                    pygame.mixer.music.set_volume(music_volume)
                    print(f"Volume decreased to: {music_volume*100:.0f}%", flush=True)

                # Use 9 / 0 for web reliability
                elif event.key == pygame.K_0:
                    brightness = min(brightness + BRIGHTNESS_STEP, 1.0)
                    print(f"Brightness increased to: {brightness*100:.0f}%", flush=True)

                elif event.key == pygame.K_9:
                    brightness = max(brightness - BRIGHTNESS_STEP, 0.2)
                    print(f"Brightness decreased to: {brightness*100:.0f}%", flush=True)

                # State-specific keyboard input
                elif state == MENU:
                    if event.key == pygame.K_RETURN:
                        state = GAME
                        if not music_started:
                            pygame.mixer.music.play(-1)
                            music_started = True
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                elif state == GAME:
                    if event.key == pygame.K_i:
                        state = INVENTORY
                    elif event.key == pygame.K_ESCAPE:
                        state = MENU

                elif state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        player.health = 100
                        player.rect.topleft = (100, 100)
                        bullets.clear()
                        enemies.clear()
                        enemies.append(Enemy(300, 300))
                        floating_texts.clear()
                        state = GAME
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                elif state == CREDITS:
                    if event.key == pygame.K_ESCAPE:
                        state = MENU

                elif state == INVENTORY:
                    if event.key == pygame.K_i:
                        state = GAME
                    elif event.key == pygame.K_ESCAPE:
                        state = MENU

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == MENU:
                    if start_rect.collidepoint(event.pos):
                        state = GAME
                        if not music_started:
                            pygame.mixer.music.play(-1)
                            music_started = True
                    elif credits_rect.collidepoint(event.pos):
                        state = CREDITS
                        if not music_started:
                            pygame.mixer.music.play(-1)
                            music_started = True
                    elif quit_rect.collidepoint(event.pos):
                        running = False

                elif state == GAME:
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
                    if bullet:
                        bullets.append(bullet)

        # ---------- DRAW / UPDATE PHASE ----------
        win.fill((0, 0, 0))

        if state == MENU:
            start_rect, quit_rect, credits_rect = render_menu_screen(
            win, screen_width, screen_height, background, menu_camera_x, 
            menu_camera_y, truck_img, float_time)

        elif state == GAME:
            keys = pygame.key.get_pressed()
            player.update(keys, world.walls)
            camera.update(player)

            # Update floating texts (fading/moving)
            floating_texts = [ft for ft in floating_texts if ft.update()]

            if player.health <= 0 or keys[pygame.K_k]:
                state = GAME_OVER
            else:
                player.rect = player.get_rect()

                for enemy in enemies:
                    enemy.update(player.rect)
                    if enemy.rect.colliderect(player.rect):
                        if not player.is_invincible:
                            player.take_damage(10)
                            # Action Effect: Player hit text
                            floating_texts.append(FloatingText(player.x, player.y - 20, "Player has been Hit!!! -10", color=(255, 0, 0)))

                for bullet in bullets[:]:
                    bullet.update()

                    bullet_rect = pygame.Rect(
                        int(bullet.pos.x - bullet.radius),
                        int(bullet.pos.y - bullet.radius),
                        bullet.radius * 2,
                        bullet.radius * 2
                    )

                    for enemy in enemies[:]:
                        if bullet_rect.colliderect(enemy.rect):
                            # Track enemy health before applying damage so we only show damage text
                            before_health = getattr(enemy, "health", None)
                            enemy.take_damage(10)
                            # Action Effect: Enemy hit text (only if damage was actually applied)
                            if before_health is not None and getattr(enemy, "health", before_health) < before_health:
                                floating_texts.append(FloatingText(enemy.x, enemy.y - 20, "-10", color=(255, 255, 0)))

                            if bullet in bullets:
                                bullets.remove(bullet)

                            if enemy.is_dead:
                                coins.append(Coin(enemy.rect.centerx, enemy.rect.centery, value=3))
                                enemies.remove(enemy)

                            break

                for coin in coins[:]:
                    coin.update()
                    if player.rect.colliderect(coin.rect):
                        player.money += coin.value
                        coins.remove(coin)

                draw_objects(win, player, enemies, bullets, world.walls, camera, background, coins, floating_texts)

        elif state == INVENTORY:
<<<<<<< HEAD
            render_inventory_screen(win, player, enemies, bullets, world.walls,
                                    camera, background, coins, inventory_ui)
=======
            background.update_and_draw(win, (camera.camera.x, camera.camera.y))
            draw_objects(win, player, enemies, bullets, world.walls, camera, background, coins, floating_texts)
            inventory_ui.draw(win, player.money)

>>>>>>> b2e0947da51f3ddadba5509e46e64acdb12c81f2
        elif state == GAME_OVER:
            render_game_over_screen(win, screen_width, screen_height, background, 
                                    menu_camera_x, menu_camera_y, gameOver_img, float_time)

        elif state == CREDITS:
            draw_credits(win, screen_width, screen_height, background, float_time, menu_camera_x, menu_camera_y)

        apply_brightness(win, brightness)
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())