import pygame
import math
from src.ui import draw_health_bar, draw_money
from dungeongen.classes import CombatRoom

# Pause menu - Wil
def draw_pause_menu(win, screen_width, screen_height):
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    win.blit(overlay, (0, 0))

    title_font = pygame.font.SysFont(None, 72)
    btn_font = pygame.font.SysFont(None, 48)

    title = title_font.render("PAUSED", True, (255, 255, 255))
    win.blit(title, title.get_rect(center=(screen_width // 2, screen_height // 2 - 140)))

    btn_w, btn_h = 260, 60
    mx, my = pygame.mouse.get_pos()

    def make_btn(label, cy):
        rect = pygame.Rect(0, 0, btn_w, btn_h)
        rect.center = (screen_width // 2, cy)
        hover = rect.collidepoint(mx, my)
        color = (220, 220, 220) if hover else (170, 170, 170)
        pygame.draw.rect(win, color, rect, border_radius=12)
        pygame.draw.rect(win, (40, 40, 40), rect, 3, border_radius=12)
        lbl = btn_font.render(label, True, (0, 0, 0))
        win.blit(lbl, lbl.get_rect(center=rect.center))
        return rect

    resume_rect = make_btn("Resume",   screen_height // 2 - 30)
    menu_rect   = make_btn("Main Menu", screen_height // 2 + 60)
    quit_rect   = make_btn("Quit",      screen_height // 2 + 150)

    return resume_rect, menu_rect, quit_rect

def draw_objects(win, player, enemies, bullets, camera, background, coins, floating_texts, dungeon, tile_size):
    # 1. Draw the parallax background first using camera position
    background.update_and_draw(win, (camera.camera.x, camera.camera.y))

    # 2. Draw dungeon or walls
    if dungeon and dungeon.draw:
        # Use dungeon rendering pipeline instead of manual walls
        # Use provided tile_size or fall back to dungeon's tile_size
        render_tile_size = tile_size or dungeon.tile_size
        dungeon.draw(
            surface=win,
            tile_size=render_tile_size,
            cam_x=-camera.camera.x,
            cam_y=-camera.camera.y,
            show_grid=False,
            show_sprites=True,
        )
    
    if dungeon and dungeon.rooms and tile_size:
        # Let each combat room draw its own spawn warnings
        for room in dungeon.rooms:
            if isinstance(room, CombatRoom):
                room.draw_spawn_warnings(win, camera, tile_size)

    # 3. Draw entities relative to camera
    for coin in coins:
        coin.draw(win, camera)

    for bullet in bullets: 
        bullet.draw(win, camera)

    for enemy in enemies:
        enemy.draw(win, camera)

    # 4. Draw the player (passing camera for offset)
    player.draw(win, camera)

    # 5. Draw Floating Action Text (Damage numbers, etc.)
    # We draw these after entities so they appear on top of characters
    for ft in floating_texts:
        ft.draw(win, camera)

    # 6. Draw Fixed HUD elements (Screen Space)
    # Player HUD health bar
    draw_health_bar(win, player.health, player.max_health, 20, 20, 250, 18)
    draw_money(win, player.money, 20, 50)

    # 7. Draw hovering enemy health bars (World Space)
    for enemy in enemies:
        screen_rect = camera.apply(enemy.rect)
        
        draw_health_bar(
            win,
            enemy.health,
            enemy.max_health,
            screen_rect.x,
            screen_rect.y - 10,
            screen_rect.width,
            6,
            border=1
        )

def apply_brightness(win, brightness):
    if brightness >= 1.0:
        return
    
    darkness = int((1.0 - brightness) * 255)
    
    overlay = pygame.Surface(win.get_size())
    overlay.fill((0, 0, 0))
    overlay.set_alpha(darkness)

    win.blit(overlay, (0, 0))

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
    truck_rect.midtop = (screen_width // 2, 200 + int(float_offset))
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
        ("Simon Halaszi",        "| Developer | Dungeon Master |"),
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
