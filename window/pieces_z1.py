"""Attraction scenes of zone 1, the Entrance & Midway. Each function draws one attraction
around screen position cx; ctx["t"] (seconds) drives the animations."""
import math

import pygame

from .pieces_kit import (CREAM, GOLD, GROUND_Y, METAL, OUTLINE, WOOD, awning, box, bulbs, circle, marquee, poly,
                         shade, stars_of_light)


def ticket_booth(s, cx, ctx, font):
    """Old ticket booth with a skeleton ticket-seller behind the glass, queue ropes and turnstiles."""
    t = ctx["t"]
    poly(s, (150, 40, 55), [(cx - 95, GROUND_Y - 215), (cx, GROUND_Y - 275), (cx + 95, GROUND_Y - 215)])   # roof
    pygame.draw.circle(s, GOLD, (cx, GROUND_Y - 280), 8)
    box(s, (120, 30, 45), (cx - 80, GROUND_Y - 215, 160, 215))
    for x in range(cx - 80, cx + 80, 20):                                                 # panel stripes
        pygame.draw.line(s, (100, 25, 38), (x, GROUND_Y - 100), (x, GROUND_Y - 4), 3)
    glass = pygame.Rect(cx - 55, GROUND_Y - 185, 110, 80)
    box(s, (40, 60, 80), glass, radius=8)
    # the skeleton ticket-seller
    circle(s, (225, 220, 205), (cx, GROUND_Y - 150), 15)
    pygame.draw.circle(s, OUTLINE, (cx - 6, GROUND_Y - 152), 4)
    pygame.draw.circle(s, OUTLINE, (cx + 6, GROUND_Y - 152), 4)
    for i in range(4):
        pygame.draw.line(s, OUTLINE, (cx - 6 + i * 4, GROUND_Y - 142), (cx - 6 + i * 4, GROUND_Y - 137), 1)
    for rib in range(3):
        pygame.draw.line(s, (225, 220, 205), (cx - 14, GROUND_Y - 128 + rib * 7), (cx + 14, GROUND_Y - 128 + rib * 7), 2)
    wave = int(8 * math.sin(t * 3))                                                       # it waves at you...
    pygame.draw.line(s, (225, 220, 205), (cx + 14, GROUND_Y - 128), (cx + 30, GROUND_Y - 150 + wave), 3)
    pygame.draw.line(s, shade((40, 60, 80), 1.6), (glass.x + 8, glass.y + 8), (glass.x + 30, glass.y + 8), 3)  # shine
    box(s, WOOD, (cx - 70, GROUND_Y - 105, 140, 14))                                      # counter
    for i in range(6):                                                                    # ticket roll
        pygame.draw.rect(s, (245, 205, 90), (cx + 72 + i * 2, GROUND_Y - 100 + i * 12, 24, 9))
        pygame.draw.rect(s, OUTLINE, (cx + 72 + i * 2, GROUND_Y - 100 + i * 12, 24, 9), 1)
    marquee(s, "TICKETS", (cx, GROUND_Y - 238), font, t=t)
    for x in (cx - 220, cx - 150, cx + 150, cx + 220):                                    # queue posts and ropes
        box(s, GOLD, (x - 4, GROUND_Y - 50, 8, 50), outline=False)
        circle(s, GOLD, (x, GROUND_Y - 52), 6)
    for a, b in ((cx - 220, cx - 150), (cx + 150, cx + 220)):
        pygame.draw.arc(s, (170, 30, 40), (a, GROUND_Y - 52, b - a, 22), math.pi, 2 * math.pi, 4)
    for side in (-1, 1):                                                                  # turnstiles
        x = cx + side * 120
        box(s, METAL, (x - 5, GROUND_Y - 62, 10, 62), outline=False)
        for arm in range(3):
            a = t * 2 * side + arm * 2.09
            pygame.draw.line(s, METAL, (x, GROUND_Y - 52), (x + 26 * math.cos(a), GROUND_Y - 52 + 9 * math.sin(a)), 4)


def carousel(s, cx, ctx, font):
    """A carousel that really turns: horses circle in depth (front ones bigger and lower)."""
    t = ctx["t"]
    top = GROUND_Y - 260
    box(s, (90, 50, 60), (cx - 210, GROUND_Y - 22, 420, 22), radius=6)                    # platform
    box(s, GOLD, (cx - 14, top + 50, 28, GROUND_Y - top - 70))                            # centre column
    for i in range(4):                                                                    # mirrors on the column
        pygame.draw.rect(s, (170, 200, 220), (cx - 9, top + 70 + i * 40, 18, 28))
    horses = []
    for i in range(8):
        a = t * 0.7 + i * math.pi / 4
        depth = math.sin(a)                                                               # -1 back ... +1 front
        horses.append((depth, cx + 180 * math.cos(a), i))
    for depth, x, i in sorted(horses):                                                    # back ones first
        scale = 0.75 + 0.25 * (depth + 1) / 2
        bob = int(16 * math.sin(t * 2.2 + i))
        y = GROUND_Y - 110 + int(20 * (depth + 1) / 2) + bob
        pygame.draw.line(s, GOLD, (x, top + 60), (x, GROUND_Y - 22), max(2, int(4 * scale)))
        colour = ((240, 235, 220), (40, 30, 30), (200, 170, 120), (230, 230, 240))[i % 4]
        colour = shade(colour, 0.6 + 0.4 * (depth + 1) / 2)                              # back horses darker
        w, h = int(60 * scale), int(26 * scale)
        body = pygame.Rect(int(x - w / 2), y, w, h)
        pygame.draw.ellipse(s, colour, body)
        pygame.draw.ellipse(s, OUTLINE, body, 2)
        head = [(x + w * 0.35, y + 4), (x + w * 0.55, y - h * 0.9), (x + w * 0.72, y - h * 0.6), (x + w * 0.5, y + h * 0.5)]
        poly(s, colour, head)
        for leg in (-0.3, 0.25):
            pygame.draw.line(s, colour, (x + w * leg, body.bottom - 3), (x + w * leg + 6, body.bottom + 20 * scale), max(3, int(5 * scale)))
        pygame.draw.rect(s, ((190, 50, 80), (60, 120, 200), (240, 190, 60), (90, 170, 100))[i % 4],
                         (int(x - 10 * scale), y - 3, int(20 * scale), int(7 * scale)))  # saddle
    # canopy on top
    poly(s, (200, 55, 85), [(cx - 230, top + 50), (cx, top - 10), (cx + 230, top + 50)])
    pygame.draw.line(s, GOLD, (cx, top - 10), (cx, top - 40), 3)
    pygame.draw.polygon(s, (240, 210, 80), [(cx, top - 40), (cx + 24, top - 32), (cx, top - 24)])  # flag
    awning(s, cx - 230, top + 48, 460, [(200, 55, 85), (245, 230, 190)], depth=20)
    bulbs(s, (cx - 230, top + 46, 460, 2), t, step=20)


