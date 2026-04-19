import pygame
import math


class InventoryUI:
    # ── Visual constants copied from TutorialPopup ──────────────────────
    C_BG          = (5, 5, 20, 220)
    C_BORDER      = (60, 180, 255)
    C_BORDER2     = (30,  90, 160)
    C_HEADING     = (90, 220, 255)
    C_BODY        = (190, 215, 240)
    C_MUTED       = (90, 120, 150)
    C_ICON_BG     = (20,  50,  90)
    C_ICON_TEXT   = (60, 200, 255)
    C_BTN_NORMAL  = (25,  55,  95)
    C_BTN_HOVER   = (40,  90, 155)
    C_BTN_TEXT    = (160, 210, 255)
    C_GOLD        = (255, 215,  80)

    ANIM_SPEED  = 8
    FADE_SPEED  = 18
    SCAN_PERIOD = 3.0

    def __init__(self, screen_width: int, screen_height: int):
        self.sw = screen_width
        self.sh = screen_height

        # Panel dimensions (same proportions as TutorialPopup)
        self.pw = min(560, screen_width - 80)
        self.ph = 400
        self.px = (screen_width  - self.pw) // 2
        self.py = (screen_height - self.ph) // 2
        
        self.panel_rect = pygame.Rect(self.px, self.py, self.pw, self.ph)

        # Animation state
        self._alpha   = 0
        self._slide_y = 40
        self._scan_t  = 0.0
        self._visible = False   # internal; toggled by game loop via draw()

        # Fonts — identical family/sizes to TutorialPopup
        self.font_heading = pygame.font.SysFont("Pixellari.ttf", 28, bold=True)
        self.font_body    = pygame.font.SysFont("Pixellari.ttf", 18)
        self.font_icon    = pygame.font.SysFont("Pixellari.ttf", 22, bold=True)
        self.font_btn     = pygame.font.SysFont("Pixellari.ttf", 18, bold=True)

        # Close button rect (screen-space, updated each draw)
        self._btn_close  = pygame.Rect(0, 0, 0, 0)
        self._hover_close = False
    

    def draw(self, surface: pygame.Surface, money: int, visible: bool = True):
        """Call every frame while the inventory key is held / toggled on."""
        if not visible:
            self._alpha   = 0
            self._slide_y = 40
            return

        # Animate in
        self._alpha   = min(255, self._alpha   + self.FADE_SPEED)
        self._slide_y = max(0,   self._slide_y - self.ANIM_SPEED)
        self._scan_t += 1 / 60

        mx, my = pygame.mouse.get_pos()
        self._hover_close = self._btn_close.collidepoint(mx, my)

        draw_y = self.py + self._slide_y

        # ── Dim overlay ──────────────────────────────────────────────
        dim = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        dim.fill((5, 5, 15, int(0.7 * self._alpha)))
        surface.blit(dim, (0, 0))

        # ── Panel surface ────────────────────────────────────────────
        panel = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA)
        panel.fill((*self.C_BG[:3], int(self.C_BG[3] * self._alpha / 255)))

        # Double border ring
        pygame.draw.rect(panel, self.C_BORDER2, (0, 0, self.pw, self.ph), 2)
        pygame.draw.rect(panel, self.C_BORDER,  (3, 3, self.pw - 6, self.ph - 6), 1)

        self._draw_corners(panel)
        self._draw_scanlines(panel)

        # Icon box
        icon_rect = pygame.Rect(24, 28, 60, 60)
        pygame.draw.rect(panel, self.C_ICON_BG, icon_rect, border_radius=6)
        icon_surf = self.font_icon.render("[I]", True, self.C_ICON_TEXT)
        panel.blit(icon_surf, (
            icon_rect.centerx - icon_surf.get_width()  // 2,
            icon_rect.centery - icon_surf.get_height() // 2,
        ))

        # Heading 
        heading_surf = self.font_heading.render("Inventory", True, self.C_HEADING)
        panel.blit(heading_surf, (icon_rect.right + 16, 36))

        # Separator
        sep_y = icon_rect.bottom + 18
        pygame.draw.line(panel, self.C_BORDER2, (20, sep_y), (self.pw - 20, sep_y), 1)

        # Body content 
        body_y = sep_y + 18

        # Coins row with colour accent
        coin_label = self.font_body.render("Space Bucks", True, self.C_MUTED)
        coin_value = self.font_body.render(f"  $  {money}", True, self.C_GOLD)
        panel.blit(coin_label, (28, body_y))
        panel.blit(coin_value, (28 + coin_label.get_width(), body_y))
        body_y += self.font_body.get_linesize() + 10

        # Horizontal rule under coins
        pygame.draw.line(panel, self.C_ICON_BG,(28, body_y), (self.pw - 28, body_y), 1)
        body_y += 14

        # Placeholder item slots (3 × 2 grid)
        slot_size  = 64
        slot_gap   = 14
        cols       = 5
        grid_w     = cols * slot_size + (cols - 1) * slot_gap
        grid_x     = (self.pw - grid_w) // 2

        for i in range(cols):
            sx = grid_x + i * (slot_size + slot_gap)
            slot_rect = pygame.Rect(sx, body_y, slot_size, slot_size)
            pygame.draw.rect(panel, self.C_ICON_BG,  slot_rect, border_radius=6)
            pygame.draw.rect(panel, self.C_BORDER2,  slot_rect, 1, border_radius=6)
            # Empty slot indicator
            dash = self.font_btn.render("—", True, self.C_MUTED)
            panel.blit(dash, (
                slot_rect.centerx - dash.get_width()  // 2,
                slot_rect.centery - dash.get_height() // 2,
            ))

        body_y += slot_size + slot_gap

        # Second row
        for i in range(cols):
            sx = grid_x + i * (slot_size + slot_gap)
            slot_rect = pygame.Rect(sx, body_y, slot_size, slot_size)
            pygame.draw.rect(panel, self.C_ICON_BG,  slot_rect, border_radius=6)
            pygame.draw.rect(panel, self.C_BORDER2,  slot_rect, 1, border_radius=6)
            dash = self.font_btn.render("—", True, self.C_MUTED)
            panel.blit(dash, (
                slot_rect.centerx - dash.get_width()  // 2,
                slot_rect.centery - dash.get_height() // 2,
            ))

        # Close button (top-right, same position as TutorialPopup) ─
        close_rect  = pygame.Rect(self.pw - 26, 8, 18, 18)
        close_color = (140, 30, 30) if self._hover_close else self.C_BTN_NORMAL
        pygame.draw.rect(panel, close_color, close_rect, border_radius=3)
        x_surf = self.font_btn.render("X", True, self.C_BTN_TEXT)
        panel.blit(x_surf, (
            close_rect.centerx - x_surf.get_width()  // 2,
            close_rect.centery - x_surf.get_height() // 2,
        ))
        self._btn_close = close_rect.move(self.px, draw_y)

        # Hint bar 
        hint_surf = self.font_body.render("Press I to close", True, self.C_MUTED)
        panel.blit(hint_surf, (
            self.pw // 2 - hint_surf.get_width() // 2,
            self.ph - 32,
        ))

        panel.set_alpha(self._alpha)
        surface.blit(panel, (self.px, draw_y))

    # Internal helpers (identical to TutorialPopup)

    def _draw_corners(self, surf: pygame.Surface):
        L, c = 10, self.C_BORDER
        W, H = self.pw, self.ph
        for cx, cy, sx, sy in [
            (4, 4, 1, 1),
            (W-4-L, 4, -1,1),
            (4, H-4-L, 1, -1),
            (W-4-L, H-4-L,-1, -1),
        ]:
            pygame.draw.line(surf, c, (cx, cy), (cx + L * sx, cy), 2)
            pygame.draw.line(surf, c, (cx, cy), (cx, cy + L * sy), 2)

    def _draw_scanlines(self, surf: pygame.Surface):
        line_gap = 4
        offset   = int((self._scan_t % self.SCAN_PERIOD) / self.SCAN_PERIOD * self.ph)
        y        = -offset % line_gap
        while y < self.ph:
            sl = pygame.Surface((self.pw, 1), pygame.SRCALPHA)
            sl.fill((60, 180, 255, 10))
            surf.blit(sl, (0, y))
            y += line_gap