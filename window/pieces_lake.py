"""Attraction scenes of Night B, "The Lakeside" (the part of the park closed after the fire). Each
function draws one attraction around screen position cx; ctx["t"] (seconds) drives the animations."""
import math

import pygame

from .pieces_kit import CREAM, GOLD, GROUND_Y, METAL, OUTLINE, WOOD, box, bulbs, circle, marquee, poly, shade

RUST = (140, 80, 50)


def bumper_cars(s, cx, ctx, font):
    """A bumper-car pavilion: a flat roof on poles with a sparking ceiling grid, and old cars that still
    drift around the floor on their own."""
    t = ctx["t"]
    roof = pygame.Rect(cx - 250, GROUND_Y - 250, 500, 34)
    for x in (cx - 240, cx - 80, cx + 80, cx + 240):                                      # poles
        box(s, METAL, (x - 6, roof.bottom, 12, GROUND_Y - roof.bottom), outline=False)
    box(s, (60, 70, 90), roof, radius=4)
    for i in range(0, 500, 25):                                                           # ceiling grid
        pygame.draw.line(s, (90, 96, 110), (roof.x + i, roof.bottom), (roof.x + i + 30, roof.bottom + 14), 1)
    marquee(s, "DODGEMS", (cx, roof.y - 18), font, color=(130, 220, 255), back=(30, 40, 70), t=t)
    floor = pygame.Rect(cx - 240, GROUND_Y - 30, 480, 30)                                 # the metal floor
    box(s, (70, 72, 80), floor)
    colors = ((210, 60, 60), (60, 140, 210), (230, 190, 60), (90, 180, 110))
    for i in range(4):                                                                    # drifting cars
        x = cx + int(190 * math.sin(t * 0.4 + i * 1.7))
        y = GROUND_Y - 40 + (i % 2) * 8
        car = pygame.Rect(x - 40, y - 26, 80, 30)
        box(s, colors[i], car, radius=12)
        box(s, (30, 30, 34), (car.x - 4, car.bottom - 8, car.width + 8, 10), radius=5)    # rubber bumper
        box(s, shade(colors[i], 0.6), (x - 14, y - 40, 28, 16), radius=4)                 # seat back
        pygame.draw.line(s, METAL, (x + 10, y - 34), (x + 10, roof.bottom), 2)           # pole to the ceiling
        if int(t * 8 + i * 3) % 11 == 0:                                                  # a spark at the grid
            for k in range(5):
                a = k * 1.25
                pygame.draw.line(s, (255, 250, 180), (x + 10, roof.bottom + 2),
                                 (x + 10 + int(12 * math.cos(a)), roof.bottom + 2 + int(12 * math.sin(a))), 2)
    sign = pygame.Rect(cx + 150, GROUND_Y - 120, 110, 50)                                 # "CLOSED" sign on a chain
    box(s, CREAM, sign, radius=4)
    image = font.render("CLOSED", True, (170, 30, 30))
    s.blit(image, image.get_rect(center=sign.center))
    pygame.draw.line(s, METAL, (sign.x + 10, sign.y), (cx + 80, roof.bottom), 2)
    pygame.draw.line(s, METAL, (sign.right - 10, sign.y), (cx + 240, roof.bottom), 2)


