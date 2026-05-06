# main menu
import pygame
import asyncio
import math
import sys
import random
from src.render import draw_game_over, draw_credits, draw_menu, draw_game_settings_menu
from src.background import SpaceBackground 
from src.game import game as dungeon_game
from src.assets import resolve_asset_path
import traceback
import os
os.environ['SDL_VIDEO_HIGHDPI_DISABLED'] = '1'

# NOTE:
# When debugging pygbag web crashes, temporarily wrap main() in a try/except
# with traceback.print_exc() to surface errors in the browser console.

#raise RuntimeError("TEST: main.py is definitely being executed")

# Start Menu - Loy
MENU = "menu"
SETTINGS = "settings"
CREDITS = "Credits"


def generate_menu_seed():
    return random.randint(0, 2_147_483_647)


def parse_seed_input(seed_input, fallback_seed):
    if not seed_input:
        return fallback_seed
    try:
        return int(seed_input)
    except ValueError:
        return fallback_seed

async def run_game(win, screen_width, screen_height, background, truck_img, settings): # checks the status of the character
    result = await dungeon_game(win, settings)
    
    if isinstance(result, tuple):
        status, returned_settings = result
        settings.update(returned_settings)
        result = status
    
    if result == "quit":
        settings['dungeon_runs'] = 0
        return "quit"

    if result != "dead":
        settings['dungeon_runs'] = 0
        return result

    settings['dungeon_runs'] = 0
    
    clock = pygame.time.Clock()
    float_time = 0
    menu_cam_x = 0

    # music set to dead
    pygame.mixer.music.stop()
    music_volume = pygame.mixer.music.get_volume()
    pygame.mixer.music.load(resolve_asset_path("sound/uncomfortable-panels.ogg"))
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)

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
        draw_game_over(win, screen_width, screen_height, truck_img, float_time)
        
        # Apply brightness filter
        brightness = settings.get('brightness', 1.0)
        if brightness < 1.0:
            dark_surface = pygame.Surface((screen_width, screen_height))
            dark_surface.set_alpha(int((1.0 - brightness) * 255))
            dark_surface.fill((0, 0, 0))
            win.blit(dark_surface, (0, 0))
        
        pygame.display.flip()
        await asyncio.sleep(0)


