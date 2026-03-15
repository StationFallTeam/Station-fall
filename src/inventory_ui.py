import pygame

class InventoryUI:

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.title_font = pygame.font.SysFont(None, 64)
        self.text_font = pygame.font.SysFont(None, 40)

        # panel size
        self.panel_width = 500
        self.panel_height = 400

        self.panel_rect = pygame.Rect(
            (screen_width - self.panel_width) // 2,
            (screen_height - self.panel_height) // 2,
            self.panel_width,
            self.panel_height
        )

    def draw(self, win, coin_count):

        # dark transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        win.blit(overlay, (0, 0))

        # main panel
        pygame.draw.rect(win, (40, 40, 40), self.panel_rect, border_radius=12)
        pygame.draw.rect(win, (200, 200, 200), self.panel_rect, 3, border_radius=12)

        # title
        title = self.title_font.render("INVENTORY", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, self.panel_rect.top + 50))
        win.blit(title, title_rect)

        # coin display
        coin_text = self.text_font.render(f"Coins: {coin_count}", True, (255, 215, 0))
        coin_rect = coin_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        win.blit(coin_text, coin_rect)