def cotton_candy(s, cx, ctx, font):
    """Cotton-candy stall: spinning machine with a pink cloud, cones on display, a creepy mascot."""
    t = ctx["t"]
    box(s, (240, 150, 190), (cx - 120, GROUND_Y - 130, 240, 130))
    for x in range(cx - 120, cx + 120, 24):
        pygame.draw.line(s, (255, 200, 225), (x, GROUND_Y - 128), (x, GROUND_Y - 4), 4)
    awning(s, cx - 135, GROUND_Y - 170, 270, [(255, 120, 180), (255, 255, 255)])
    box(s, CREAM, (cx - 120, GROUND_Y - 132, 240, 14))
    bowl = pygame.Rect(cx - 50, GROUND_Y - 175, 100, 40)                                 # the machine
    box(s, METAL, (cx - 30, GROUND_Y - 140, 60, 10))
    pygame.draw.ellipse(s, (210, 215, 230), bowl)
    pygame.draw.ellipse(s, OUTLINE, bowl, 2)
    for i in range(10):                                                                   # pink fluff spinning
        a = t * 5 + i * 0.63
        circle(s, (255, 170, 210), (cx + 34 * math.cos(a), GROUND_Y - 160 + 6 * math.sin(a)), 9, outline=False)
    for i in range(6):                                                                    # cones on display
        x = cx - 100 + i * 40
        poly(s, CREAM, [(x - 5, GROUND_Y - 132), (x + 5, GROUND_Y - 132), (x, GROUND_Y - 100)])
        for dx, dy in ((0, -150), (-9, -142), (9, -142), (0, -138)):
            circle(s, (255, 170, 210) if i % 2 else (170, 210, 255), (x + dx, GROUND_Y + dy), 10, outline=False)
    marquee(s, "COTTON CANDY", (cx, GROUND_Y - 205), font, color=(255, 190, 220), back=(120, 30, 70), t=t)
    mx = cx + 170                                                                         # mascot on a pole
    box(s, METAL, (mx - 4, GROUND_Y - 120, 8, 120), outline=False)
    tilt = int(6 * math.sin(t * 0.8))
    circle(s, (245, 235, 225), (mx + tilt, GROUND_Y - 150), 30)
    circle(s, (255, 170, 200), (mx - 22 + tilt, GROUND_Y - 175), 10)
    circle(s, (255, 170, 200), (mx + 22 + tilt, GROUND_Y - 175), 10)
    circle(s, OUTLINE, (mx - 10 + tilt, GROUND_Y - 156), 5, outline=False)
    circle(s, OUTLINE, (mx + 10 + tilt, GROUND_Y - 156), 5, outline=False)
    pygame.draw.arc(s, (200, 30, 50), (mx - 16 + tilt, GROUND_Y - 152, 32, 22), math.pi, 2 * math.pi, 4)


def photo_booth(s, cx, ctx, font):
    """Vintage photo booth with a flash, and a corkboard of old photo strips from happy visitors."""
    t = ctx["t"]
    box(s, (55, 45, 85), (cx - 80, GROUND_Y - 235, 160, 235), radius=8)
    marquee(s, "PHOTOS 4 FOR 10c", (cx, GROUND_Y - 250), font, color=(255, 230, 150), back=(40, 30, 60), t=t)
    curtain = pygame.Rect(cx - 58, GROUND_Y - 190, 116, 190)
    pygame.draw.rect(s, (160, 30, 45), curtain)
    for i in range(6):
        pygame.draw.line(s, (120, 20, 32), (curtain.x + 10 + i * 19, curtain.y), (curtain.x + 10 + i * 19, curtain.bottom), 3)
    pygame.draw.rect(s, GOLD, (curtain.x - 4, curtain.y - 6, curtain.width + 8, 8))
    if (t % 3.2) < 0.12:                                                                  # the flash goes off
        pygame.draw.rect(s, (255, 255, 235), curtain)
    box(s, (60, 60, 70), (cx + 60, GROUND_Y - 120, 18, 30))                               # coin slot
    pygame.draw.rect(s, OUTLINE, (cx + 66, GROUND_Y - 112, 6, 14))
    board = pygame.Rect(cx + 110, GROUND_Y - 220, 170, 150)                               # corkboard
    box(s, (170, 120, 70), board, radius=4)
    for i in range(5):
        x = board.x + 12 + i * 32
        y = board.y + 10 + (i % 2) * 14
        pygame.draw.rect(s, CREAM, (x, y, 24, 92))
        for f in range(4):
            pygame.draw.rect(s, (80, 70, 70), (x + 3, y + 4 + f * 22, 18, 18))
            circle(s, (205, 190, 170), (x + 12, y + 12 + f * 22), 4, outline=False)
        pygame.draw.circle(s, (220, 40, 40), (x + 12, y + 2), 3)                         # pin
    family_photo = pygame.Rect(board.x + 40, board.bottom - 40, 60, 34)                   # a family snapshot
    pygame.draw.rect(s, CREAM, family_photo)
    for i, size in enumerate((6, 6, 4, 4)):                                              # two adults, two kids
        circle(s, (205, 190, 170), (family_photo.x + 10 + i * 13, family_photo.y + 12 + (6 - size)), size, outline=False)
    small = pygame.font.SysFont(None, 14).render("SMILE!", True, OUTLINE)
    s.blit(small, (family_photo.x + 14, family_photo.bottom - 10))
    for i in range(3):                                                                    # strips on the left too
        x = cx - 150 - i * 34
        pygame.draw.line(s, METAL, (x - 16, GROUND_Y - 214), (x + 18, GROUND_Y - 214), 1)
        pygame.draw.rect(s, CREAM, (x - 12, GROUND_Y - 210, 24, 90))
        for f in range(4):
            pygame.draw.rect(s, (80, 70, 70), (x - 9, GROUND_Y - 206 + f * 21, 18, 17))