def photo_pier(s, cx, ctx, font):
    """Rosa's photo stand at the end of the pier: a wooden pier over the water, a big painted cut-out
    board with holes for faces, an old box camera on a tripod, and her photos pegged on a line."""
    t = ctx["t"]
    deck = pygame.Rect(cx - 260, GROUND_Y - 16, 520, 16)                                  # the pier
    box(s, WOOD, deck)
    for x in range(cx - 250, cx + 260, 60):
        box(s, shade(WOOD, 0.7), (x, GROUND_Y - 4, 12, 30), outline=False)
    board = pygame.Rect(cx - 210, GROUND_Y - 230, 220, 214)                               # cut-out board
    box(s, (240, 220, 180), board, radius=6)
    # two painted figures, a lady in a ball gown and a strongman, with holes where the faces should be
    lady, strong = board.x + 60, board.x + 160
    poly(s, (220, 80, 110), [(lady - 45, board.bottom - 8), (lady - 18, board.y + 112), (lady + 18, board.y + 112),
                             (lady + 45, board.bottom - 8)])                              # gown
    box(s, (220, 80, 110), (lady - 18, board.y + 104, 36, 20), outline=False)
    for i in range(5):                                                                    # frills
        pygame.draw.arc(s, (250, 210, 220), (lady - 44 + i * 18, board.bottom - 30, 18, 14), math.pi, 2 * math.pi, 3)
    pygame.draw.circle(s, (255, 230, 240), (lady, board.y + 102), 9)                      # a rose
    box(s, (240, 200, 170), (strong - 34, board.y + 104, 68, 60), radius=10)              # strongman's chest
    for k in range(2):
        pygame.draw.line(s, (60, 40, 30), (strong - 34, board.y + 112 + k * 10), (strong + 34, board.y + 112 + k * 10), 4)
    box(s, (40, 40, 70), (strong - 30, board.y + 164, 60, board.bottom - board.y - 172), outline=False)  # trousers
    pygame.draw.line(s, METAL, (strong - 70, board.y + 100), (strong + 70, board.y + 100), 6)   # barbell
    for side in (-1, 1):
        circle(s, (40, 40, 44), (strong + side * 72, board.y + 100), 16)
        pygame.draw.line(s, (240, 200, 170), (strong + side * 34, board.y + 110), (strong + side * 50, board.y + 100), 10)
    for hx in (lady, strong):                                                             # holes for faces
        circle(s, (16, 22, 32), (hx, board.y + 78), 22)
        pygame.draw.circle(s, (120, 100, 80), (hx, board.y + 78), 22, 3)
    marquee(s, "ROSA'S PHOTOS", (board.centerx, board.y - 20), font, color=(255, 220, 160), back=(60, 30, 50), t=t)
    tripod_x = cx + 120                                                                   # box camera on a tripod
    for dx in (-24, 0, 24):
        pygame.draw.line(s, (60, 50, 40), (tripod_x, GROUND_Y - 120), (tripod_x + dx, GROUND_Y - 16), 4)
    box(s, (40, 36, 34), (tripod_x - 30, GROUND_Y - 160, 60, 44), radius=4)
    circle(s, (100, 110, 130), (tripod_x - 30, GROUND_Y - 138), 12)                      # the lens
    if int(t * 0.5) % 4 == 0 and (t * 0.5) % 1 < 0.15:                                    # a ghostly flash now and then
        flash = pygame.Surface((240, 240), pygame.SRCALPHA)
        pygame.draw.circle(flash, (255, 255, 240, 120), (120, 120), 120)
        s.blit(flash, (tripod_x - 150, GROUND_Y - 258))
    line_y = GROUND_Y - 200                                                               # photos on a line
    pygame.draw.line(s, CREAM, (cx + 40, line_y), (cx + 250, line_y + 10), 1)
    for i in range(5):
        px = cx + 50 + i * 42
        py = line_y + i * 2 + int(3 * math.sin(t * 2 + i))
        box(s, (235, 230, 215), (px, py, 30, 38), outline=False)
        pygame.draw.rect(s, (90, 80, 70), (px + 4, py + 4, 22, 22))
        pygame.draw.circle(s, (200, 190, 170), (px + 15, py + 14), 6)


def water(s, cx, half_width, t, top=GROUND_Y - 30):
    """A strip of dark lake water with moving ripples in front of a dock."""
    rect = pygame.Rect(cx - half_width, top, 2 * half_width, GROUND_Y - top + 4)
    pygame.draw.rect(s, (22, 40, 56), rect)
    for row in range(3):
        y = top + 8 + row * 9
        for x in range(rect.x, rect.right, 40):
            shift = int(10 * math.sin(t * 1.5 + x * 0.05 + row))
            pygame.draw.line(s, (70, 100, 120), (x + shift, y), (x + shift + 16, y), 2)


def swan_boats(s, cx, ctx, font):
    """The swan-boat dock: a ticket hut, a wooden jetty and big white swan pedal boats that bob on the
    water, one of them with a broken neck."""
    t = ctx["t"]
    water(s, cx, 280, t, top=GROUND_Y - 60)
    for i in range(3):                                                                    # the swan boats
        x = cx - 170 + i * 150
        bob = int(4 * math.sin(t * 1.6 + i))
        y = GROUND_Y - 58 + bob
        hull = pygame.Rect(x - 55, y - 28, 110, 40)
        pygame.draw.ellipse(s, (235, 235, 240), hull)
        pygame.draw.ellipse(s, OUTLINE, hull, 2)
        poly(s, (225, 225, 232), [(x + 40, y - 18), (x + 62, y - 28), (x + 56, y - 4)])   # tail feathers
        box(s, (90, 140, 200), (x - 30, y - 34, 50, 12), radius=4)                       # the seat
        if i == 1:                                                                        # the broken one
            pygame.draw.line(s, (235, 235, 240), (x - 46, y - 18), (x - 74, y - 6), 12)
            circle(s, (235, 235, 240), (x - 80, y - 2), 11)
        else:
            pygame.draw.arc(s, (235, 235, 240), (x - 70, y - 100, 40, 90), math.pi * 0.5, math.pi * 1.5, 11)
            circle(s, (235, 235, 240), (x - 52, y - 98), 12)
            poly(s, (240, 150, 40), [(x - 64, y - 100), (x - 80, y - 94), (x - 64, y - 90)], outline=False)
            pygame.draw.circle(s, OUTLINE, (x - 56, y - 101), 2)
    hut = pygame.Rect(cx + 160, GROUND_Y - 200, 120, 140)                                 # ticket hut
    box(s, (190, 200, 210), hut)
    poly(s, (60, 110, 160), [(hut.x - 12, hut.y), (hut.centerx, hut.y - 40), (hut.right + 12, hut.y)])
    box(s, (40, 50, 60), (hut.x + 24, hut.y + 30, 72, 44), radius=4)
    marquee(s, "SWAN BOATS", (cx - 40, GROUND_Y - 250), font, color=(230, 240, 255), back=(30, 50, 80), t=t)


def mirror_maze(s, cx, ctx, font):
    """Lily's Mirror Maze: an open-air glass pavilion. Tall panes in silver frames stand at angles,
    each with a faint reflection of the player (never of Walt)."""
    t = ctx["t"]
    roof = pygame.Rect(cx - 280, GROUND_Y - 270, 560, 24)
    poly(s, (150, 160, 175), [(roof.x - 16, roof.bottom), (cx, roof.y - 40), (roof.right + 16, roof.bottom)])
    box(s, (120, 130, 145), roof)
    marquee(s, "MIRROR MAZE", (cx, roof.y - 52), font, color=(200, 230, 255), back=(40, 50, 70), t=t)
    for i in range(5):
        x = cx - 230 + i * 115
        lean = (-1) ** i * 10                                                             # panes stand at angles
        pane = pygame.Rect(x - 40, GROUND_Y - 236, 80, 220)
        glass = pygame.Surface(pane.size, pygame.SRCALPHA)
        glass.fill((120, 160, 190, 130))
        image = ctx["sprites"]["player"][0]
        small = pygame.transform.scale(image, (int(image.get_width() * 0.6), int(image.get_height() * 0.6)))
        small = pygame.transform.flip(small, True, False)
        small.set_alpha(150)
        offset = int((ctx["player_x"] - 480) / 25)                                        # moves when you move
        glass.blit(small, (pane.width // 2 - small.get_width() // 2 + offset, pane.height - small.get_height() - 6))
        pygame.draw.line(glass, (255, 255, 255, 90), (10, 40), (40, 6), 5)               # shine
        glass = pygame.transform.rotate(glass, lean)
        s.blit(glass, glass.get_rect(midbottom=(x, GROUND_Y)))
        frame = glass.get_rect(midbottom=(x, GROUND_Y))
        pygame.draw.rect(s, (200, 205, 215), frame, 3)
        if int(t * 2 + i) % 7 == 0:                                                       # a glint travels along
            pygame.draw.line(s, (255, 255, 255), (frame.x + 10, frame.y + 30), (frame.x + 30, frame.y + 10), 3)
    for x in (cx - 280, cx + 280):                                                        # corner posts
        box(s, (120, 130, 145), (x - 7, roof.bottom, 14, GROUND_Y - roof.bottom), outline=False)


def bandstand(s, cx, ctx, font):
    """A round bandstand by the lake: white columns, a striped dome roof, music stands and a drum,
    and notes that drift out of it although nobody plays."""
    t = ctx["t"]
    base = pygame.Rect(cx - 220, GROUND_Y - 40, 440, 40)
    box(s, (200, 195, 185), base, radius=6)
    for i in range(5):                                                                    # steps
        pygame.draw.line(s, (170, 165, 155), (cx - 60, GROUND_Y - 8 - i * 8), (cx + 60, GROUND_Y - 8 - i * 8), 2)
    for x in range(cx - 200, cx + 201, 100):                                              # columns
        box(s, (235, 232, 222), (x - 8, GROUND_Y - 230, 16, 190), outline=True)
    dome = [(cx - 240, GROUND_Y - 228), (cx, GROUND_Y - 320), (cx + 240, GROUND_Y - 228)]
    poly(s, (190, 70, 80), dome)
    for k in range(-3, 4):                                                                # stripes on the dome
        pygame.draw.line(s, (240, 230, 215), (cx, GROUND_Y - 318), (cx + k * 70, GROUND_Y - 230), 6)
    pygame.draw.line(s, GOLD, (cx, GROUND_Y - 320), (cx, GROUND_Y - 350), 3)
    for x in (cx - 120, cx - 40, cx + 40):                                                # music stands
        pygame.draw.line(s, OUTLINE, (x, GROUND_Y - 40), (x, GROUND_Y - 110), 3)
        box(s, (60, 56, 50), (x - 18, GROUND_Y - 130, 36, 22), outline=False)
    box(s, (180, 40, 50), (cx + 110, GROUND_Y - 100, 70, 60), radius=8)                   # bass drum
    circle(s, CREAM, (cx + 145, GROUND_Y - 70), 22)
    for i in range(4):                                                                    # drifting notes
        phase = (t * 0.3 + i / 4) % 1.0
        nx = cx - 80 + i * 50 + int(20 * math.sin(phase * 6))
        ny = GROUND_Y - 150 - int(phase * 120)
        pygame.draw.circle(s, (230, 230, 200), (nx, ny), 5)
        pygame.draw.line(s, (230, 230, 200), (nx + 5, ny), (nx + 5, ny - 16), 2)
    marquee(s, "BANDSTAND", (cx, GROUND_Y - 360), font, color=(255, 230, 190), back=(70, 30, 40), t=t)


def wild_mouse(s, cx, ctx, font):
    """The station of the Wild Mouse coaster: a zig-zag track high above, a little mouse-faced car
    stuck at the top of the lift hill, and the station hut with a height-check sign."""
    t = ctx["t"]
    points = [(cx - 300, GROUND_Y - 90), (cx - 180, GROUND_Y - 280), (cx - 60, GROUND_Y - 280),
              (cx - 60, GROUND_Y - 200), (cx + 120, GROUND_Y - 200), (cx + 120, GROUND_Y - 140),
              (cx + 300, GROUND_Y - 140)]
    for x, y in points:                                                                   # supports
        pygame.draw.line(s, (140, 100, 70), (x, y), (x, GROUND_Y), 5)
    pygame.draw.lines(s, (200, 60, 60), False, points, 6)                                 # the track
    pygame.draw.lines(s, OUTLINE, False, [(x, y + 8) for x, y in points], 2)
    shake = int(2 * math.sin(t * 9))                                                      # the stuck mouse car
    car = pygame.Rect(cx - 160 + shake, GROUND_Y - 310, 70, 30)
    box(s, (150, 150, 160), car, radius=10)
    for side in (0, 1):
        circle(s, (150, 150, 160), (car.x + 14 + side * 20, car.y - 6), 9)                # mouse ears
    pygame.draw.circle(s, OUTLINE, (car.right - 10, car.y + 12), 3)
    hut = pygame.Rect(cx + 140, GROUND_Y - 120, 150, 120)                                 # station hut
    box(s, (230, 200, 90), hut)
    poly(s, (200, 60, 60), [(hut.x - 10, hut.y), (hut.centerx, hut.y - 36), (hut.right + 10, hut.y)])
    marquee(s, "WILD MOUSE", (hut.centerx, hut.y - 52), font, color=(255, 240, 160), back=(80, 30, 30), t=t)
    sign_x = cx - 240                                                                     # "you must be this tall"
    box(s, (240, 220, 120), (sign_x - 6, GROUND_Y - 150, 12, 150), outline=False)
    box(s, (240, 220, 120), (sign_x - 30, GROUND_Y - 170, 60, 30), radius=4)
    pygame.draw.line(s, OUTLINE, (sign_x + 6, GROUND_Y - 150), (sign_x + 30, GROUND_Y - 150), 3)


def lake_gate(s, cx, ctx, font):
    """Night B's finale: the old staff gate by the water, the same iron gate as the main exit but
    overgrown with ivy and wrapped in grey smoke."""
    from .pieces_z3 import draw_big_gate
    t = ctx["t"]
    draw_big_gate(s, cx, 0.0, font)
    for i in range(30):                                                                   # ivy on the pillars
        side = -1 if i % 2 else 1
        y = GROUND_Y - 30 - (i // 2) * 16
        circle(s, (50, 90, 60), (cx + side * 190 + int(16 * math.sin(i)), y), 8, outline=False)
    smoke = pygame.Surface((560, 300), pygame.SRCALPHA)                                   # smoke drifting through
    for k in range(7):
        x = int((t * 30 + k * 90) % 640) - 40
        pygame.draw.circle(smoke, (90, 90, 96, 70), (x, 200 - k * 18), 50)
    s.blit(smoke, (cx - 280, GROUND_Y - 300))


LAKE_PIECES = {"bumper_cars": bumper_cars, "photo_pier": photo_pier, "swan_boats": swan_boats,
               "mirror_maze": mirror_maze, "bandstand": bandstand, "wild_mouse": wild_mouse,
               "lake_gate": lake_gate}
