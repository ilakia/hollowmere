"""
The park as layered, slowly moving scenery (parallax) with a colour mood per zone, plus lighting.

Parallax: the picture is made of layers (sky, far rides, mid stalls, ground, foreground). A slow
"camera" drifts left and right; far layers move little, near layers move more, which looks like depth.
Lighting: a dark see-through layer covers the scene, and every light source (lamps, Walt's flashlight,
glowing ghosts) cuts a soft hole into it and adds a little coloured light.
"""
import math
import random
import time

import pygame

from .art import HEIGHT, WIDTH

GROUND_Y = 385
MARGIN = 210            # layers are wider than the screen (1380 px = 6 stalls of 230 px, so they repeat seamlessly)

ZONE_MOODS = {
    1: {"name": "Entrance & Midway", "sky": ((30, 24, 66), (96, 58, 112)), "far": (78, 58, 110),
        "mid": (44, 34, 62), "accent": (255, 200, 90), "accent2": (190, 90, 150), "ground": (56, 46, 66),
        "light": (255, 214, 150), "fog": (200, 185, 225), "sign": "TICKETS"},
    2: {"name": "The Funhouse", "sky": ((18, 34, 64), (60, 72, 120)), "far": (58, 82, 126),
        "mid": (32, 44, 72), "accent": (90, 240, 220), "accent2": (255, 100, 200), "ground": (44, 50, 70),
        "light": (170, 250, 240), "fog": (180, 220, 240), "sign": "FUN HOUSE"},
    3: {"name": "The Dark Rides", "sky": ((34, 12, 22), (98, 34, 44)), "far": (96, 38, 52),
        "mid": (50, 20, 30), "accent": (255, 80, 60), "accent2": (255, 170, 60), "ground": (58, 36, 40),
        "light": (255, 150, 110), "fog": (230, 170, 170), "sign": "GHOST TRAIN"},
    4: {"name": "The Exit Gate", "sky": ((14, 34, 34), (52, 92, 84)), "far": (48, 92, 86),
        "mid": (26, 50, 48), "accent": (130, 255, 190), "accent2": (220, 255, 230), "ground": (40, 58, 54),
        "light": (180, 255, 210), "fog": (190, 240, 215), "sign": "EXIT"},
}
LAMP_Y = 230
LAMP_SPACING = 820                                 # a lamppost every 820 px of park (foreground, moves fastest)


def gradient(size, top, bottom):
    surface = pygame.Surface(size)
    for row in range(size[1]):
        share = row / size[1]
        color = [int(top[i] * (1 - share) + bottom[i] * share) for i in range(3)]
        pygame.draw.line(surface, color, (0, row), (size[0], row))
    return surface


