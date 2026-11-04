"""
Pixel-art sprites, the park background and small drawing helpers.

A sprite is a list of text rows; every character is one pixel and PALETTE says its colour
("." = transparent). make_sprite() turns it into an image, SCALE times bigger, so the pixels
stay crisp. Changing a character in a row changes that pixel in the game.
"""
import math
import random
import time

import pygame

WIDTH, HEIGHT = 960, 540
SCALE = 7

COLORS = {
    "sky_top": (26, 24, 62), "sky_bottom": (88, 56, 108), "ground": (52, 44, 62), "ground_line": (72, 62, 84),
    "text": (235, 230, 220), "dim_text": (160, 150, 170), "panel": (18, 16, 30),
    "hp_good": (90, 200, 110), "hp_low": (220, 90, 80), "bar_back": (60, 55, 70),
    "damage": (240, 90, 80), "heal": (110, 230, 140), "glow": (190, 120, 255), "charge": (255, 190, 60),
    "button": (55, 45, 80), "button_hover": (85, 70, 120), "potion": (200, 60, 120),
    "flashlight": (255, 230, 140), "bulb": (255, 200, 120),
    "in_band": (110, 230, 140), "too_easy": (120, 170, 240), "too_hard": (240, 90, 80),
}

PALETTE = {
    # player
    "h": (70, 45, 35), "s": (232, 200, 168), "e": (30, 25, 35), "t": (70, 190, 200), "n": (45, 140, 155),
    "j": (60, 70, 120), "d": (40, 30, 30),
    # Walt
    "c": (95, 85, 70), "g": (200, 200, 205), "w": (150, 138, 115), "v": (120, 108, 90), "k": (75, 65, 55),
    "f": (255, 225, 120), "F": (200, 170, 80),
    # wisp
    "b": (170, 220, 255), "B": (120, 170, 230),
    # animatronic bear
    "o": (150, 100, 60), "O": (230, 150, 160), "R": (255, 60, 60), "K": (40, 20, 20), "m": (120, 40, 50),
    "y": (240, 200, 60), "W": (240, 235, 220),
    # wraith
    "p": (70, 40, 95), "P": (50, 28, 70), "E": (235, 240, 255),
}

PLAYER = [
    "....hhhh....",
    "...hhhhhh...",
    "..hhssssh...",
    "...sesses...",
    "...ssssss...",
    "....ssss....",
    "..tttttttt..",
    ".tttttttttt.",
    ".ttnttttntt.",
    ".tt.tttt.tt.",
    ".ss.tttt.ss.",
    "....tttt....",
    "....jj.jj...",
    "....jj.jj...",
    "....jj.jj...",
    "...ddd.ddd..",
]

WALT = [
    "....cccccc....",
    "...cccccccc...",
    "..cccccccccc..",
    "....ssssss....",
    "....sesses....",
    "....ssssss....",
    "....gggggg....",
    ".....gggg.....",
    "...wwwwwwww...",
    "..wwwvwwvwww..",
    "..ww.wwww.ww..",
    "..ww.wwww.wwFf",
    "..ss.wwww.ssFf",
    ".....wwww.....",
    ".....kkkk.....",
    ".....kk.kk....",
    ".....kk.kk....",
    "....ddd.ddd...",
]

WISP = [
    "...bbbb...",
    "..bbbbbb..",
    ".bbbbbbbb.",
    ".bbebbebb.",
    ".bbbbbbbb.",
    ".bbbBBbbb.",
    ".bbbbbbbb.",
    ".b.bb.bb..",
    "..b..b..b.",
]

ANIMATRONIC = [
    ".oo......oo.",
    "oOOo....oOOo",
    ".oooooooooo.",
    ".oooooooooo.",
    ".ooRooooRoo.",
    ".oooooooooo.",
    ".oooKKKKooo.",
    ".ooKWKWKKoo.",
    "..oooooooo..",
    "...oooooo...",
    ".mmmmmmmmmm.",
    "mmmmmyymmmmm",
    "mmmmmmmmmmmm",
    "mm.mmmmmm.mm",
    "oo.mm..mm.oo",
    "...mm..mm...",
]

WRAITH = [
    "...pppp...",
    "..pppppp..",
    ".pppPPppp.",
    ".ppEppEpp.",
    ".pppppppp.",
    ".ppPPPPpp.",
    "..pppppp..",
    ".pppppppp.",
    "pppppppppp",
    "ppPppppPpp",
    "pppppppppp",
    "pppPppPppp",
    "pppppppppp",
    ".pppppppp.",
    ".ppPppPpp.",
    "..pppppp..",
    "..pp.ppp..",
    "...p..pp..",
    "...p...p..",
]

