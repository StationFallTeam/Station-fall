# main menu
import pygame
import asyncio
import math
import sys

from src.background import SpaceBackground 
from src.game import game as dungeon_game

# NOTE:
# When debugging pygbag web crashes, temporarily wrap main() in a try/except
# with traceback.print_exc() to surface errors in the browser console.

# Start Menu - Loy
MENU = "menu"
CREDITS = "Credits"

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
        ("Simon Halaszi",        "| Developer | Dungeon Master |"),
        ("Loy Ngo",              "| Developer |"),
        ("Mark",                 "| Developer |"),
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

async def main(): 
    pygame.init()
    if sys.platform != "emscripten":
        pygame.mixer.init()

    # Use same window size as playerInDungeon
    screen_width = 920
    screen_height = 920
    win = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Station Fall")

    clock = pygame.time.Clock()

    # Load menu images
    truck_img = pygame.image.load("sprites/truck.png").convert_alpha()
    truck_img = pygame.transform.scale(truck_img, (150, 150))
    float_time = 0
    menu_camera_x = 0
    menu_camera_y = 0

    # Background for menus
    background = SpaceBackground(screen_width, screen_height)

    # Music setup
    pygame.mixer.music.load("sound/starfield.ogg")
    music_volume = 0.5
    pygame.mixer.music.set_volume(music_volume)
    VOLUME_STEP = 0.1
    music_started = False

    # Brightness control
    brightness = 1.0
    BRIGHTNESS_STEP = 0.1

    # Start Menu System
    state = MENU
    running = True

    try:
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
                            if not music_started:
                                pygame.mixer.music.play(-1)
                                music_started = True
                            await dungeon_game(win)
                        elif event.key == pygame.K_ESCAPE:
                            running = False

                    elif state == CREDITS:
                        if event.key == pygame.K_ESCAPE:
                            state = MENU

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if state == MENU:
                        if start_rect.collidepoint(event.pos):
                            if not music_started:
                                pygame.mixer.music.play(-1)
                                music_started = True
                            await dungeon_game(win)
                            # After returning from dungeon, stay in menu
                        elif credits_rect.collidepoint(event.pos):
                            state = CREDITS
                            if not music_started:
                                pygame.mixer.music.play(-1)
                                music_started = True
                        elif quit_rect.collidepoint(event.pos):
                            running = False

            # ---------- DRAW / UPDATE PHASE ----------
            win.fill((0, 0, 0))

            if state == MENU:
                background.update_and_draw(win, (menu_camera_x, menu_camera_y))
                start_rect, quit_rect, credits_rect = draw_menu(
                    win, screen_width, screen_height, truck_img, float_time
                )

            elif state == CREDITS:
                draw_credits(win, screen_width, screen_height, background, float_time, menu_camera_x, menu_camera_y)

            # Apply brightness filter
            if brightness < 1.0:
                dark_surface = pygame.Surface((screen_width, screen_height))
                dark_surface.set_alpha(int((1.0 - brightness) * 255))
                dark_surface.fill((0, 0, 0))
                win.blit(dark_surface, (0, 0))

            pygame.display.flip()
            await asyncio.sleep(0)

    except asyncio.CancelledError:
        # Expected on Ctrl+C when the event loop cancels the running coroutine.
        pass
    finally:
        pygame.quit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass