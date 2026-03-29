import pygame
import asyncio

MENU = 0
GAME = 1
CREDITS = 2

def apply_brightness(win, brightness):
    if brightness >= 1.0:
        return

    darkness = int((1.0 - brightness) * 255)
    overlay = pygame.Surface(win.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, darkness))
    win.blit(overlay, (0, 0))

def draw_button(win, rect, text, font):
    mx, my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx, my)
    color = (220, 220, 220) if hover else (170, 170, 170)

    pygame.draw.rect(win, color, rect, border_radius=12)
    pygame.draw.rect(win, (40, 40, 40), rect, 3, border_radius=12)

    label = font.render(text, True, (0, 0, 0))
    win.blit(label, label.get_rect(center=rect.center))

async def main():
    pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()

    screen_width, screen_height = 1000, 700
    win = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("pygbag input test")

    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)
    debug_font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()

    state = MENU
    running = True

    music_volume = 0.5
    VOLUME_STEP = 0.1
    brightness = 1.0
    BRIGHTNESS_STEP = 0.1

    start_rect = pygame.Rect(0, 0, 260, 60)
    start_rect.center = (screen_width // 2, screen_height // 2)

    credits_rect = pygame.Rect(0, 0, 260, 60)
    credits_rect.center = (screen_width // 2, screen_height // 2 + 90)

    quit_rect = pygame.Rect(0, 0, 260, 60)
    quit_rect.center = (screen_width // 2, screen_height // 2 + 180)

    while running:
        clock.tick(60)
        win.fill((25, 25, 35))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # volume
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    music_volume = min(music_volume + VOLUME_STEP, 1.0)
                    print(f"Volume increased to: {music_volume*100:.0f}%", flush=True)

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    music_volume = max(music_volume - VOLUME_STEP, 0.0)
                    print(f"Volume decreased to: {music_volume*100:.0f}%", flush=True)

                # brightness (use 9/0 for web reliability)
                elif event.key == pygame.K_9:
                    brightness = max(brightness - BRIGHTNESS_STEP, 0.2)
                    print(f"Brightness decreased to: {brightness*100:.0f}%", flush=True)

                elif event.key == pygame.K_0:
                    brightness = min(brightness + BRIGHTNESS_STEP, 1.0)
                    print(f"Brightness increased to: {brightness*100:.0f}%", flush=True)

                # menu/game state changes
                elif state == MENU:
                    if event.key == pygame.K_RETURN:
                        state = GAME
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                elif state in (GAME, CREDITS):
                    if event.key == pygame.K_ESCAPE:
                        state = MENU

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == MENU:
                    if start_rect.collidepoint(event.pos):
                        state = GAME
                    elif credits_rect.collidepoint(event.pos):
                        state = CREDITS
                    elif quit_rect.collidepoint(event.pos):
                        running = False

        if state == MENU:
            title = font.render("PYGBAG MENU TEST", True, (255, 255, 255))
            hint = small_font.render("Click buttons or press Enter | 9/0 brightness | +/- volume", True, (200, 200, 200))
            win.blit(title, title.get_rect(center=(screen_width // 2, 120)))
            win.blit(hint, hint.get_rect(center=(screen_width // 2, 170)))

            draw_button(win, start_rect, "Start", font)
            draw_button(win, credits_rect, "Credits", font)
            draw_button(win, quit_rect, "Quit", font)

        elif state == GAME:
            label = font.render("GAME STATE", True, (100, 255, 100))
            hint = small_font.render("Press ESC to return to menu", True, (220, 220, 220))
            win.blit(label, label.get_rect(center=(screen_width // 2, screen_height // 2)))
            win.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height // 2 + 60)))

        elif state == CREDITS:
            label = font.render("CREDITS STATE", True, (100, 180, 255))
            hint = small_font.render("Press ESC to return to menu", True, (220, 220, 220))
            win.blit(label, label.get_rect(center=(screen_width // 2, screen_height // 2)))
            win.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height // 2 + 60)))

        state_name = "MENU" if state == MENU else "GAME" if state == GAME else "CREDITS"
        debug = debug_font.render(
            f"STATE: {state_name} | VOL: {music_volume:.1f} | BRIGHT: {brightness:.1f}",
            True,
            (255, 255, 0)
        )
        win.blit(debug, (10, 10))

        apply_brightness(win, brightness)
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())