def ring_toss(s, cx, ctx, font):
    """A real ring-toss stall: striped awning, prize wall of stuffed toys, rows of glass bottles,
    rings on pegs and flying, light bulbs around the frame and a price sign."""
    t = ctx["t"]
    stall = pygame.Rect(cx - 230, GROUND_Y - 260, 460, 260)
    box(s, (70, 40, 50), stall)                                                           # back wall
    for row in range(2):                                                                  # prize wall of toys
        for i in range(9):
            x = stall.x + 30 + i * 50
            y = stall.y + 48 + row * 42
            colour = ((230, 120, 160), (120, 180, 230), (240, 200, 80), (150, 210, 120), (200, 140, 90))[(i + row) % 5]
            circle(s, colour, (x, y + 10), 14)
            circle(s, colour, (x - 10, y - 4), 6)
            circle(s, colour, (x + 10, y - 4), 6)
            pygame.draw.circle(s, OUTLINE, (x - 5, y + 7), 2)
            pygame.draw.circle(s, OUTLINE, (x + 5, y + 7), 2)
            if (i + row) % 4 == 0:                                                        # some bears have teeth
                pygame.draw.rect(s, (250, 250, 240), (x - 5, y + 14, 10, 4))
    box(s, WOOD, (stall.x, GROUND_Y - 80, stall.width, 80))                               # counter
    for x in range(stall.x, stall.right, 40):
        pygame.draw.line(s, shade(WOOD, 0.75), (x, GROUND_Y - 78), (x, GROUND_Y), 2)
    box(s, (200, 60, 60), (stall.x - 10, GROUND_Y - 88, stall.width + 20, 12), outline=False)
    for row in range(3):                                                                  # bottle rows: back rows higher
        for i in range(9 - row):
            x = cx - 170 + i * 42 + row * 21
            base = GROUND_Y - 88 - row * 22                                               # each row on a step
            bottle = ((60, 150, 100), (90, 120, 200), (200, 140, 60))[row]
            if i == 0:
                box(s, shade(WOOD, 1.1), (cx - 190 + row * 21, base, 380 - row * 42, 8), outline=False)
            box(s, bottle, (x - 8, base - 28, 16, 28), radius=5, outline=False)
            pygame.draw.rect(s, bottle, (x - 3, base - 40, 6, 13))
            pygame.draw.line(s, shade(bottle, 1.7), (x - 4, base - 24), (x - 4, base - 8), 2)   # glass shine
    for i in range(3):                                                                    # rings flying in an arc
        phase = (t * 0.6 + i / 3) % 1.0
        x = stall.x - 60 + phase * 300
        y = GROUND_Y - 200 + 160 * (phase - 0.5) ** 2 * 2 - 60
        pygame.draw.ellipse(s, (255, 210, 80), (x, y, 28, 12), 4)
    for i in range(5):                                                                    # rings on a peg
        pygame.draw.ellipse(s, (255, 210, 80) if i % 2 else (240, 90, 90), (stall.right - 70, GROUND_Y - 60 + i * 6, 30, 10), 4)
    awning(s, stall.x - 20, stall.y - 6, stall.width + 40, [(220, 50, 60), (250, 240, 220)], depth=30)
    bulbs(s, (stall.x - 14, stall.y + 30, stall.width + 28, stall.height - 130), t, step=22)
    marquee(s, "RING TOSS  ·  3 RINGS 25c", (cx, stall.y - 28), font, t=t)


