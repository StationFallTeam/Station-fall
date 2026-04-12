import pygame
import math

class TutorialPopup:
    # ------------------------------------------------------------------
    # Content pages (icon_char, heading, lines)
    # ------------------------------------------------------------------
    PAGES = [
        {
            "icon": ">>",
            "heading": "Welcome to Station Fall",
            "lines": [
                "You are stranded aboard a derelict space station.",
                "Fight your way through combat zones, collect",
                "coins, and make it back to the hub alive.",
                "",
                "Use the arrow buttons below to read the controls.",
            ],
        },
        {
            "icon": "[]",
            "heading": "Movement",
            "lines": [
                "W  —  move up",
                "A  —  move left",
                "S  —  move down",
                "D  —  move right",
                "",
                "Your character always faces the last direction moved.",
            ],
        },
        {
            "icon": "(*)",
            "heading": "Combat",
            "lines": [
                "Left Click  —  fire your blaster toward the cursor",
                "",
                "Enemies deal contact damage and ranged fire.",
                "You have brief invincibility frames after each hit.",
                "",
                "Kill all enemies to complete a combat room.",
            ],
        },
        {
            "icon": "[$]",
            "heading": "Coins & Shop",
            "lines": [
                "Defeated enemies drop coins automatically.",
                "Walk over coins to collect them.",
                "",
                "E  —  open the shop (stand near the shop terminal)",
                "I  —  open your inventory at any time",
                "",
                "Spend coins on healing kits and upgrades.",
            ],
        },
        {
            "icon": "[>]",
            "heading": "Hub & Dungeon",
            "lines": [
                "ENTER  —  travel to the dungeon (stand on the portal)",
                "R       —  return to the hub once ALL rooms are cleared",
                "",
                "The minimap in the top-right tracks your position.",
                "The room counter shows your dungeon progress.",
                "",
                "Complete every combat room before leaving!",
            ],
        },
        {
            "icon": "||",
            "heading": "Other Controls",
            "lines": [
                "ESC    —  pause menu  (Resume / Main Menu / Quit)",
                "+  /  -  —  raise / lower music volume",
                "0  /  9  —  raise / lower screen brightness",
                "",
                "Good luck, pilot.",
                "The station won't clear itself.",
            ],
        },
    ]

    # Colors matched to SpaceBackground aesthetic
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
    C_CLOSE_HOVER = (140,  30,  30)
    C_DOT_ACTIVE  = (60, 200, 255)
    C_DOT_IDLE    = (40,  70, 110)
    C_SCANLINE    = (255, 255, 255, 10)    

    ANIM_SPEED = 8          
    FADE_SPEED = 18         
    SCAN_PERIOD = 3.0       

    def __init__(self, screen_width: int, screen_height: int):
        self.sw = screen_width
        self.sh = screen_height

        # Panel dimensions
        self.pw = min(560, screen_width - 80)
        self.ph = 400
        self.px = (screen_width  - self.pw) // 2
        self.py = (screen_height - self.ph) // 2

        # State
        self.visible   = False
        self.page      = 0
        self._alpha    = 0          
        self._slide_y  = 40        
        self._scan_t   = 0.0       

        # Fonts
        self.font_heading = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_body    = pygame.font.SysFont("Consolas", 16)
        self.font_icon    = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_btn     = pygame.font.SysFont("Consolas", 15, bold=True)
        self.font_page    = pygame.font.SysFont("Consolas", 13)

        # Interactive button rects (updated each frame)
        self._btn_prev  = pygame.Rect(0, 0, 0, 0)
        self._btn_next  = pygame.Rect(0, 0, 0, 0)
        self._btn_close = pygame.Rect(0, 0, 0, 0)

        # Hover states
        self._hover_prev  = False
        self._hover_next  = False
        self._hover_close = False
        # ----------------------------------------------

        self._build_panel_surface()

    def show(self, page: int = 0):
        self.visible  = True
        self.page     = page
        self._alpha   = 0
        self._slide_y = 40

    def hide(self):
        self.visible = False

    def update(self, events: list):
        if not self.visible:
            return

        if self._alpha < 255:
            self._alpha = min(255, self._alpha + self.FADE_SPEED)
        if self._slide_y > 0:
            self._slide_y = max(0, self._slide_y - self.ANIM_SPEED)

        self._scan_t += 1 / 60

        mx, my = pygame.mouse.get_pos()
        self._hover_prev  = self._btn_prev.collidepoint(mx, my)
        self._hover_next  = self._btn_next.collidepoint(mx, my)
        self._hover_close = self._btn_close.collidepoint(mx, my)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.hide()
                elif event.key == pygame.K_LEFT:
                    self._prev_page()
                elif event.key == pygame.K_RIGHT:
                    self._next_page()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._hover_close:
                    self.hide()
                elif self._hover_prev:
                    self._prev_page()
                elif self._hover_next:
                    self._next_page()

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Dim background overlay
        dim = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        dim.fill((5, 5, 15, int(0.7 * self._alpha))) 
        surface.blit(dim, (0, 0))

        draw_y = self.py + self._slide_y
        panel = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA)
        panel.fill((*self.C_BG[:3], int(self.C_BG[3] * self._alpha / 255)))

        pygame.draw.rect(panel, self.C_BORDER2, (0, 0, self.pw, self.ph), 2)
        pygame.draw.rect(panel, self.C_BORDER,  (3, 3, self.pw - 6, self.ph - 6), 1)

        self._draw_corners(panel)
        self._draw_scanlines(panel)

        # Icon
        icon_rect = pygame.Rect(24, 28, 60, 60)
        pygame.draw.rect(panel, self.C_ICON_BG, icon_rect, border_radius=6)
        icon_text = self.font_icon.render(self.PAGES[self.page]["icon"], True, self.C_ICON_TEXT)
        panel.blit(icon_text, (icon_rect.centerx - icon_text.get_width() // 2, 
                               icon_rect.centery - icon_text.get_height() // 2))

        heading_surf = self.font_heading.render(self.PAGES[self.page]["heading"], True, self.C_HEADING)
        panel.blit(heading_surf, (icon_rect.right + 16, 36))

        sep_y = icon_rect.bottom + 18
        pygame.draw.line(panel, self.C_BORDER2, (20, sep_y), (self.pw - 20, sep_y), 1)

        # Body Lines
        body_y = sep_y + 14
        for line in self.PAGES[self.page]["lines"]:
            if line == "":
                body_y += 8
                continue
            if "\u2014" in line or "  -  " in line:
                self._draw_keybind_line(panel, line, 28, body_y)
            else:
                surf = self.font_body.render(line, True, self.C_BODY)
                panel.blit(surf, (28, body_y))
            body_y += self.font_body.get_linesize() + 2

        # Buttons
        btn_y, btn_h, btn_w = self.ph - 36, 26, 80
        prev_rect  = pygame.Rect(20, btn_y, btn_w, btn_h)
        next_rect  = pygame.Rect(self.pw - 20 - btn_w, btn_y, btn_w, btn_h)
        close_rect = pygame.Rect(self.pw - 26, 8, 18, 18)

        self._btn_prev  = prev_rect.move(self.px, draw_y)
        self._btn_next  = next_rect.move(self.px, draw_y)
        self._btn_close = close_rect.move(self.px, draw_y)

        if self.page > 0:
            col = self.C_BTN_HOVER if self._hover_prev else self.C_BTN_NORMAL
            pygame.draw.rect(panel, col, prev_rect, border_radius=4)
            lbl = self.font_btn.render("< PREV", True, self.C_BTN_TEXT)
            panel.blit(lbl, (prev_rect.centerx - lbl.get_width() // 2, prev_rect.centery - lbl.get_height() // 2))

        col = self.C_BTN_HOVER if self._hover_next else self.C_BTN_NORMAL
        pygame.draw.rect(panel, col, next_rect, border_radius=4)
        label = "NEXT >" if self.page < len(self.PAGES) - 1 else "DONE"
        lbl = self.font_btn.render(label, True, self.C_BTN_TEXT)
        panel.blit(lbl, (next_rect.centerx - lbl.get_width() // 2, next_rect.centery - lbl.get_height() // 2))

        panel.set_alpha(self._alpha)
        surface.blit(panel, (self.px, draw_y))

    def _next_page(self):
        if self.page < len(self.PAGES) - 1: self.page += 1
        else: self.hide()

    def _prev_page(self):
        if self.page > 0: self.page -= 1

    def _draw_keybind_line(self, surf, line, x, y):
        for sep in ["\u2014", "  -  "]:
            if sep in line:
                parts = line.split(sep, 1)
                k_surf = self.font_body.render(parts[0].rstrip(), True, self.C_ICON_TEXT)
                s_surf = self.font_body.render(f" {sep} ", True, self.C_MUTED)
                d_surf = self.font_body.render(parts[1].lstrip(), True, self.C_BODY)
                surf.blit(k_surf, (x, y))
                surf.blit(s_surf, (x + k_surf.get_width(), y))
                surf.blit(d_surf, (x + k_surf.get_width() + s_surf.get_width(), y))
                return
        surf.blit(self.font_body.render(line, True, self.C_BODY), (x, y))

    def _draw_corners(self, surf):
        L, c = 10, self.C_BORDER
        W, H = self.pw, self.ph
        for cx, cy, sx, sy in [(4,4,1,1), (W-4-L,4,-1,1), (4,H-4-L,1,-1), (W-4-L,H-4-L,-1,-1)]:
            pygame.draw.line(surf, c, (cx, cy), (cx + L * sx, cy), 2)
            pygame.draw.line(surf, c, (cx, cy), (cx, cy + L * sy), 2)

    def _draw_scanlines(self, surf):
        line_gap = 4
        offset = int((self._scan_t % self.SCAN_PERIOD) / self.SCAN_PERIOD * self.ph)
        y = -offset % line_gap
        while y < self.ph:
            sl = pygame.Surface((self.pw, 1), pygame.SRCALPHA)
            sl.fill((60, 180, 255, 10))
            surf.blit(sl, (0, y))
            y += line_gap

def should_show_first_launch_tutorial() -> bool:
    import pathlib
    flag = pathlib.Path(".tutorial_shown")
    if flag.exists(): return False
    try: flag.touch()
    except OSError: pass   
    return True