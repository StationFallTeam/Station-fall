import pygame

class InventoryUI:

    def __init__(self, screen_width, screen_height):

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.panel_rect = pygame.Rect(
            screen_width // 2 - 200,
            screen_height // 2 - 150,
            400,
            300
        )

        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 28)

    def draw(self, screen, money):

        # dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(160)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))

        # panel
        pygame.draw.rect(screen, (40,40,40), self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, (200,200,200), self.panel_rect, 3, border_radius=12)

        # title
        title = self.font.render("Inventory", True, (255,255,255))
        screen.blit(title, (self.panel_rect.centerx - title.get_width()//2,
                            self.panel_rect.top + 20))

        # coin display
        coin_text = self.font.render(f"Coins: {money}", True, (255,215,0))
        screen.blit(coin_text, (self.panel_rect.left + 40,
                                self.panel_rect.top + 100))

        # hint
        hint = self.small_font.render("Press I to close", True, (200,200,200))
        screen.blit(hint, (self.panel_rect.centerx - hint.get_width()//2,
                           self.panel_rect.bottom - 40))