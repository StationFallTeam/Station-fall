import pygame
import math

class TutorialPopup:
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
    C_DOT_ACTIVE  = (60, 200, 255)
    C_DOT_IDLE    = (40,  70, 110)
    
    # Speeds (Bumped up for snappier UI)
    ANIM_SPEED = 14          
    FADE_SPEED = 22         
    SCAN_PERIOD = 3.0       

    PAGES = [
        {
            "icon": ">>",
            "heading": "Mission Briefing",
            "lines": [
                "Pilot, you've woken up on a derelict graveyard in orbit.",
                "The station's AI has gone rogue, and the corridors",
                "are crawling with automated security and scavengers.",
                "",
                "Your objective: Survive the Combat Zones, loot 'Space Bucks',",
                "and upgrade your gear to escape this metal tomb.",
            ],
        },
        {
            "icon": "[WASD]",
            "heading": "Movement",
            "lines": [
                "W — THRUST NORTH: Move up through the debris.",
                "S — THRUST SOUTH: Back away from danger.",
                "A — THRUST WEST: strafe left to dodge fire.",
                "D — THRUST EAST: strafe right into the fray.",
                "",
                "TACTICAL NOTE: You face the last direction you moved.",
                "Positioning is life. Don't get backed into a corner!",
            ],
        },
        {
            "icon": "(*)",
            "heading": "Combat",
            "lines": [
                "MOUSE LEFT CLICK — Fire your high-energy Blaster.",
                "",
                "THE SHIELD EFFECT: When you or an enemy takes a hit,",
                "a brief 0.5s invincibility shield activates.",
                "Don't waste ammo—wait for the shield to flicker out!",
                "",
                "HEALTH DROPS: Scavenge Red Cross kits from fallen foes",
                "to instantly patch 10 HP of hull damage.",
            ],
        },
        {
            "icon": "[!]",
            "heading": "Enemies",
            "lines": [
                "STALKERS: These melee units will hunt you relentlessly.",
                "Keep moving or they will shred your suit on contact.",
                "",
                "SNIPERS: Cowardly ranged units that maintain distance.",
                "If you charge them, they will flee to keep shooting!",
                "Check the health bars above their heads to prioritize targets.",
            ],
        },
        {
            "icon": "[$]",
            "heading": "Stationzone: Gear & Inventory",
            "lines": [
                "E — SHOP: Stand near a terminal to trade Space Bucks.",
                "I — INVENTORY: Check your wallet and gear status.",
                "",
                "AVAILABLE UPGRADES:",
                "• BLASTER: Cranks up your damage per bolt.",
                "• SPACE SUIT: Reinforces your max health capacity.",
                "• HEALING KITS: Emergency 20 HP repairs.",
            ],
        },
        {
            "icon": "[OK]",
            "heading": "System Keys",
            "lines": [
                "ENTER — PORTAL: Launch your mission from the Hub portal.",
                "R — RECALL: Return home ONLY after all rooms are clear.",
                "ESC — PAUSE: Access the menu or exit the shop interface.",
                "+ / - — VOLUME: Adjust the haunting space ambiance.",
                "0 / 9 — BRIGHTNESS: Adjust your suit's visor visibility.",
                "",
                "The station won't clear itself, Pilot. Get to work.",
            ],
        },
    ]

    def __init__(self, screen_width: int, screen_height: int):
        self.sw, self.sh = screen_width, screen_height
        self.pw = min(560, screen_width - 80)
        self.ph = 400
        self.px = (screen_width  - self.pw) // 2
        self.py = (screen_height - self.ph) // 2

        self.visible   = False
        self.page      = 0
        self._alpha    = 0          
        self._slide_y  = 40        
        self._scan_t   = 0.0       

        # Load fonts (Using direct file path for speed)
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

        # Pre-create UI surfaces for instant blitting
        self.panel_surface = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA).convert_alpha()
        self.dim_overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA).convert_alpha()
        
        self._btn_prev  = pygame.Rect(0, 0, 0, 0)
        self._btn_next  = pygame.Rect(0, 0, 0, 0)
        self._hover_prev  = False
        self._hover_next  = False
        
        # Cache pre-rendered text pages
        self.page_surfaces = []
        self._pre_render_all_pages()

    def _pre_render_all_pages(self):
        """Processes text and wraps it to fit the popup width."""
        self.page_surfaces = []
        # Calculate available width (panel width minus horizontal margins)
        max_w = self.pw - 60 

        for page_data in self.PAGES:
            temp_surf = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA).convert_alpha()
            
            # Draw Heading
            h_surf = self.font_heading.render(page_data["heading"], True, self.C_HEADING)
            temp_surf.blit(h_surf, (100, 36))
            
            body_y = 120
            for line in page_data["lines"]:
                if line == "":
                    body_y += 12 # Paragraph spacing
                    continue
                
                # Split line into wrapped chunks
                wrapped_chunks = self._get_wrapped_lines(line, max_w)
                
                for i, chunk in enumerate(wrapped_chunks):
                    # Only the first chunk of a line gets special 'Key — Value' coloring
                    is_start_of_line = (i == 0)
                    line_surf = self._render_line_internal(chunk, use_special_colors=is_start_of_line)
                    
                    temp_surf.blit(line_surf, (28, body_y))
                    body_y += self.font_body.get_linesize() + 2
                    
            self.page_surfaces.append(temp_surf)

    def _get_wrapped_lines(self, text, max_width):
        """Helper to break a long string into a list of strings based on pixel width."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            w, _ = self.font_body.size(test_line)
            if w <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines

    def _render_line_internal(self, text, use_special_colors=True):
        """Renders text, optionally highlighting keys like 'W —' or 'STALKERS:'."""
        if use_special_colors:
            # Check for common separators
            for sep in [" — ", " - ", ": ", "\u2014"]:
                if sep in text:
                    parts = text.split(sep, 1)
                    k = self.font_body.render(parts[0], True, self.C_ICON_TEXT)
                    s = self.font_body.render(sep, True, self.C_MUTED)
                    d = self.font_body.render(parts[1], True, self.C_BODY)
                    
                    res = pygame.Surface((self.pw, k.get_height()), pygame.SRCALPHA).convert_alpha()
                    res.blit(k, (0, 0))
                    res.blit(s, (k.get_width(), 0))
                    res.blit(d, (k.get_width() + s.get_width(), 0))
                    return res
        
        # Default rendering for simple lines or wrapped continuations
        return self.font_body.render(text, True, self.C_BODY)

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

        # --- 1. ANIMATE ---
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + self.FADE_SPEED)
        if self._slide_y > 0:
            self._slide_y = max(0, self._slide_y - self.ANIM_SPEED)

        self._scan_t += 1 / 60

        # Update hovers every frame
        mx, my = pygame.mouse.get_pos()
        self._hover_prev = self._btn_prev.collidepoint(mx, my)
        self._hover_next = self._btn_next.collidepoint(mx, my)

        # --- 2. HANDLE INPUT ---
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_h):
                    self.hide()
                elif event.key == pygame.K_LEFT:
                    self._prev_page()
                elif event.key == pygame.K_RIGHT:
                    self._next_page()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._hover_prev: self._prev_page()
                elif self._hover_next: self._next_page()

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Dim Overlay
        self.dim_overlay.fill((5, 5, 15, int(0.7 * self._alpha))) 
        surface.blit(self.dim_overlay, (0, 0))

        # Panel
        draw_y = self.py + self._slide_y
        self.panel_surface.fill((0, 0, 0, 0)) 
        self.panel_surface.fill((*self.C_BG[:3], int(self.C_BG[3] * self._alpha / 255)))

        pygame.draw.rect(self.panel_surface, self.C_BORDER2, (0, 0, self.pw, self.ph), 2)
        pygame.draw.rect(self.panel_surface, self.C_BORDER,  (3, 3, self.pw - 6, self.ph - 6), 1)
        self._draw_corners(self.panel_surface)
        self._draw_scanlines(self.panel_surface)

        # Icon
        icon_rect = pygame.Rect(24, 28, 60, 60)
        pygame.draw.rect(self.panel_surface, self.C_ICON_BG, icon_rect, border_radius=6)
        icon_txt = self.font_icon.render(self.PAGES[self.page]["icon"], True, self.C_ICON_TEXT)
        self.panel_surface.blit(icon_txt, (icon_rect.centerx - icon_txt.get_width() // 2, 
                                           icon_rect.centery - icon_txt.get_height() // 2))

        pygame.draw.line(self.panel_surface, self.C_BORDER2, (20, 106), (self.pw - 20, 106), 1)

        # Blit Content
        self.panel_surface.blit(self.page_surfaces[self.page], (0, 0))
        self._draw_buttons(self.panel_surface)

        self.panel_surface.set_alpha(self._alpha)
        surface.blit(self.panel_surface, (self.px, draw_y))

    def _draw_buttons(self, surf):
        btn_y, btn_h, btn_w = self.ph - 36, 26, 80
        prev_rect  = pygame.Rect(20, btn_y, btn_w, btn_h)
        next_rect  = pygame.Rect(self.pw - 20 - btn_w, btn_y, btn_w, btn_h)

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