# ---- Study 2: the victims of the 1987 fire (drawn as people, shown pale and ghostly in the game)
PALETTE.update({
    "G": (200, 200, 205),   # grey hair
    "a": (120, 80, 140),    # cardigan
    "A": (70, 60, 90),      # skirt
    "U": (230, 210, 120),   # buttons / brass
    "L": (60, 55, 70),      # legs / trousers
    "q": (40, 40, 50),      # glasses frame / camera body
    "Q": (170, 200, 230),   # camera lens
    "r": (210, 40, 50),     # red (ribbon, neckerchief, stripes)
    "x": (240, 235, 225),   # white (stripes, collar)
    "z": (40, 70, 140),     # overalls / denim
    "D": (220, 190, 110),   # straw hat
    "V": (80, 50, 40),      # waistcoat
    "M": (60, 40, 30),      # moustache / beret
    "Z": (250, 200, 210),   # dress
})

MARTHA = [
    "....GGGG....",
    "...GGGGGG...",
    "...GssssG...",
    "...qsqqsq...",
    "...ssssss...",
    "....ssss....",
    "..aaaaaaaa..",
    ".aaaaaaaaaa.",
    ".aaUaaaaUaa.",
    ".aa.aaaa.aa.",
    ".ss.AAAA.ss.",
    "....AAAA....",
    "...AAAAAA...",
    "....LL.LL...",
    "...dd...dd..",
]

BENNY = [
    "...cccccc...",
    "..cccccccc..",
    "...ssssss...",
    "...sesses...",
    "...sMMMMs...",
    "....ssss....",
    "..xVVxxVVx..",
    ".xxVVxxVVxx.",
    ".xxVVUUVVxx.",
    ".ss.VVVV.ss.",
    "....LLLL....",
    "....LL.LL...",
    "....LL.LL...",
    "...dd...dd..",
]

ROSA = [
    "...MMMMM....",
    "..MMMMMMM...",
    "...hssssh...",
    "...hsesse...",
    "...hssssh...",
    "....ssss....",
    "..rrrrrrrr..",
    ".rrqqqqqrrr.",
    ".rrqQQqqrrr.",
    ".ssqqqqqrss.",
    "....AAAA....",
    "...AAAAAA...",
    "....LL.LL...",
    "...dd...dd..",
]

HENRY = [
    "..DDDDDDDD..",
    ".DDDDDDDDDD.",
    "...ssssss...",
    "...sesses...",
    "...sMMMMs...",
    "....ssss....",
    "..rxrxrxrx..",
    ".rxrxrxrxrx.",
    ".rxrxUUrxrx.",
    ".ss.rxrx.ssk",
    "....LLLL...k",
    "....LL.LL..k",
    "....LL.LL..k",
    "...dd...dd.k",
]

LILY = [
    "...hhhhh.rr.",
    "..hhhhhhhrr.",
    "..hssssshh..",
    "...sesses...",
    "...ssssss...",
    "....ssss....",
    "...ZZZZZZ...",
    "..ZZZZZZZZ..",
    ".sZZZZZZZZs.",
    "..ZZZZZZZZ..",
    ".ZZZZZZZZZZ.",
    "....s..s....",
    "....s..s....",
    "...dd..dd...",
]

LILY_REFLECTION = [row.replace("r", ".") for row in LILY]     # the reflection has no red ribbon

NED = [
    "...zxzxzx...",
    "..zxzxzxzx..",
    "...ssssss...",
    "...sesses...",
    "...sGGGGs...",
    "....rrrr....",
    "..zzzzzzzz..",
    ".zzzUzzUzzz.",
    ".zzzzzzzzzz.",
    ".ss.zzzz.ss.",
    "....zzzz....",
    "....zz.zz...",
    "....zz.zz...",
    "...dd...dd..",
]

VICTIM_SPRITES = {"martha": MARTHA, "benny": BENNY, "rosa": ROSA, "henry": HENRY, "lily": LILY,
                  "lily_reflection": LILY_REFLECTION, "ned": NED}

SPRITES = {"player": PLAYER, "walt": WALT, "wisp": WISP, "animatronic": ANIMATRONIC, "wraith": WRAITH,
           **VICTIM_SPRITES}
for _name, _rows in SPRITES.items():                  # catch typing mistakes in the pixel rows early
    assert len(set(len(r) for r in _rows)) == 1, f"sprite {_name}: rows have different lengths"


def make_sprite(rows, recolor=None):
    """Turn text rows into an image. recolor = function (r, g, b) -> (r, g, b), e.g. for ghost-Walt."""
    image = pygame.Surface((len(rows[0]) * SCALE, len(rows) * SCALE), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == ".":
                continue
            color = PALETTE[char]
            if recolor:
                color = recolor(color)
            pygame.draw.rect(image, color, (x * SCALE, y * SCALE, SCALE, SCALE))
    return image


def silhouette(image, color):
    """Same shape, one colour (white hit flash, coloured glow outline)."""
    flat = image.copy()
    flat.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MAX)
    flat.fill(color + (255,), special_flags=pygame.BLEND_RGB_MIN)
    return flat


