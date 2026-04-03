# main menu
import pygame
import asyncio
import math
import sys
from src.render import draw_game_over, draw_credits, draw_menu
from src.background import SpaceBackground 
from src.game import game as dungeon_game

# NOTE:
# When debugging pygbag web crashes, temporarily wrap main() in a try/except
# with traceback.print_exc() to surface errors in the browser console.

# Start Menu - Loy
MENU = "menu"
CREDITS = "Credits"

async def run_game(win, screen_width, screen_height, background, truck_img): # checks the status of the character
    result = await dungeon_game(win)
    if result != "dead":
        return
    
    clock = pygame.time.Clock()
    float_time = 0
    menu_cam_x = 0

    while True:
        clock.tick(60)
        float_time += 0.05
        menu_cam_x -= 2
    

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return

        win.fill((0, 0, 0))
        background.update_and_draw(win, (menu_cam_x, 0))
        draw_game_over(win, screen_width, screen_height, truck_img, float_time) # calls game over from render
        pygame.display.flip()
        await asyncio.sleep(0)


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
                            await run_game(win, screen_width, screen_height, background, truck_img)
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
                            await run_game(win, screen_width, screen_height, background, truck_img)

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