async def main(): 
    try:
        pygame.init()
        if sys.platform != "emscripten":
            pygame.mixer.init()

        # Use monitor resolution for window size
        if sys.platform != "emscripten":
            info = pygame.display.Info()
            screen_width = info.current_w
            screen_height = info.current_h
        else:
            screen_width = 920
            screen_height = 920
        win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Station Fall")

        clock = pygame.time.Clock()

        # Load menu images
        truck_img = pygame.image.load(resolve_asset_path("sprites/truck.png")).convert_alpha()
        truck_img = pygame.transform.scale(truck_img, (150, 150))
        float_time = 0
        menu_camera_x = 0
        menu_camera_y = 0

        # Background for menus
        background = SpaceBackground(screen_width, screen_height)

        # Music setup
        pygame.mixer.music.load(resolve_asset_path("sound/starfield.ogg"))
        music_volume = 0.5
        pygame.mixer.music.set_volume(music_volume)
        VOLUME_STEP = 0.1

        waiting = True
        font = pygame.font.SysFont(None, 48)
        while waiting:
            win.fill((0, 0, 0))
            background.update_and_draw(win, (0, 0))
            text = font.render("Click or press any key to start", True, (255, 255, 255))
            win.blit(text, (screen_width//2 - text.get_width()//2, screen_height//2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    waiting = False
            await asyncio.sleep(0)

        pygame.mixer.music.play(-1)

        # Brightness control
        brightness = 1.0
        BRIGHTNESS_STEP = 0.1
        base_seed = generate_menu_seed()
        seed_input_text = str(base_seed)
        seed_input_active = False

        # Settings dictionary to pass to and from the game
        current_settings = {
            'music_volume': music_volume,
            'brightness': brightness,
            'dungeon_runs': 0,
            'base_seed': base_seed,
        }

        # Start Menu System
        state = MENU
        running = True
        start_rect = pygame.Rect(0, 0, 0, 0)
        quit_rect = pygame.Rect(0, 0, 0, 0)
        credits_rect = pygame.Rect(0, 0, 0, 0)
        random_seed_rect = pygame.Rect(0, 0, 0, 0)
        seed_input_rect = pygame.Rect(0, 0, 0, 0)
        begin_game_rect = pygame.Rect(0, 0, 0, 0)
        back_rect = pygame.Rect(0, 0, 0, 0)

        try:
            while running:
                clock.tick(60)
                float_time += 0.05
                menu_camera_x -= 4

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.KEYDOWN:
                        if state == SETTINGS and seed_input_active:
                            if event.key == pygame.K_BACKSPACE:
                                seed_input_text = seed_input_text[:-1]
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                                seed_input_active = False
                            elif event.key == pygame.K_ESCAPE:
                                seed_input_active = False
                                state = MENU
                            elif event.unicode and event.unicode.isdigit() and len(seed_input_text) < 18:
                                seed_input_text += event.unicode
                            continue

                        # Global controls
                        if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                            music_volume = min(music_volume + VOLUME_STEP, 1.0)
                            current_settings['music_volume'] = music_volume
                            pygame.mixer.music.set_volume(music_volume)
                            print(f"Volume increased to: {music_volume*100:.0f}%", flush=True)

                        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                            music_volume = max(music_volume - VOLUME_STEP, 0.0)
                            current_settings['music_volume'] = music_volume
                            pygame.mixer.music.set_volume(music_volume)
                            print(f"Volume decreased to: {music_volume*100:.0f}%", flush=True)

                        # Use 9 / 0 for web reliability
                        elif event.key == pygame.K_0:
                            brightness = min(brightness + BRIGHTNESS_STEP, 1.0)
                            current_settings['brightness'] = brightness
                            print(f"Brightness increased to: {brightness*100:.0f}%", flush=True)

                        elif event.key == pygame.K_9:
                            brightness = max(brightness - BRIGHTNESS_STEP, 0.2)
                            current_settings['brightness'] = brightness
                            print(f"Brightness decreased to: {brightness*100:.0f}%", flush=True)

                        # State-specific keyboard input
                        elif state == MENU:
                            if event.key == pygame.K_RETURN:
                                state = SETTINGS
                                seed_input_active = True
                            elif event.key == pygame.K_ESCAPE:
                                running = False

                        elif state == SETTINGS:
                            if event.key == pygame.K_RETURN:
                                selected_seed = parse_seed_input(seed_input_text, current_settings.get('base_seed', base_seed))
                                current_settings['base_seed'] = selected_seed
                                seed_input_text = str(selected_seed)
                                seed_input_active = False

                                result = await run_game(win, screen_width, screen_height, background, truck_img, current_settings)
                                music_volume = current_settings.get('music_volume', music_volume)
                                brightness = current_settings.get('brightness', brightness)
                                base_seed = current_settings.get('base_seed', base_seed)
                                seed_input_text = str(base_seed)
                                pygame.mixer.music.set_volume(music_volume)
                                if result == "quit":
                                    running = False
                                    continue
                                state = MENU
                            elif event.key == pygame.K_r:
                                base_seed = generate_menu_seed()
                                current_settings['base_seed'] = base_seed
                                seed_input_text = str(base_seed)
                                seed_input_active = False
                            elif event.key == pygame.K_ESCAPE:
                                state = MENU
                                seed_input_active = False

                        elif state == CREDITS:
                            if event.key == pygame.K_ESCAPE:
                                state = MENU

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if state == MENU:
                            if start_rect.collidepoint(event.pos):
                                state = SETTINGS
                                seed_input_active = True
                            elif credits_rect.collidepoint(event.pos):
                                state = CREDITS
                            elif quit_rect.collidepoint(event.pos):
                                running = False

                        elif state == SETTINGS:
                            if begin_game_rect.collidepoint(event.pos):
                                selected_seed = parse_seed_input(seed_input_text, current_settings.get('base_seed', base_seed))
                                current_settings['base_seed'] = selected_seed
                                seed_input_text = str(selected_seed)
                                seed_input_active = False

                                result = await run_game(win, screen_width, screen_height, background, truck_img, current_settings)
                                music_volume = current_settings.get('music_volume', music_volume)
                                brightness = current_settings.get('brightness', brightness)
                                base_seed = current_settings.get('base_seed', base_seed)
                                seed_input_text = str(base_seed)
                                pygame.mixer.music.set_volume(music_volume)
                                if result == "quit":
                                    running = False
                                    continue
                                state = MENU
                            elif random_seed_rect.collidepoint(event.pos):
                                base_seed = generate_menu_seed()
                                current_settings['base_seed'] = base_seed
                                seed_input_text = str(base_seed)
                                seed_input_active = False
                            elif seed_input_rect.collidepoint(event.pos):
                                seed_input_active = True
                            elif back_rect.collidepoint(event.pos):
                                state = MENU
                                seed_input_active = False
                            else:
                                seed_input_active = False
                    
                    elif event.type == pygame.VIDEORESIZE:
                        screen_width, screen_height = event.w, event.h
                        win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                        background = SpaceBackground(screen_width, screen_height)

                # ---------- DRAW / UPDATE PHASE ----------
                
                
                win.fill((0, 0, 0))

                if state == MENU:
                    background.update_and_draw(win, (menu_camera_x, menu_camera_y))
                    start_rect, quit_rect, credits_rect = draw_menu(
                        win,
                        screen_width,
                        screen_height,
                        truck_img,
                        float_time,
                    )

                elif state == SETTINGS:
                    background.update_and_draw(win, (menu_camera_x, menu_camera_y))
                    begin_game_rect, random_seed_rect, seed_input_rect, back_rect = draw_game_settings_menu(
                        win,
                        screen_width,
                        screen_height,
                        truck_img,
                        float_time,
                        seed_input_text,
                        seed_input_active=seed_input_active,
                    )

                elif state == CREDITS:
                    draw_credits(win, screen_width, screen_height, background, float_time, menu_camera_x, menu_camera_y, truck_img)

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

    except Exception:
        traceback.print_exc()
        raise
    finally:
        pygame.quit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass