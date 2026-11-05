"""Attraction scenes of Night C, "June 1987": the park on the night of the fire, freshly painted and
busy-looking, with flames on the roofs. Each function draws one attraction around screen position cx;
ctx["t"] (seconds) drives the animations (the flames flicker)."""
import math

import pygame

from .pieces_kit import CREAM, GOLD, GROUND_Y, METAL, OUTLINE, WOOD, awning, box, bulbs, circle, marquee, poly, shade


def flames(s, x, y, width, t, height=40):
    """A row of flickering flames standing on (x, y), width pixels wide."""
    for i in range(0, width, 16):
        h = height * (0.6 + 0.4 * abs(math.sin(t * 6 + i * 0.7)))
        poly(s, (255, 110, 30), [(x + i - 9, y), (x + i + 9, y), (x + i, y - h)], outline=False)
        poly(s, (255, 210, 80), [(x + i - 4, y), (x + i + 4, y), (x + i, y - h * 0.5)], outline=False)


def main_street(s, cx, ctx, font):
    """Main Street, 1987: a candy-striped arcade front with a 'SUMMER '87' banner, a popcorn cart and
    balloons, and flames already on the roof."""
    t = ctx["t"]
    front = pygame.Rect(cx - 230, GROUND_Y - 230, 460, 230)
    box(s, (200, 70, 80), front)
    for x in range(front.x, front.right, 30):                                             # candy stripes
        pygame.draw.rect(s, (235, 225, 210), (x, front.y + 60, 15, front.height - 60))
    awning(s, front.x - 10, front.y + 40, front.width + 20, [(60, 150, 200), (240, 235, 220)], depth=26)
    door = pygame.Rect(cx - 50, GROUND_Y - 110, 100, 110)
    box(s, (50, 34, 30), door, radius=6)
    pygame.draw.rect(s, (255, 200, 120), door.inflate(-16, -16), 2, border_radius=4)
    marquee(s, "ARCADE", (cx, front.y + 15), font, color=(255, 230, 120), back=(80, 20, 40), t=t)
    banner = pygame.Rect(cx - 150, front.y + 78, 300, 30)                                 # the 1987 banner
    box(s, (40, 120, 190), banner, radius=4)
    image = font.render("SUMMER '87", True, (255, 240, 200))
    s.blit(image, image.get_rect(center=banner.center))
    flames(s, front.x + 20, front.y, front.width - 40, t, height=50)                      # the roof is burning
    cart_x = cx + 300                                                                     # popcorn cart
    box(s, (230, 60, 60), (cart_x - 40, GROUND_Y - 90, 80, 70), radius=4)
    box(s, (250, 245, 230), (cart_x - 32, GROUND_Y - 150, 64, 60), radius=4)
    for i in range(10):
        circle(s, (255, 240, 190), (cart_x - 24 + (i * 13) % 52, GROUND_Y - 140 + (i // 4) * 14), 5, outline=False)
    for side in (-1, 1):
        circle(s, OUTLINE, (cart_x + side * 30, GROUND_Y - 14), 14)
    for i, color in enumerate(((230, 70, 70), (70, 160, 230), (240, 200, 60))):           # balloons on strings
        bx = cx - 300 + i * 22
        by = GROUND_Y - 200 + int(8 * math.sin(t * 1.5 + i))
        pygame.draw.line(s, CREAM, (cx - 290, GROUND_Y - 60), (bx, by + 18), 1)
        pygame.draw.ellipse(s, color, (bx - 14, by - 18, 28, 36))
    box(s, METAL, (cx - 292, GROUND_Y - 60, 4, 60), outline=False)


def carousel_1987(s, cx, ctx, font):
    """Benny's carousel as it was in 1987: fresh paint and lit bulbs, still turning, the canopy on fire."""
    from .pieces_z1 import carousel
    t = ctx["t"]
    carousel(s, cx, ctx, font)
    flames(s, cx - 200, GROUND_Y - 236, 400, t, height=46)                                # the canopy burns
    marquee(s, "BENNY'S CAROUSEL", (cx, GROUND_Y - 330), font, color=(255, 230, 140), back=(90, 30, 40), t=t)


def henry_stage(s, cx, ctx, font):
    """The Great Henry's stage in Clown Alley: a barker's podium with a megaphone, his posters on the
    walls, striped tent walls, and flames creeping along the tent top."""
    t = ctx["t"]
    tent = pygame.Rect(cx - 270, GROUND_Y - 240, 540, 240)
    for i, x in enumerate(range(tent.x, tent.right, 45)):                                 # striped tent wall
        box(s, (210, 60, 70) if i % 2 else (245, 235, 215), (x, tent.y, 45, tent.height), outline=False)
    poly(s, (210, 60, 70), [(tent.x - 20, tent.y), (cx, tent.y - 80), (tent.right + 20, tent.y)])
    flames(s, cx - 160, tent.y - 30, 320, t, height=40)
    for px in (cx - 200, cx + 130):                                                       # posters
        poster = pygame.Rect(px, tent.y + 30, 80, 110)
        box(s, (250, 230, 160), poster, radius=3)
        circle(s, (240, 210, 180), (poster.centerx, poster.y + 38), 18)                   # Henry's face
        poly(s, (40, 40, 50), [(poster.centerx - 22, poster.y + 22), (poster.centerx + 22, poster.y + 22),
                               (poster.centerx + 14, poster.y + 4), (poster.centerx - 14, poster.y + 4)])  # top hat
        pygame.draw.line(s, (60, 30, 20), (poster.centerx - 10, poster.y + 46), (poster.centerx + 10, poster.y + 46), 3)
        image = font.render("GREAT", True, (170, 30, 30))
        s.blit(image, image.get_rect(center=(poster.centerx, poster.y + 72)))
        image = font.render("HENRY", True, (170, 30, 30))
        s.blit(image, image.get_rect(center=(poster.centerx, poster.y + 92)))
    podium = pygame.Rect(cx - 50, GROUND_Y - 110, 100, 110)                               # barker's podium
    box(s, (120, 40, 60), podium, radius=4)
    pygame.draw.rect(s, GOLD, podium.inflate(-14, -14), 2)
    poly(s, (220, 200, 90), [(cx + 30, GROUND_Y - 140), (cx + 80, GROUND_Y - 160), (cx + 80, GROUND_Y - 110)])  # megaphone
    marquee(s, "THE GREAT HENRY!", (cx, tent.y - 100), font, color=(255, 230, 140), back=(90, 20, 40), t=t)


def helter_skelter(s, cx, ctx, font):
    """The Helter Skelter: a tall striped tower with a slide spiralling round it, mats at the bottom,
    smoke pouring from the top window."""
    t = ctx["t"]
    tower = pygame.Rect(cx - 50, GROUND_Y - 300, 100, 300)
    for i, y in enumerate(range(tower.y, tower.bottom, 30)):                              # striped tower
        box(s, (240, 200, 60) if i % 2 else (210, 60, 60), (tower.x, y, tower.width, 30), outline=False)
    pygame.draw.rect(s, OUTLINE, tower, 2)
    poly(s, (60, 140, 200), [(tower.x - 20, tower.y), (cx, tower.y - 70), (tower.right + 20, tower.y)])
    for k in range(5):                                                                    # the spiral slide
        y = tower.y + 40 + k * 52
        pygame.draw.arc(s, (240, 230, 210), (cx - 110, y, 220, 60), math.pi, 2 * math.pi, 12)
        pygame.draw.arc(s, OUTLINE, (cx - 110, y, 220, 60), math.pi, 2 * math.pi, 2)
    for i in range(3):                                                                    # mats at the bottom
        box(s, (150, 60, 140), (cx + 90 + i * 40, GROUND_Y - 10, 36, 10), outline=False)
    for k in range(6):                                                                    # smoke from the top
        phase = (t * 0.25 + k / 6) % 1.0
        pygame.draw.circle(s, (70, 60, 60), (cx + int(40 * phase) + 20, tower.y - 60 - int(phase * 120)),
                           int(16 + 30 * phase))
    marquee(s, "HELTER SKELTER", (cx + 220, GROUND_Y - 220), font, color=(255, 230, 140), back=(40, 60, 100), t=t)


def food_court(s, cx, ctx, font):
    """The food court: a burger stand with a giant burger on the roof, picnic tables with umbrellas,
    a melting ice-cream sign, and a fire starting in the kitchen window."""
    t = ctx["t"]
    stand = pygame.Rect(cx + 40, GROUND_Y - 190, 220, 190)
    box(s, (240, 220, 180), stand)
    awning(s, stand.x - 8, stand.y + 20, stand.width + 16, [(220, 60, 60), (245, 240, 230)], depth=24)
    window = pygame.Rect(stand.x + 30, stand.y + 70, 160, 60)
    box(s, (60, 30, 20), window, radius=4)
    flames(s, window.x + 10, window.bottom, window.width - 20, t, height=48)              # fire in the kitchen
    bx, by = stand.centerx, stand.y - 30                                                  # giant burger on the roof
    pygame.draw.ellipse(s, (220, 150, 60), (bx - 60, by - 30, 120, 40))
    pygame.draw.rect(s, (90, 50, 30), (bx - 58, by - 4, 116, 14))
    pygame.draw.rect(s, (90, 180, 70), (bx - 62, by - 8, 124, 6))
    pygame.draw.ellipse(s, (220, 150, 60), (bx - 58, by + 8, 116, 20))
    for i in range(2):                                                                    # picnic tables
        x = cx - 220 + i * 150
        box(s, WOOD, (x - 50, GROUND_Y - 50, 100, 10))
        for leg in (-40, 40):
            pygame.draw.line(s, shade(WOOD, 0.7), (x + leg, GROUND_Y - 40), (x + leg, GROUND_Y), 5)
        pygame.draw.line(s, METAL, (x, GROUND_Y - 50), (x, GROUND_Y - 150), 3)
        poly(s, ((230, 80, 80), (60, 150, 200))[i], [(x - 60, GROUND_Y - 130), (x, GROUND_Y - 170), (x + 60, GROUND_Y - 130)])
    cone_x, cone_y = cx - 60, GROUND_Y - 260                                              # ice-cream sign, melting
    box(s, METAL, (cone_x - 4, cone_y + 40, 8, GROUND_Y - cone_y - 40), outline=False)    # on a pole
    poly(s, (220, 170, 100), [(cone_x - 20, cone_y), (cone_x + 20, cone_y), (cone_x, cone_y + 50)])
    circle(s, (250, 200, 220), (cone_x, cone_y - 12), 24)
    drip = int(10 + 8 * abs(math.sin(t)))
    pygame.draw.line(s, (250, 200, 220), (cone_x + 12, cone_y), (cone_x + 12, cone_y + drip), 5)
    marquee(s, "FOOD COURT", (cx + 150, GROUND_Y - 260), font, color=(255, 230, 140), back=(90, 30, 30), t=t)


def workshop_1987(s, cx, ctx, font):
    """Walt's workshop on the night of the fire: the old radio on the workbench throws sparks, the
    wiring above it is already burning, and tools hang on the wall where he left them."""
    t = ctx["t"]
    room = pygame.Rect(cx - 260, GROUND_Y - 260, 520, 260)
    box(s, (90, 76, 70), room)
    for x in range(room.x, room.right, 40):                                               # brick lines
        for y in range(room.y, room.bottom, 20):
            pygame.draw.rect(s, (80, 66, 60), (x + (y // 20 % 2) * 20, y, 40, 20), 1)
    bench = pygame.Rect(cx - 200, GROUND_Y - 100, 300, 16)
    box(s, WOOD, bench)
    for leg in (bench.x + 10, bench.right - 20):
        box(s, shade(WOOD, 0.7), (leg, bench.bottom, 10, GROUND_Y - bench.bottom), outline=False)
    radio = pygame.Rect(cx - 120, bench.y - 60, 90, 60)                                   # the old radio
    box(s, (120, 70, 40), radio, radius=8)
    circle(s, (60, 40, 30), (radio.x + 28, radio.centery), 18)
    for k in range(3):
        pygame.draw.line(s, GOLD, (radio.x + 54, radio.y + 16 + k * 12), (radio.right - 8, radio.y + 16 + k * 12), 2)
    if int(t * 10) % 3 == 0:                                                              # sparks
        for k in range(6):
            a = k * 1.05 + t
            pygame.draw.line(s, (255, 250, 170), (radio.right, radio.y + 6),
                             (radio.right + int(18 * math.cos(a)), radio.y + 6 + int(18 * math.sin(a))), 2)
    pygame.draw.line(s, (40, 36, 34), (radio.right - 10, radio.y), (cx + 60, room.y + 30), 3)   # wire to the ceiling
    flames(s, cx - 20, room.y + 40, 240, t, height=36)                                    # the burning wiring
    for i in range(5):                                                                    # tools on the wall
        x = cx + 120 + (i % 3) * 36
        y = room.y + 90 + (i // 3) * 60
        pygame.draw.line(s, METAL, (x, y), (x, y + 44), 5)
        circle(s, METAL, (x, y), 7)
    calendar = pygame.Rect(cx - 240, room.y + 40, 70, 80)                                 # the calendar
    box(s, CREAM, calendar)
    image = font.render("JUN 87", True, (170, 30, 30))
    s.blit(image, image.get_rect(center=(calendar.centerx, calendar.y + 22)))
    marquee(s, "W. HALE - REPAIRS", (cx, room.y - 22), font, color=(255, 220, 160), back=(60, 40, 30), t=t)


def main_gate_1987(s, cx, ctx, font):
    """Night C's finale: the main gate on the night of the fire, with flames along the arch."""
    from .pieces_z3 import draw_big_gate
    t = ctx["t"]
    draw_big_gate(s, cx, 0.0, font)
    flames(s, cx - 170, GROUND_Y - 300, 340, t, height=44)
    for side in (-1, 1):
        flames(s, cx + side * 190 - 24, GROUND_Y - 160, 48, t, height=30)


FIRE_PIECES = {"main_street": main_street, "carousel_1987": carousel_1987, "henry_stage": henry_stage,
               "helter_skelter": helter_skelter, "food_court": food_court, "workshop_1987": workshop_1987,
               "main_gate_1987": main_gate_1987}
