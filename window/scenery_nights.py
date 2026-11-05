"""
Backgrounds for the story nights B and C (window/scenery.py builds the classic park's four zones).

  zone 5, "The Lakeside" (Night B): the half of the park that was closed after the fire. A lake in the
          moonlight with the shore and an old boathouse far away, willows and a promenade railing nearer.
  zone 6, "June 1987" (Night C): the park as it was on the night of the fire: new, colourful shop fronts,
          but an orange sky, smoke columns and a burning ferris wheel behind them.

Same layer system as the classic park: far layer (moves slowly), mid layer, ground.
"""
import math
import random

import pygame

from .art import HEIGHT, WIDTH

GROUND_Y = 385
MARGIN = 210

NIGHT_MOODS = {
    5: {"name": "The Lakeside", "sky": ((10, 22, 40), (44, 70, 92)), "far": (30, 52, 66),
        "mid": (24, 38, 44), "accent": (200, 230, 255), "accent2": (120, 170, 160), "ground": (52, 50, 46),
        "light": (200, 225, 255), "fog": (190, 215, 230), "sign": "LAKESIDE"},
    6: {"name": "June 1987", "sky": ((40, 12, 10), (150, 60, 24)), "far": (54, 22, 18),
        "mid": (70, 40, 40), "accent": (255, 190, 60), "accent2": (40, 150, 200), "ground": (70, 52, 44),
        "light": (255, 180, 110), "fog": (120, 90, 80), "sign": "SUMMER '87"},
}


