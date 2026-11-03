"""
The park map shown before each room: the 3 zones side by side, every attraction as a dot,
the player's path so far as a line, and the next attraction glowing.
"""
import pygame

from .art import COLORS, draw_glow, draw_text

ZONE_COLORS = {1: (90, 60, 110), 2: (70, 80, 120), 3: (100, 55, 70), 4: (60, 110, 90)}
ZONE_SHORT = {1: "Entrance", 2: "Funhouse", 3: "Dark Rides", 4: "Exit"}


def map_positions(beats, rect):
    """Where each attraction sits on the map. Output: dict beat_id -> (x, y).
    Zones are columns from left to right; the finale is on the far right."""
    positions = {}
    zone_width = rect.width / 3.6
    for zone in (1, 2, 3):
        zone_beats = [b for b in beats if b["zone"] == zone]
        for i, beat in enumerate(zone_beats):
            x = rect.x + zone_width * (zone - 1) + zone_width / 2 + (18 if i % 2 else -18)
            y = rect.y + 40 + i * (rect.height - 60) / max(1, len(zone_beats) - 1)
            positions[beat["id"]] = (int(x), int(y))
    for beat in beats:
        if beat["zone"] == 4:
            positions[beat["id"]] = (rect.right - 28, rect.centery + 10)
    return positions


def draw_park_map(surface, rect, beats, visited, next_id, font):
    """Inputs: rect = where to draw, beats = all attractions, visited = ids already played (in order),
    next_id = the attraction about to be played, font for labels."""
    pygame.draw.rect(surface, (14, 12, 24), rect, border_radius=10)
    zone_width = rect.width / 3.6
    for zone in (1, 2, 3):
        area = pygame.Rect(int(rect.x + zone_width * (zone - 1)) + 4, rect.y + 24, int(zone_width) - 8, rect.height - 30)
        pygame.draw.rect(surface, ZONE_COLORS[zone], area, width=2, border_radius=8)
        draw_text(surface, ZONE_SHORT[zone], font, COLORS["dim_text"], area.centerx, rect.y + 12, center=True)
    draw_text(surface, ZONE_SHORT[4], font, COLORS["dim_text"], rect.right - 28, rect.y + 12, center=True)

    positions = map_positions(beats, rect)
    path = [positions[b] for b in visited if b in positions]
    if next_id in positions:
        path = path + [positions[next_id]]
    if len(path) > 1:
        pygame.draw.lines(surface, COLORS["flashlight"], False, path, 3)          # the way walked so far
    for beat in beats:
        x, y = positions[beat["id"]]
        if beat["id"] == next_id:
            draw_glow(surface, x, y, 22, COLORS["charge"], strength=50)
            pygame.draw.circle(surface, COLORS["charge"], (x, y), 8)
        elif beat["id"] in visited:
            pygame.draw.circle(surface, COLORS["flashlight"], (x, y), 6)
        else:
            pygame.draw.circle(surface, ZONE_COLORS.get(beat["zone"], (90, 90, 90)), (x, y), 6, width=2)
        if beat["zone"] == 4:
            pygame.draw.rect(surface, (120, 200, 160), (x - 10, y - 30, 20, 18), width=2)   # the exit gate
