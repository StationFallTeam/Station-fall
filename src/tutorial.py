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

    # Speeds increased for a snappier feel
    ANIM_SPEED = 12          
    FADE_SPEED = 25         
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

        # Fonts - Use direct loading for speed
        try:
            self.font_heading = pygame.font.Font("Pixellari.ttf", 28)
            self.font_body    = pygame.font.Font("Pixellari.ttf", 18)
            self.font_icon    = pygame.font.Font("Pixellari.ttf", 22)
            self.font_btn     = pygame.font.Font("Pixellari.ttf", 18)
        except:
            self.font_heading = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_body    = pygame.font.SysFont("Arial", 18)
            self.font_icon    = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_btn     = pygame.font.SysFont("Arial", 18, bold=True)

        # Pre-create surfaces for blitting (The Performance Fix)
        self.panel_surface = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA).convert_alpha()
        self.dim_overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA).convert_alpha()
        
        # Interactive button rects
        self._btn_prev  = pygame.Rect(0, 0, 0, 0)
        self._btn_next  = pygame.Rect(0, 0, 0, 0)

        # Hover states
        self._hover_prev  = False
        self._hover_next  = False
        
        # Cache text surfaces
        self.page_surfaces = []
        self._pre_render_all_pages()

    def _pre_render_all_pages(self):
        """Creates static surfaces for each page to avoid rendering every frame."""
        for page_data in self.PAGES:
            temp_surf = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA).convert_alpha()
            
            # Heading
            h_surf = self.font_heading.render(page_data["heading"], True, self.C_HEADING)
            temp_surf.blit(h_surf, (100, 36))

            # Body Lines
            sep_y = 28 + 60 + 18
            body_y = sep_y + 14
            for line in page_data["lines"]:
                if line == "":
                    body_y += 8
                    continue
                
                line_surf = self._render_line_internal(line)
                temp_surf.blit(line_surf, (28, body_y))
                body_y += self.font_body.get_linesize() + 2
                
            self.page_surfaces.append(temp_surf)

    def _render_line_internal(self, line):
        """Helper to create text surfaces for keybind lines."""
        for sep in ["\u2014", "  -  "]:
            if sep in line:
                parts = line.split(sep, 1)
                k = self.font_body.render(parts[0].rstrip(), True, self.C_ICON_TEXT)
                s = self.font_body.render(f" {sep} ", True, self.C_MUTED)
                d = self.font_body.render(parts[1].lstrip(), True, self.C_BODY)
                
                res = pygame.Surface((self.pw, k.get_height()), pygame.SRCALPHA).convert_alpha()
                res.blit(k, (0, 0))
                res.blit(s, (k.get_width(), 0))
                res.blit(d, (k.get_width() + s.get_width(), 0))
                return res
        return self.font_body.render(line, True, self.C_BODY)

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

        # 1. ANIMATION CODE - Moves every frame regardless of input
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + self.FADE_SPEED)
        if self._slide_y > 0:
            self._slide_y = max(0, self._slide_y - self.ANIM_SPEED)

        self._scan_t += 1 / 60

        # Update hovers every frame
        mx, my = pygame.mouse.get_pos()
        self._hover_prev  = self._btn_prev.collidepoint(mx, my)
        self._hover_next  = self._btn_next.collidepoint(mx, my)

        # 2. INPUT CODE - Only runs when an event actually happens
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.hide()
                elif event.key == pygame.K_LEFT:
                    self._prev_page()
                elif event.key == pygame.K_RIGHT:
                    self._next_page()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._hover_prev:
                    self._prev_page()
                elif self._hover_next:
                    self._next_page()

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # 1. Background Dim
        self.dim_overlay.fill((5, 5, 15, int(0.7 * self._alpha))) 
        surface.blit(self.dim_overlay, (0, 0))

        draw_y = self.py + self._slide_y
        
        # 2. Panel Base
        self.panel_surface.fill((0, 0, 0, 0)) 
        self.panel_surface.fill((*self.C_BG[:3], int(self.C_BG[3] * self._alpha / 255)))

        # Decoration
        pygame.draw.rect(self.panel_surface, self.C_BORDER2, (0, 0, self.pw, self.ph), 2)
        pygame.draw.rect(self.panel_surface, self.C_BORDER,  (3, 3, self.pw - 6, self.ph - 6), 1)
        self._draw_corners(self.panel_surface)
        self._draw_scanlines(self.panel_surface)

        # 3. Page Icon
        icon_rect = pygame.Rect(24, 28, 60, 60)
        pygame.draw.rect(self.panel_surface, self.C_ICON_BG, icon_rect, border_radius=6)
        icon_txt = self.font_icon.render(self.PAGES[self.page]["icon"], True, self.C_ICON_TEXT)
        self.panel_surface.blit(icon_txt, (icon_rect.centerx - icon_txt.get_width() // 2, 
                                           icon_rect.centery - icon_txt.get_height() // 2))

        # Divider line
        pygame.draw.line(self.panel_surface, self.C_BORDER2, (20, 106), (self.pw - 20, 106), 1)

        # 4. BLIT CACHED CONTENT (Instant performance)
        self.panel_surface.blit(self.page_surfaces[self.page], (0, 0))

        # 5. Buttons
        self._draw_buttons(self.panel_surface)

        # Apply final transparency and blit to screen
        self.panel_surface.set_alpha(self._alpha)
        surface.blit(self.panel_surface, (self.px, draw_y))

    def _draw_buttons(self, surf):
        btn_y, btn_h, btn_w = self.ph - 36, 26, 80
        prev_rect  = pygame.Rect(20, btn_y, btn_w, btn_h)
        next_rect  = pygame.Rect(self.pw - 20 - btn_w, btn_y, btn_w, btn_h)

        # Update the collision rects for the mouse logic
        self._btn_prev = prev_rect.move(self.px, self.py + self._slide_y)
        self._btn_next = next_rect.move(self.px, self.py + self._slide_y)

        if self.page > 0:
            col = self.C_BTN_HOVER if self._hover_prev else self.C_BTN_NORMAL
            pygame.draw.rect(surf, col, prev_rect, border_radius=4)
            lbl = self.font_btn.render("< PREV", True, self.C_BTN_TEXT)
            surf.blit(lbl, (prev_rect.centerx - lbl.get_width() // 2, prev_rect.centery - lbl.get_height() // 2))

        col = self.C_BTN_HOVER if self._hover_next else self.C_BTN_NORMAL
        pygame.draw.rect(surf, col, next_rect, border_radius=4)
        label = "NEXT >" if self.page < len(self.PAGES) - 1 else "DONE"
        lbl = self.font_btn.render(label, True, self.C_BTN_TEXT)
        surf.blit(lbl, (next_rect.centerx - lbl.get_width() // 2, next_rect.centery - lbl.get_height() // 2))

    def _next_page(self):
        if self.page < len(self.PAGES) - 1: self.page += 1
        else: self.hide()

    def _prev_page(self):
        if self.page > 0: self.page -= 1

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
            pygame.draw.line(surf, (60, 180, 255, 8), (0, y), (self.pw, y))
            y += line_gap

def should_show_first_launch_tutorial() -> bool:
    import pathlib
    flag = pathlib.Path(".tutorial_shown")
    if flag.exists(): return False
    try: flag.touch()
    except OSError: pass   
    return True