"""
Small drawing tools shared by all attraction scenes (window/pieces_z1.py, z2, z3), so that
everything gets the same richer look: shading, outlines, marquee bulbs, people for wax figures.
"""
import math

import pygame

GROUND_Y = 385
OUTLINE = (18, 14, 24)
WOOD = (110, 72, 44)
METAL = (120, 122, 138)
CREAM = (238, 228, 205)
GOLD = (215, 175, 80)


def shade(color, factor):
    """Darker (factor < 1) or lighter (factor > 1) version of a colour."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def box(s, color, rect, radius=0, outline=True):
    """A filled shape with a little depth: lighter top edge, darker bottom, dark outline."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(s, color, rect, border_radius=radius)
    if rect.height > 12:
        pygame.draw.rect(s, shade(color, 0.72), (rect.x, rect.bottom - max(4, rect.height // 6), rect.width,
                                                  max(4, rect.height // 6)), border_radius=radius)
        pygame.draw.line(s, shade(color, 1.25), (rect.x + 3, rect.y + 2), (rect.right - 4, rect.y + 2), 2)
    if outline:
        pygame.draw.rect(s, OUTLINE, rect, width=2, border_radius=radius)


def poly(s, color, points, outline=True):
    pygame.draw.polygon(s, color, points)
    if outline:
        pygame.draw.polygon(s, OUTLINE, points, 2)


def circle(s, color, center, radius, outline=True):
    pygame.draw.circle(s, color, (int(center[0]), int(center[1])), int(radius))
    if outline and radius > 3:
        pygame.draw.circle(s, OUTLINE, (int(center[0]), int(center[1])), int(radius), 2)


def bulbs(s, rect, t, color=(255, 220, 130), step=18):
    """Chasing light bulbs around a rectangle (marquee lights)."""
    rect = pygame.Rect(rect)
    points = []
    for x in range(rect.x, rect.right + 1, step):
        points += [(x, rect.y), (x, rect.bottom)]
    for y in range(rect.y + step, rect.bottom, step):
        points += [(rect.x, y), (rect.right, y)]
    for i, (x, y) in enumerate(points):
        on = (i + int(t * 6)) % 3 != 0
        pygame.draw.circle(s, color if on else shade(color, 0.35), (x, y), 3)


def marquee(s, text, center, font, color=(255, 220, 130), back=(60, 20, 40), t=0.0):
    """A sign board with chasing bulbs around it."""
    image = font.render(text, True, color)
    board = image.get_rect(center=center).inflate(30, 18)
    box(s, back, board, radius=6)
    bulbs(s, board.inflate(-6, -6), t, color, step=14)
    s.blit(image, image.get_rect(center=center))
    return board


def awning(s, x, y, width, colors, depth=24):
    """Striped awning with a scalloped edge."""
    stripe = 22
    for i, sx in enumerate(range(x, x + width, stripe)):
        color = colors[i % len(colors)]
        w = min(stripe, x + width - sx)
        pygame.draw.rect(s, color, (sx, y, w, depth))
        pygame.draw.circle(s, color, (sx + w // 2, y + depth), w // 2, draw_top_left=False, draw_top_right=False,
                           draw_bottom_left=True, draw_bottom_right=True)
    pygame.draw.line(s, OUTLINE, (x, y), (x + width, y), 2)


def stars_of_light(s, center, radius, t, color=(255, 240, 200)):
    """A soft twinkle (for glass highlights, magic)."""
    size = int(radius * (0.6 + 0.4 * abs(math.sin(t * 3))))
    pygame.draw.line(s, color, (center[0] - size, center[1]), (center[0] + size, center[1]), 2)
    pygame.draw.line(s, color, (center[0], center[1] - size), (center[0], center[1] + size), 2)


def person(s, x, foot_y, look, t=0.0, turn=0):
    """A wax-museum style figure (about 150 px tall). look = dict with:
    skin, hair, hair_style ('bun', 'short', 'long', 'bald', 'none'), body, legs, hat ('none', 'crown',
    'shako', 'tricorn', 'cap', 'clown'), extra ('cane', 'rifle', 'sword', 'flower', 'tutu', 'balloon'),
    eye ('normal', 'patch'). turn = small sideways head shift (a wax figure that moves...)."""
    skin = look.get("skin", (226, 214, 196))
    body = look["body"]
    legs = look.get("legs", shade(body, 0.6))
    head_y = foot_y - 140
    # legs and shoes
    if look.get("extra") == "tutu":
        poly(s, (250, 200, 220), [(x - 34, foot_y - 70), (x + 34, foot_y - 70), (x + 20, foot_y - 58), (x - 20, foot_y - 58)])
        pygame.draw.line(s, skin, (x - 8, foot_y - 58), (x - 12, foot_y - 4), 6)
        pygame.draw.line(s, skin, (x + 8, foot_y - 58), (x + 18, foot_y - 20), 6)
    else:
        box(s, legs, (x - 16, foot_y - 62, 13, 58), outline=False)
        box(s, legs, (x + 3, foot_y - 62, 13, 58), outline=False)
    box(s, (30, 24, 28), (x - 19, foot_y - 8, 17, 8), outline=False)
    box(s, (30, 24, 28), (x + 2, foot_y - 8, 17, 8), outline=False)
    # body and arms
    if look.get("dress"):
        poly(s, body, [(x - 22, foot_y - 118), (x + 22, foot_y - 118), (x + 38, foot_y - 10), (x - 38, foot_y - 10)])
    else:
        box(s, body, (x - 22, foot_y - 118, 44, 60), radius=8)
    if look.get("belt"):
        pygame.draw.rect(s, look["belt"], (x - 22, foot_y - 70, 44, 7))
    if look.get("cross_straps"):
        pygame.draw.line(s, CREAM, (x - 20, foot_y - 116), (x + 20, foot_y - 66), 5)
        pygame.draw.line(s, CREAM, (x + 20, foot_y - 116), (x - 20, foot_y - 66), 5)
    pygame.draw.line(s, body, (x - 22, foot_y - 112), (x - 36, foot_y - 70), 10)
    pygame.draw.line(s, body, (x + 22, foot_y - 112), (x + 36, foot_y - 70), 10)
    circle(s, skin, (x - 37, foot_y - 66), 6, outline=False)
    circle(s, skin, (x + 37, foot_y - 66), 6, outline=False)
    extra = look.get("extra")
    if extra == "cane":
        pygame.draw.line(s, WOOD, (x + 38, foot_y - 70), (x + 44, foot_y), 4)
        pygame.draw.arc(s, WOOD, (x + 30, foot_y - 80, 16, 16), 0, math.pi, 4)
    if extra == "rifle":
        pygame.draw.line(s, (80, 60, 40), (x + 36, foot_y - 66), (x + 36, foot_y - 170), 5)
        pygame.draw.line(s, METAL, (x + 36, foot_y - 170), (x + 36, foot_y - 186), 3)
    if extra == "sword":
        pygame.draw.line(s, METAL, (x + 38, foot_y - 70), (x + 60, foot_y - 120), 4)
        pygame.draw.line(s, GOLD, (x + 34, foot_y - 78), (x + 44, foot_y - 70), 4)
    if extra == "flower":
        circle(s, (230, 60, 90), (x + 40, foot_y - 76), 7)
    if extra == "balloon":
        pygame.draw.line(s, CREAM, (x - 37, foot_y - 66), (x - 50, foot_y - 190), 1)
        circle(s, (220, 60, 60), (x - 50, foot_y - 205), 15)
    # neck, head, face
    pygame.draw.rect(s, skin, (x - 6, foot_y - 126, 12, 10))
    hx = x + turn
    hair = look.get("hair", (90, 60, 40))
    style = look.get("hair_style", "short")
    if style == "long":
        poly(s, hair, [(hx - 20, head_y - 8), (hx + 20, head_y - 8), (hx + 24, head_y + 40), (hx - 24, head_y + 40)], outline=False)
    circle(s, skin, (hx, head_y + 4), 19)
    if look.get("clown_face"):
        circle(s, (240, 240, 245), (hx, head_y + 4), 17, outline=False)
        circle(s, (230, 40, 40), (hx, head_y + 8), 5, outline=False)
        pygame.draw.arc(s, (230, 40, 40), (hx - 11, head_y + 6, 22, 12), math.pi, 2 * math.pi, 3)
    if style == "bun":
        circle(s, hair, (hx, head_y - 18), 10)
        pygame.draw.arc(s, hair, (hx - 20, head_y - 16, 40, 30), 0, math.pi, 7)
    elif style in ("short", "long"):
        pygame.draw.arc(s, hair, (hx - 20, head_y - 16, 40, 34), 0, math.pi, 8)
    if look.get("eye") == "patch":
        circle(s, OUTLINE, (hx + 7, head_y + 2), 5, outline=False)
        pygame.draw.line(s, OUTLINE, (hx - 18, head_y - 6), (hx + 18, head_y - 2), 2)
        pygame.draw.circle(s, OUTLINE, (hx - 7, head_y + 2), 2)
    else:
        pygame.draw.circle(s, OUTLINE, (hx - 7, head_y + 2), 2)
        pygame.draw.circle(s, OUTLINE, (hx + 7, head_y + 2), 2)
    if not look.get("clown_face"):
        pygame.draw.line(s, shade(skin, 0.7), (hx - 5, head_y + 12), (hx + 5, head_y + 12), 2)
    if look.get("glasses"):
        pygame.draw.circle(s, METAL, (hx - 7, head_y + 2), 5, 1)
        pygame.draw.circle(s, METAL, (hx + 7, head_y + 2), 5, 1)
    if look.get("beard"):
        poly(s, look["beard"], [(hx - 14, head_y + 10), (hx + 14, head_y + 10), (hx, head_y + 34)], outline=False)
    hat = look.get("hat", "none")
    if hat == "crown":
        poly(s, GOLD, [(hx - 16, head_y - 12), (hx - 16, head_y - 32), (hx - 8, head_y - 22), (hx, head_y - 36),
                       (hx + 8, head_y - 22), (hx + 16, head_y - 32), (hx + 16, head_y - 12)])
        circle(s, (200, 30, 60), (hx, head_y - 22), 3, outline=False)
    elif hat == "shako":
        box(s, (30, 30, 50), (hx - 15, head_y - 46, 30, 34), radius=3)
        pygame.draw.rect(s, GOLD, (hx - 15, head_y - 18, 30, 4))
        circle(s, (230, 230, 230), (hx, head_y - 50), 5, outline=False)
    elif hat == "tricorn":
        poly(s, (30, 24, 30), [(hx - 28, head_y - 12), (hx, head_y - 34), (hx + 28, head_y - 12), (hx, head_y - 18)])
        circle(s, CREAM, (hx, head_y - 22), 4, outline=False)
    elif hat == "cap":
        poly(s, (70, 70, 90), [(hx - 20, head_y - 8), (hx + 20, head_y - 8), (hx + 30, head_y - 2), (hx - 20, head_y - 2)])
    elif hat == "clown":
        poly(s, (90, 180, 90), [(hx - 14, head_y - 12), (hx, head_y - 46), (hx + 14, head_y - 12)])
        circle(s, (240, 220, 60), (hx, head_y - 46), 5, outline=False)