def lake_far_layer(mood):
    """The far shore, a boathouse, a dark coaster and the lake with the moon's reflection."""
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    width = layer.get_width()
    color = mood["far"]
    rng = random.Random(5)
    for x in range(0, width, 18):                                          # tree line on the far shore
        height = 30 + rng.randint(0, 40) + int(12 * math.sin(x / 70))
        pygame.draw.ellipse(layer, color, (x - 16, 300 - height, 44, height + 20))
    pygame.draw.rect(layer, color, (0, 290, width, 16))
    for i in range(0, width, 7):                                           # a wooden coaster on the far shore
        y = int(205 + 45 * math.sin(i / 60) + 18 * math.sin(i / 23))
        if 620 < i < 1150:
            pygame.draw.circle(layer, color, (i, y), 3)
            if i % 28 == 0:
                pygame.draw.line(layer, color, (i, y), (i, 300), 2)
    boathouse = pygame.Rect(230, 238, 150, 62)                             # the old boathouse
    pygame.draw.rect(layer, color, boathouse)
    pygame.draw.polygon(layer, color, [(boathouse.x - 14, boathouse.y), (boathouse.centerx, boathouse.y - 40),
                                       (boathouse.right + 14, boathouse.y)])
    pygame.draw.rect(layer, (240, 220, 150), (boathouse.x + 24, boathouse.y + 18, 12, 14))   # one lit window
    water = pygame.Rect(0, 306, width, GROUND_Y - 306)                      # the lake
    for row in range(water.height):
        share = row / water.height
        tone = (int(16 + 20 * share), int(30 + 26 * share), int(46 + 28 * share))
        pygame.draw.line(layer, tone, (0, water.y + row), (width, water.y + row))
    for i in range(14):                                                    # moonlight on the water
        y = water.y + 6 + i * 5
        half = 60 - i * 3
        pygame.draw.line(layer, (150, 170, 190), (WIDTH // 2 + MARGIN - half, y), (WIDTH // 2 + MARGIN + half, y), 2)
    return layer


def lake_mid_layer(mood):
    """Willows, lanterns on posts and the promenade railing along the water."""
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    width = layer.get_width()
    dark = mood["mid"]
    for x in range(120, width, 460):                                       # weeping willows
        pygame.draw.polygon(layer, (34, 30, 30), [(x - 10, GROUND_Y), (x - 5, GROUND_Y - 170),
                                                  (x + 5, GROUND_Y - 170), (x + 12, GROUND_Y)])   # trunk
        pygame.draw.ellipse(layer, (30, 52, 46), (x - 90, GROUND_Y - 250, 180, 110))              # crown
        for strand in range(-84, 85, 7):                                   # long hanging branches
            top = GROUND_Y - 200 + int(abs(strand) * 0.35)
            length = 150 - int(abs(strand) * 0.8)
            for k in range(0, length, 6):                                  # each strand is a row of leaves
                lx = x + strand + int(4 * math.sin(k / 18 + strand))
                pygame.draw.circle(layer, (40 + (strand % 3) * 6, 70, 60), (lx, top + k), 2)
    rail_y = GROUND_Y - 34                                                 # railing along the promenade
    pygame.draw.line(layer, (70, 68, 64), (0, rail_y), (width, rail_y), 4)
    pygame.draw.line(layer, (70, 68, 64), (0, rail_y + 16), (width, rail_y + 16), 2)
    for x in range(0, width, 40):
        pygame.draw.line(layer, (70, 68, 64), (x, rail_y), (x, GROUND_Y), 3)
    for x in range(330, width, 460):                                       # a string of paper lanterns, high up
        pygame.draw.line(layer, (50, 46, 44), (x, GROUND_Y - 230), (x, GROUND_Y), 3)
        pygame.draw.arc(layer, (50, 46, 44), (x, GROUND_Y - 250, 230, 50), math.pi, 2 * math.pi, 2)
        for i, color in enumerate(((230, 120, 90), (240, 210, 120), (150, 200, 220), (230, 120, 90))):
            lx = x + 30 + i * 52
            pygame.draw.ellipse(layer, color, (lx - 8, GROUND_Y - 222 + abs(i - 1.5) * -6 + 6, 16, 20))
    return layer


def lake_ground(mood):
    """Wooden boardwalk planks."""
    ground = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT - GROUND_Y))
    ground.fill(mood["ground"])
    for y in range(0, HEIGHT - GROUND_Y, 16):
        pygame.draw.line(ground, (38, 36, 34), (0, y), (ground.get_width(), y), 2)
        for x in range((y // 16 % 2) * 60, ground.get_width(), 120):
            pygame.draw.line(ground, (38, 36, 34), (x, y), (x, y + 16), 2)
    return ground


def burning_wheel(layer, x, y, radius, color):
    """A ferris wheel silhouette with flames along its rim."""
    pygame.draw.circle(layer, color, (x, y), radius, width=6)
    for spoke in range(12):
        angle = spoke * math.pi / 6
        end = (x + radius * math.cos(angle), y + radius * math.sin(angle))
        pygame.draw.line(layer, color, (x, y), end, 2)
        pygame.draw.rect(layer, color, (end[0] - 9, end[1] - 4, 18, 13), border_radius=3)
    pygame.draw.polygon(layer, color, [(x - 80, GROUND_Y), (x, y), (x + 80, GROUND_Y)], 5)
    for spoke in range(0, 12, 2):                                          # flames on the upper half
        angle = math.pi + spoke * math.pi / 12
        fx, fy = x + radius * math.cos(angle), y + radius * math.sin(angle)
        pygame.draw.polygon(layer, (255, 140, 40), [(fx - 10, fy), (fx + 10, fy), (fx, fy - 28)])
        pygame.draw.polygon(layer, (255, 220, 90), [(fx - 5, fy), (fx + 5, fy), (fx, fy - 14)])


def fire_far_layer(mood):
    """Smoke columns, a burning ferris wheel and burning roofs against the orange sky."""
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    color = mood["far"]
    for x, w in ((260, 140), (900, 180), (1250, 120)):                     # smoke columns
        for i in range(8):
            r = w // 2 + i * 10
            pygame.draw.circle(layer, (60, 40, 38, 150), (x + int(30 * math.sin(i)), 300 - i * 40), r)
    burning_wheel(layer, 880, 205, 135, color)
    rng = random.Random(6)
    for x in range(0, layer.get_width(), 150):                             # roofs of the far buildings, some on fire
        height = rng.randint(60, 110)
        pygame.draw.rect(layer, color, (x, GROUND_Y - 60 - height, 120, height + 60))
        pygame.draw.polygon(layer, color, [(x - 8, GROUND_Y - 60 - height), (x + 60, GROUND_Y - 100 - height),
                                           (x + 128, GROUND_Y - 60 - height)])
        if rng.random() < 0.5:
            top = GROUND_Y - 100 - height
            for f in range(5):
                fx = x + 20 + f * 20
                pygame.draw.polygon(layer, (255, 120, 30), [(fx - 12, top + 40), (fx + 12, top + 40), (fx, top - 10 - (f % 2) * 14)])
                pygame.draw.polygon(layer, (255, 210, 80), [(fx - 6, top + 40), (fx + 6, top + 40), (fx, top + 12)])
    return layer


def fire_mid_layer(mood):
    """The 1987 shop fronts: fresh paint, striped awnings, '87 banners."""
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    rng = random.Random(87)
    fronts = [(220, 70, 70), (60, 150, 200), (240, 190, 60), (90, 180, 110), (200, 90, 170)]
    font = pygame.font.SysFont(None, 26)
    for i, x in enumerate(range(30, layer.get_width(), 230)):
        width = rng.randint(150, 190)
        top = GROUND_Y - rng.randint(120, 150)
        color = fronts[i % len(fronts)]
        dim = tuple(int(c * 0.55) for c in color)                          # it is night: colours are muted
        pygame.draw.rect(layer, dim, (x, top, width, GROUND_Y - top))
        for s in range(0, width, 20):                                      # striped awning
            stripe = (230, 220, 200) if (s // 20) % 2 else tuple(int(c * 0.7) for c in color)
            pygame.draw.rect(layer, stripe, (x + s, top + 30, 20, 18))
        pygame.draw.rect(layer, (40, 30, 34), (x + 20, top + 60, width - 40, 50), border_radius=3)   # shop window
        pygame.draw.rect(layer, (255, 200, 120), (x + 26, top + 66, width - 52, 38), 2, border_radius=3)
        name = ("SODA", "CANDY", "TOYS", "PIZZA", "ARCADE")[i % 5]
        image = font.render(name, True, (250, 240, 220))
        layer.blit(image, image.get_rect(center=(x + width // 2, top + 15)))
    return layer


def fire_ground(mood):
    """Fresh paving stones, with ash."""
    ground = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT - GROUND_Y))
    ground.fill(mood["ground"])
    rng = random.Random(1987)
    for y in range(6, HEIGHT - GROUND_Y, 20):
        for x in range((y // 20 % 2) * 30, ground.get_width(), 60):
            pygame.draw.rect(ground, (86, 66, 56), (x, y, 54, 14), 1, border_radius=3)
    for _ in range(300):
        pygame.draw.circle(ground, (110, 104, 100), (rng.randrange(ground.get_width()), rng.randrange(ground.get_height())), 1)
    return ground


def night_layers(zone):
    """Output: (far layer, mid layer, ground) for zone 5 or 6."""
    mood = NIGHT_MOODS[zone]
    if zone == 5:
        return lake_far_layer(mood), lake_mid_layer(mood), lake_ground(mood)
    return fire_far_layer(mood), fire_mid_layer(mood), fire_ground(mood)