def ferris_base(s, cx, ctx, font):
    """The Big Wheel: double rim with cross-bracing, real cabins, chasing lights, a ticket hut."""
    t = ctx["t"]
    hub = (cx, GROUND_Y - 190)
    radius = 132
    for side in (-1, 1):                                                                  # steel A-frame
        pygame.draw.line(s, (90, 92, 108), hub, (cx + side * 120, GROUND_Y), 10)
        pygame.draw.line(s, (90, 92, 108), (cx + side * 40, GROUND_Y - 120), (cx + side * 95, GROUND_Y - 30), 4)
    pygame.draw.line(s, (90, 92, 108), (cx - 80, GROUND_Y - 60), (cx + 80, GROUND_Y - 60), 6)
    turn = t * 0.22
    for r, width in ((radius, 6), (radius - 22, 3)):
        pygame.draw.circle(s, (180, 60, 95), hub, r, width)
    for spoke in range(18):
        a = turn + spoke * math.pi / 9
        outer = (hub[0] + radius * math.cos(a), hub[1] + radius * math.sin(a))
        inner = (hub[0] + (radius - 22) * math.cos(a + 0.17), hub[1] + (radius - 22) * math.sin(a + 0.17))
        pygame.draw.line(s, (160, 162, 178), hub, outer, 2)
        pygame.draw.line(s, (160, 162, 178), outer, inner, 2)                               # cross-bracing
        on = (spoke + int(t * 5)) % 3 == 0
        pygame.draw.circle(s, (255, 230, 140) if on else (110, 80, 60), (int(outer[0]), int(outer[1])), 4)
    for car in range(9):                                                                  # cabins hang straight down
        a = turn + car * 2 * math.pi / 9
        x = hub[0] + radius * math.cos(a)
        y = hub[1] + radius * math.sin(a)
        swing = 4 * math.sin(t * 2 + car)
        pygame.draw.line(s, METAL, (x, y), (x + swing, y + 14), 2)
        colour = ((220, 70, 90), (70, 150, 220), (240, 200, 70), (110, 200, 120))[car % 4]
        cabin = pygame.Rect(int(x + swing - 18), int(y + 14), 36, 26)
        box(s, colour, cabin, radius=6)
        poly(s, shade(colour, 0.7), [(cabin.x - 3, cabin.y + 2), (cabin.centerx, cabin.y - 8), (cabin.right + 3, cabin.y + 2)])
        pygame.draw.rect(s, (40, 30, 50), (cabin.x + 6, cabin.y + 6, 24, 9))
    circle(s, (150, 152, 168), hub, 18)
    stars_of_light(s, hub, 9, t, (255, 220, 120))
    box(s, (70, 55, 70), (cx - 170, GROUND_Y - 14, 340, 14))                             # loading platform
    box(s, (150, 50, 70), (cx + 150, GROUND_Y - 90, 70, 90))                              # ticket hut
    poly(s, (190, 70, 90), [(cx + 140, GROUND_Y - 90), (cx + 185, GROUND_Y - 118), (cx + 230, GROUND_Y - 90)])
    marquee(s, "THE BIG WHEEL", (cx + 185, GROUND_Y - 140), font, t=t)