def draw_ferris_wheel(surface, x, y, radius, color, accent):
    pygame.draw.circle(surface, color, (x, y), radius, width=5)
    pygame.draw.circle(surface, color, (x, y), radius // 4, width=3)
    for spoke in range(12):
        angle = spoke * math.pi / 6
        end = (x + radius * math.cos(angle), y + radius * math.sin(angle))
        pygame.draw.line(surface, color, (x, y), end, 2)
        pygame.draw.rect(surface, color, (end[0] - 9, end[1] - 4, 18, 13), border_radius=3)
        pygame.draw.circle(surface, accent, (int(end[0]), int(end[1]) - 6), 2)
    pygame.draw.polygon(surface, color, [(x - 80, GROUND_Y), (x, y), (x + 80, GROUND_Y)], 5)


def draw_coaster(surface, width, color):
    """A roller-coaster track with supports across the far layer."""
    points = [(x, int(190 + 70 * math.sin(x / 90) + 30 * math.sin(x / 37))) for x in range(0, width, 6)]
    pygame.draw.lines(surface, color, False, points, 5)
    pygame.draw.lines(surface, color, False, [(x, y + 12) for x, y in points], 2)
    for x, y in points[::8]:
        pygame.draw.line(surface, color, (x, y), (x, GROUND_Y), 2)


def draw_tent(surface, x, width, height, roof, body):
    top = GROUND_Y - height
    pygame.draw.rect(surface, body, (x - width // 2, top + height // 3, width, height - height // 3))
    pygame.draw.polygon(surface, roof, [(x - width // 2 - 10, top + height // 3), (x, top), (x + width // 2 + 10, top + height // 3)])
    for i in range(-2, 3):
        pygame.draw.line(surface, body, (x, top), (x + i * width // 5, top + height // 3), 3)


def make_far_layer(zone, mood):
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    color, accent = mood["far"], mood["accent"]
    if zone == 1:
        draw_ferris_wheel(layer, 860, 205, 140, color, accent)
        draw_tent(layer, 300, 220, 150, color, color)
    elif zone == 2:
        pygame.draw.circle(layer, color, (380, 250), 120)                       # big clown-face tent
        pygame.draw.circle(layer, mood["mid"], (340, 230), 18)
        pygame.draw.circle(layer, mood["mid"], (420, 230), 18)
        pygame.draw.arc(layer, mood["mid"], (320, 250, 120, 70), math.pi, 2 * math.pi, 8)
        for i in range(6):                                                      # spiral slide tower
            pygame.draw.rect(layer, color, (820 + (i % 2) * 30, 150 + i * 38, 90, 14), border_radius=6)
        pygame.draw.rect(layer, color, (850, 130, 30, GROUND_Y - 130))
    elif zone == 3:
        draw_coaster(layer, WIDTH + 2 * MARGIN, color)
        pygame.draw.polygon(layer, color, [(620, GROUND_Y), (620, 220), (700, 160), (780, 220), (780, GROUND_Y)])
        for wx in (650, 730):                                                   # mansion windows
            pygame.draw.rect(layer, accent, (wx, 240, 20, 28))
    else:
        pygame.draw.rect(layer, color, (0, 240, WIDTH + 2 * MARGIN, GROUND_Y - 240))   # park wall
        pygame.draw.rect(layer, mood["sky"][1], (WIDTH // 2 + MARGIN - 110, 170, 220, GROUND_Y - 170))
        pygame.draw.arc(layer, color, (WIDTH // 2 + MARGIN - 150, 110, 300, 160), 0, math.pi, 22)  # gate arch
        for i in range(9):                                                      # gate bars
            bx = WIDTH // 2 + MARGIN - 100 + i * 25
            pygame.draw.line(layer, color, (bx, 190), (bx, GROUND_Y), 4)
    return layer


def make_mid_layer(zone, mood, font):
    layer = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT), pygame.SRCALPHA)
    rng = random.Random(zone)
    for x in range(40, WIDTH + 2 * MARGIN, 230):                                # stalls with striped awnings
        width = rng.randint(120, 170)
        top = GROUND_Y - rng.randint(95, 130)
        pygame.draw.rect(layer, mood["mid"], (x, top + 26, width, GROUND_Y - top - 26))
        pygame.draw.rect(layer, mood["mid"], (x - 6, top, width + 12, 18))       # awning roof
        for i in range(0, width + 1, 20):                                       # striped, scalloped edge
            color = mood["accent2"] if (i // 20) % 2 else tuple(min(255, c + 40) for c in mood["mid"])
            pygame.draw.rect(layer, color, (x + i - 6, top, 20, 18))
            pygame.draw.circle(layer, color, (x + i + 4, top + 18), 10, draw_top_left=False, draw_top_right=False,
                               draw_bottom_left=True, draw_bottom_right=True)
        opening = tuple(c // 2 for c in mood["mid"])
        pygame.draw.rect(layer, opening, (x + 18, top + 46, width - 36, 34), border_radius=4)   # counter opening
        pygame.draw.rect(layer, mood["accent"], (x + 30, top + 72, 10, 8))     # a prize on the counter
    return layer


def make_ground(mood):
    ground = pygame.Surface((WIDTH + 2 * MARGIN, HEIGHT - GROUND_Y))
    ground.fill(mood["ground"])
    line = tuple(min(255, c + 18) for c in mood["ground"])
    for row, y in enumerate(range(8, HEIGHT - GROUND_Y, 18)):
        for x in range((row % 2) * 22, WIDTH + 2 * MARGIN, 44):
            pygame.draw.ellipse(ground, line, (x, y, 38, 12), width=1)
    return ground


def tile(surface, layer, offset, y):
    """Draw a layer moved left by offset; it repeats, so the player can walk on for ever."""
    width = layer.get_width()
    x = -int(offset % width)
    surface.blit(layer, (x, y))
    surface.blit(layer, (x + width, y))


class Scenery:
    """Builds every zone's layers once and draws them with a drifting camera and lights."""

    def __init__(self):
        sign_font = pygame.font.SysFont(None, 40)
        self.layers = {}
        for zone, mood in ZONE_MOODS.items():
            sky = gradient((WIDTH, HEIGHT), *mood["sky"])
            self.layers[zone] = (sky, make_far_layer(zone, mood), make_mid_layer(zone, mood, sign_font),
                                 make_ground(mood))
        self.stars = [(random.Random(i).randrange(WIDTH), random.Random(i + 99).randrange(230)) for i in range(80)]
        self.dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.kick = 0.0                 # extra camera push (e.g. towards the ghosts on an attack)
        self.world_x = 0.0              # how far the player has walked in this zone (pixels)
        self.last_cam = 0.0
        self.stamps = {}

    def glow_stamp(self, radius, color):
        """Soft coloured light, faint at the edge and a little stronger in the centre (made once per size)."""
        key = ("glow", radius, color)
        if key not in self.stamps:
            stamp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for step in range(10):
                r = int(radius * (1 - step / 10))
                pygame.draw.circle(stamp, color + (3 + step * 3,), (radius, radius), r)
            self.stamps[key] = stamp
        return self.stamps[key]

    def light_stamp(self, radius, darkness):
        """A soft round light: strongest in the centre, fading to nothing at the edge (made once per size).
        Big circles are drawn first with little alpha, smaller ones on top with more, which gives a gradient."""
        key = (radius, darkness)
        if key not in self.stamps:
            stamp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for step in range(10):
                r = int(radius * (1 - step / 10))
                alpha = int(darkness * (step + 1) / 10)
                pygame.draw.circle(stamp, (0, 0, 0, alpha), (radius, radius), r)
            self.stamps[key] = stamp
        return self.stamps[key]

    def camera(self):
        self.kick *= 0.9                                     # the push eases back
        self.last_cam = 30 * math.sin(time.time() * 0.12) + self.kick + self.world_x
        return self.last_cam

    def lamps(self):
        """Screen positions of the foreground lampposts for the current camera (they repeat along the path)."""
        positions = []
        shift = (self.last_cam * 1.2) % LAMP_SPACING
        for base in (70, 70 + LAMP_SPACING, 70 + 2 * LAMP_SPACING):
            x = int(base - shift)
            if -40 < x < WIDTH + 40:
                positions.append((x, LAMP_Y))
        return positions

    def draw_back(self, surface, zone):
        """Everything behind the characters."""
        sky, far, mid, ground = self.layers[zone]
        mood = ZONE_MOODS[zone]
        cam = self.camera()
        surface.blit(sky, (0, 0))
        now = time.time()
        for i, (x, y) in enumerate(self.stars):
            b = 150 + int(100 * (0.5 + 0.5 * math.sin(now * (1 + i % 5) + i)))
            surface.set_at((x, y), (b, b, b))
        moon_x = 140 - int(cam * 0.05)
        pygame.draw.circle(surface, (240, 236, 210), (moon_x, 92), 36)
        pygame.draw.circle(surface, mood["sky"][0], (moon_x + 15, 83), 31)
        tile(surface, far, cam * 0.25, 0)                    # far rides move slowly ...
        tile(surface, mid, cam * 0.55, 0)                    # ... stalls a bit faster ...
        tile(surface, ground, cam * 0.8, GROUND_Y)           # ... the ground almost with the player
        for i in range(17):                                  # string of fairground bulbs (mid depth)
            x = 25 + i * 56 - int(cam * 0.55) % 56
            y = 50 + int(12 * math.sin(i * 0.9))
            if random.random() > 0.03:
                pygame.draw.circle(surface, mood["light"], (x, y), 4)

    def draw_front(self, surface, zone, lights, finale=False):
        """Lighting over the characters, then the foreground lampposts.
        lights = list of (x, y, radius, colour) for this frame (Walt's flashlight, glowing ghosts...)."""
        mood = ZONE_MOODS[zone]
        darkness = 120 if not finale else 140               # how dark the unlit parts of the scene are
        # self.dark collects "how much darkness to remove" per pixel; light stamps add up where lights overlap
        self.dark.fill((0, 0, 0, 0))
        self.glow.fill((0, 0, 0, 0))
        all_lights = [(x, y + 20, 260, mood["light"]) for x, y in self.lamps()] + list(lights)
        all_lights.append((240, GROUND_Y - 60, 230, mood["light"]))     # soft light on the player's side
        all_lights.append((720, GROUND_Y - 60, 230, mood["light"]))     # and on the ghosts' side
        for x, y, radius, color in all_lights:
            stamp = self.light_stamp(int(radius), darkness)
            self.dark.blit(stamp, (int(x) - int(radius), int(y) - int(radius)), special_flags=pygame.BLEND_RGBA_ADD)
            self.glow.blit(self.glow_stamp(int(radius * 0.7), color), (int(x - radius * 0.7), int(y - radius * 0.7)))
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 4, 12, darkness))
        shade.blit(self.dark, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)   # lights remove darkness
        surface.blit(shade, (0, 0))
        surface.blit(self.glow, (0, 0))
        for x, y in self.lamps():                                         # foreground lampposts
            pygame.draw.rect(surface, (18, 14, 22), (x - 5, y, 10, GROUND_Y - y + 20))
            pygame.draw.rect(surface, (18, 14, 22), (x - 16, y - 10, 32, 14), border_radius=4)
            pygame.draw.circle(surface, (255, 240, 200), (x, y + 6), 7)
