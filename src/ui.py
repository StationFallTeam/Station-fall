import pygame
from src.assets import resolve_asset_path

def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def draw_health_bar(surface, current, maximum, x, y, w, h, *, border =2):
    maximum = max(1, int(maximum))
    current = _clamp(int(current), 0, maximum)
    ratio = current / maximum

    # background
    pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h))
    # fill
    fill_w = int(w * ratio)
    pygame.draw.rect(surface, (180, 50, 50), (x, y, fill_w, h))
    #border
    pygame.draw.rect(surface, (220, 220, 220), (x, y, w, h), border)

def draw_money(surface, amount, x, y) :
    #font = pygame.font.SysFont("Pixellari.ttf", 25)
    font = pygame.font.SysFont(None, 25)
    text = font.render(f"Space Bucks: {amount}", True, (255, 215, 0))
    surface.blit(text, (x,y))