def ghostly(color):
    """Colour change for Walt in the finale: pale green and see-through looking."""
    r, g, b = color
    return (min(255, r // 2 + 70), min(255, g // 2 + 140), min(255, b // 2 + 110))


def victim_ghostly(color):
    """Victims keep their colours, but washed out and pale blue, like a fading photograph."""
    r, g, b = color
    return (min(255, int(r * 0.45 + 120)), min(255, int(g * 0.45 + 135)), min(255, int(b * 0.45 + 150)))


def smoky(color):
    """The smoke of the fire (Night B finale): the wraith's shape in dark greys."""
    grey = (color[0] + color[1] + color[2]) // 3
    return (grey // 2 + 40, grey // 2 + 38, grey // 2 + 42)


def blazing(color):
    """The fire itself (Night C finale): the wraith's shape in burning orange and yellow."""
    bright = (color[0] + color[1] + color[2]) // 3
    return (255, min(255, 80 + bright // 2), min(120, bright // 4))


def load_sprites():
    """All sprite images plus their white hit-flash and light-outline versions.
    Output: dict name -> (image, flash, outline)."""
    images = {name: make_sprite(rows) for name, rows in SPRITES.items() if name not in VICTIM_SPRITES}
    for name, rows in VICTIM_SPRITES.items():
        images[name] = make_sprite(rows, victim_ghostly)
    # the real Lily's red ribbon stays bright red: it is the clue that tells her from her reflection
    images["lily"] = make_sprite(LILY, lambda col: col if col == PALETTE["r"] else victim_ghostly(col))
    images["walt_ghost"] = make_sprite(WALT, ghostly)
    images["smoke"] = make_sprite(WRAITH, smoky)
    images["blaze"] = make_sprite(WRAITH, blazing)
    sprites = {}
    for name, img in images.items():
        sprites[name] = (img, silhouette(img, (255, 255, 255)), silhouette(img, (255, 235, 190)))
    return sprites


# ---------------------------------------------------------------- background
def make_background():
    """The static part of the park at night: sky, ferris wheel, tents, gate, ground (drawn once)."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    for row in range(HEIGHT):
        share = row / HEIGHT
        color = [int(COLORS["sky_top"][i] * (1 - share) + COLORS["sky_bottom"][i] * share) for i in range(3)]
        pygame.draw.line(bg, color, (0, row), (WIDTH, row))
    pygame.draw.circle(bg, (235, 230, 200), (120, 90), 34)                      # moon
    pygame.draw.circle(bg, COLORS["sky_top"], (134, 82), 30)
    wheel = (790, 215)
    pygame.draw.circle(bg, (55, 42, 70), wheel, 135, width=4)                   # ferris wheel
    for spoke in range(12):
        angle = spoke * math.pi / 6
        end = (wheel[0] + 135 * math.cos(angle), wheel[1] + 135 * math.sin(angle))
        pygame.draw.line(bg, (55, 42, 70), wheel, end, 2)
        pygame.draw.rect(bg, (65, 50, 80), (end[0] - 8, end[1] - 4, 16, 12))
    pygame.draw.polygon(bg, (45, 35, 58), [(wheel[0] - 70, 385), (wheel[0], wheel[1]), (wheel[0] + 70, 385)], 4)
    for x, height, stripe in ((330, 120, (90, 40, 60)), (470, 90, (40, 60, 90))):  # circus tents
        pygame.draw.polygon(bg, (35, 28, 45), [(x - 80, 385), (x, 385 - height), (x + 80, 385)])
        for i in range(-3, 4, 2):
            pygame.draw.line(bg, stripe, (x, 385 - height), (x + i * 26, 385), 6)
    pygame.draw.rect(bg, COLORS["ground"], (0, 385, WIDTH, HEIGHT - 385))
    for x in (60, 900):                                                         # two old lampposts
        pygame.draw.rect(bg, (30, 26, 36), (x - 4, 230, 8, 155))
        pygame.draw.rect(bg, (30, 26, 36), (x - 14, 222, 28, 12), border_radius=4)
        pygame.draw.circle(bg, (255, 220, 150), (x, 238), 7)
    for y in range(395, HEIGHT, 18):                                            # cobblestones
        for x in range((y // 18) % 2 * 20, WIDTH, 40):
            pygame.draw.ellipse(bg, COLORS["ground_line"], (x, y, 34, 12), width=1)
    return bg


_light_layer = None


def light_pools():
    """Warm lamp light on the ground where the characters stand (drawn once, then reused)."""
    global _light_layer
    if _light_layer is None:
        _light_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x, width in ((230, 420), (730, 420)):
            for step in range(10):
                w = int(width * (1 - step / 12))
                h = int(90 * (1 - step / 12))
                pygame.draw.ellipse(_light_layer, (255, 210, 150, 9), (x - w // 2, 385 - h // 3, w, h))
            for step in range(8):                                    # soft cone of light from above
                w = int(width * 0.8 * (1 - step / 10))
                pygame.draw.ellipse(_light_layer, (255, 220, 170, 5), (x - w // 2, 120 + step * 10, w, 290))
    return _light_layer


STARS = [(random.Random(i).randrange(WIDTH), random.Random(i + 99).randrange(260)) for i in range(70)]
BULBS = [(20 + i * 52, 52 + int(14 * math.sin(i * 0.9))) for i in range(19)]


def draw_living_background(surface, background):
    """Background plus the moving parts: twinkling stars and flickering fairground bulbs."""
    surface.blit(background, (0, 0))
    surface.blit(light_pools(), (0, 0))
    now = time.time()
    for i, (x, y) in enumerate(STARS):
        brightness = 140 + int(110 * (0.5 + 0.5 * math.sin(now * (1 + i % 5) + i)))
        surface.set_at((x, y), (brightness, brightness, brightness))
    for i in range(len(BULBS) - 1):
        pygame.draw.line(surface, (60, 50, 60), BULBS[i], BULBS[i + 1], 1)
    for i, (x, y) in enumerate(BULBS):
        flicker = random.random() < 0.03                                        # now and then a bulb dies
        if not flicker:
            pygame.draw.circle(surface, COLORS["bulb"], (x, y), 4)
            glow = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(glow, COLORS["bulb"] + (50,), (12, 12), 11)
            surface.blit(glow, (x - 12, y - 12))


# ---------------------------------------------------------------- small helpers
def wrap_text(text, font, max_width):
    """Split text into lines that fit max_width pixels. Output: list of strings."""
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text(surface, text, font, color, x, y, center=False, shadow=True):
    if shadow:                                                                   # dark outline for readability
        dark = font.render(text, True, (0, 0, 0))
        rect = dark.get_rect(center=(x + 2, y + 2)) if center else dark.get_rect(topleft=(x + 2, y + 2))
        surface.blit(dark, rect)
    image = font.render(text, True, color)
    rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
    surface.blit(image, rect)


def draw_bar(surface, x, y, width, height, share):
    """HP bar: green when above 40%, red below, with a light frame."""
    share = max(0.0, min(1.0, share))
    color = COLORS["hp_good"] if share > 0.4 else COLORS["hp_low"]
    pygame.draw.rect(surface, COLORS["bar_back"], (x, y, width, height), border_radius=4)
    pygame.draw.rect(surface, color, (x, y, int(width * share), height), border_radius=4)
    pygame.draw.rect(surface, (200, 190, 210), (x, y, width, height), width=1, border_radius=4)


def draw_glow(surface, x, y, radius, color, strength=25):
    """A soft pulsing circle of light (transparent layers; strength = opacity per layer)."""
    pulse = 0.75 + 0.25 * math.sin(time.time() * 6)
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for step in range(6):
        r = int(radius * (1 - step / 7) * pulse)
        pygame.draw.circle(glow, color + (strength,), (radius, radius), r)
    surface.blit(glow, (x - radius, y - radius))


def draw_bubble(surface, font, text, x, y):
    """Speech bubble with its tail pointing down to (x, y)."""
    lines = wrap_text(text, font, 250)
    height = 12 + 22 * len(lines)
    box = pygame.Rect(x - 40, y - height - 16, 270, height)
    box.x = max(8, min(box.x, WIDTH - box.width - 8))                  # always fully on screen
    pygame.draw.rect(surface, COLORS["text"], box, border_radius=10)
    pygame.draw.polygon(surface, COLORS["text"], [(x - 10, box.bottom), (x + 10, box.bottom), (x, y)])
    for i, line in enumerate(lines):
        draw_text(surface, line, font, COLORS["panel"], box.x + 10, box.y + 6 + 22 * i, shadow=False)


class Button:
    """A clickable rectangle with a label and the keyboard keys that also press it."""

    def __init__(self, name, label, rect, keys, flashing=False):
        self.name = name
        self.label = label
        self.rect = pygame.Rect(rect)
        self.keys = keys
        self.flashing = flashing      # True: the border blinks (Walt's DEFEND warning)

    def draw(self, surface, font):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = COLORS["button_hover"] if hover else COLORS["button"]
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if self.flashing and math.sin(time.time() * 10) > 0:
            pygame.draw.rect(surface, COLORS["charge"], self.rect, width=4, border_radius=8)
        else:
            pygame.draw.rect(surface, COLORS["glow"], self.rect, width=2, border_radius=8)
        draw_text(surface, self.label, font, COLORS["text"], self.rect.centerx, self.rect.centery, center=True)
