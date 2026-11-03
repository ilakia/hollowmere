"""Attraction scenes of zone 3, the Dark Rides, plus the big exit gate. Each function draws one
attraction around screen position cx; ctx["t"] (seconds) drives the animations."""
import math
import random

import pygame

from .pieces_kit import (CREAM, GOLD, GROUND_Y, METAL, OUTLINE, WOOD, box, bulbs, circle, marquee, person, poly,
                         shade)

BONE = (226, 220, 200)


def skull(s, x, y, r, eye=(255, 60, 40)):
    circle(s, BONE, (x, y), r)
    pygame.draw.rect(s, BONE, (x - r * 0.6, y + r * 0.4, r * 1.2, r * 0.7))
    circle(s, eye, (x - r * 0.38, y - r * 0.05), r * 0.26, outline=False)
    circle(s, eye, (x + r * 0.38, y - r * 0.05), r * 0.26, outline=False)
    for i in range(4):
        pygame.draw.line(s, OUTLINE, (x - r * 0.45 + i * r * 0.3, y + r * 0.45), (x - r * 0.45 + i * r * 0.3, y + r), 2)


def track_point(u, cx):
    """A looping roller-coaster path (u from 0 to 1): it climbs, dives and loops across the scene."""
    a = u * 2 * math.pi
    x = cx + 300 * math.sin(a)
    y = GROUND_Y - 150 - 90 * math.sin(2 * a) - 30 * math.cos(3 * a)
    return x, y


def ghost_train(s, cx, ctx, font):
    """A long haunted track that dives and loops over a spooky station, with a train of four cars
    racing around it like crazy (skeleton passengers), tombstones and green glowing eyes."""
    t = ctx["t"]
    station = pygame.Rect(cx - 120, GROUND_Y - 170, 240, 170)                            # haunted station
    poly(s, (40, 26, 36), [(station.x - 20, station.y), (station.centerx, station.y - 70), (station.right + 20, station.y)])
    box(s, (55, 34, 46), station)
    tunnel = pygame.Rect(station.centerx - 55, GROUND_Y - 120, 110, 120)
    pygame.draw.rect(s, (8, 4, 8), tunnel, border_top_left_radius=55, border_top_right_radius=55)
    skull(s, station.centerx, station.y - 22, 20)
    for i in range(3):                                                                    # eyes in the tunnel
        if math.sin(t * 2 + i * 2) > 0.2:
            ex, ey = tunnel.x + 25 + i * 30, tunnel.y + 50 + (i % 2) * 20
            pygame.draw.circle(s, (120, 255, 120), (ex, ey), 3)
            pygame.draw.circle(s, (120, 255, 120), (ex + 9, ey), 3)
    points = [track_point(u / 120, cx) for u in range(121)]                               # the long track
    for x, y in points[::6]:
        pygame.draw.line(s, (60, 40, 40), (x, y + 6), (x, GROUND_Y), 3)                  # supports
    pygame.draw.lines(s, (110, 40, 40), False, points, 7)
    pygame.draw.lines(s, (170, 70, 60), False, [(x, y - 4) for x, y in points], 2)
    for i in range(4):                                                                    # the speeding train
        u = (t * 0.32 - i * 0.035) % 1.0
        x, y = track_point(u, cx)
        nx, ny = track_point((u + 0.01) % 1.0, cx)
        angle = math.degrees(math.atan2(-(ny - y), nx - x))
        car = pygame.Surface((54, 40), pygame.SRCALPHA)
        box(car, (150, 25, 40) if i else (40, 40, 50), (2, 14, 50, 24), radius=6)
        if i == 0:
            circle(car, (255, 230, 120), (46, 24), 6)                                      # headlight
        else:
            circle(car, BONE, (26, 10), 8, outline=False)                                  # skeleton passenger
            pygame.draw.circle(car, OUTLINE, (23, 9), 2)
            pygame.draw.circle(car, OUTLINE, (29, 9), 2)
            pygame.draw.line(car, BONE, (18, 16), (10, 2 + (i % 2) * 6), 3)                # arms up!
        car = pygame.transform.rotate(car, angle)
        s.blit(car, car.get_rect(center=(int(x), int(y) - 14)))
    for i, x in enumerate((cx - 250, cx - 200, cx + 210, cx + 260)):                      # tombstones
        box(s, (90, 90, 100), (x - 16, GROUND_Y - 40 - (i % 2) * 8, 32, 40 + (i % 2) * 8), radius=12)
        pygame.draw.line(s, OUTLINE, (x - 6, GROUND_Y - 24), (x + 6, GROUND_Y - 24), 2)
    marquee(s, "GHOST TRAIN", (cx, station.y - 96), font, color=(255, 90, 70), back=(40, 10, 16), t=t)


def tunnel_boats(s, cx, ctx, font):
    """Tunnel of Boats: black water, a tunnel through a giant skull's mouth, boats with lanterns
    drifting in, glowing eyes in the dark, hanging vines and mist."""
    t = ctx["t"]
    rock = pygame.Rect(cx - 260, GROUND_Y - 280, 520, 280)
    poly(s, (50, 40, 46), [(rock.x, GROUND_Y), (rock.x + 30, rock.y + 60), (rock.x + 140, rock.y), (rock.right - 120, rock.y + 10),
                           (rock.right - 20, rock.y + 80), (rock.right, GROUND_Y)])
    head = (cx, GROUND_Y - 160)                                                            # the giant skull
    circle(s, (200, 190, 170), head, 120)
    for dx in (-48, 48):
        circle(s, (20, 10, 14), (head[0] + dx, head[1] - 30), 30)
        glow = 120 + int(120 * abs(math.sin(t * 1.5 + dx)))
        pygame.draw.circle(s, (glow, 40, 30), (head[0] + dx, head[1] - 28), 9)              # burning eyes
    poly(s, (20, 10, 14), [(head[0] - 12, head[1] + 10), (head[0] + 12, head[1] + 10), (head[0], head[1] - 10)])
    mouth = pygame.Rect(head[0] - 90, head[1] + 20, 180, GROUND_Y - head[1] - 20)
    pygame.draw.rect(s, (5, 3, 6), mouth, border_top_left_radius=50, border_top_right_radius=50)
    for i in range(7):                                                                    # teeth over the entrance
        pygame.draw.rect(s, (220, 210, 190), (mouth.x + 8 + i * 24, mouth.y - 4, 18, 22), border_radius=4)
    for i in range(6):                                                                    # hanging vines
        x = rock.x + 40 + i * 85
        length = 70 + (i % 3) * 30
        sway = int(6 * math.sin(t + i))
        pygame.draw.line(s, (40, 80, 40), (x, rock.y + 40), (x + sway, rock.y + 40 + length), 3)
    water = pygame.Rect(cx - 320, GROUND_Y - 34, 640, 34)
    pygame.draw.rect(s, (10, 18, 28), water)
    for i in range(16):                                                                   # ripples
        x = water.x + (i * 40 + int(t * 30)) % water.width
        pygame.draw.arc(s, (60, 90, 120), (x, water.y + 8 + (i % 3) * 8, 34, 10), 0, math.pi, 2)
    for i in range(2):                                                                    # boats drifting into the mouth
        phase = (t * 0.06 + i * 0.5) % 1.0
        bx = int(water.x + 40 + phase * 380)
        alpha = 255 if bx < cx - 40 else max(0, int(255 * (1 - (bx - cx + 40) / 80)))
        boat = pygame.Surface((110, 70), pygame.SRCALPHA)
        poly(boat, (130, 80, 50), [(5, 46), (105, 46), (90, 66), (20, 66)])
        poly(boat, (230, 220, 200), [(92, 46), (104, 14), (98, 46)])                      # swan neck
        pygame.draw.line(boat, METAL, (30, 46), (30, 14), 2)
        pygame.draw.circle(boat, (255, 200, 90), (30, 12), 6)                              # lantern
        boat.set_alpha(alpha)
        s.blit(boat, (bx - 55, water.y - 40 + int(3 * math.sin(t * 2 + i))))
    mist = pygame.Surface((640, 60), pygame.SRCALPHA)
    for i in range(6):
        pygame.draw.ellipse(mist, (180, 190, 210, 40), (i * 110 + int(20 * math.sin(t * 0.5 + i)), 10, 180, 40))
    s.blit(mist, (cx - 320, GROUND_Y - 70))
    marquee(s, "TUNNEL OF BOATS", (cx, rock.y - 12), font, color=(180, 220, 255), back=(20, 30, 50), t=t)


def haunted_manor(s, cx, ctx, font):
    """A gothic manor with two towers, flickering windows, a figure that passes a window, an iron
    fence, tombstones and bats."""
    t = ctx["t"]
    body = pygame.Rect(cx - 170, GROUND_Y - 220, 340, 220)
    box(s, (52, 40, 64), body)
    poly(s, (36, 26, 46), [(body.x - 10, body.y), (cx, body.y - 70), (body.right + 10, body.y)])
    for side in (-1, 1):                                                                  # towers with spires
        tower = pygame.Rect(cx + side * 190 - 40, GROUND_Y - 290, 80, 290)
        box(s, (46, 34, 58), tower)
        poly(s, (30, 22, 40), [(tower.x - 8, tower.y), (tower.centerx, tower.y - 80), (tower.right + 8, tower.y)])
        lit = math.sin(t * 2.3 + side) > -0.2
        pygame.draw.rect(s, (255, 190, 90) if lit else (30, 24, 34), (tower.centerx - 12, tower.y + 40, 24, 40),
                         border_top_left_radius=12, border_top_right_radius=12)
    for i, x in enumerate((body.x + 40, body.x + 130, body.x + 220)):                     # windows
        win = pygame.Rect(x, body.y + 40, 60, 70)
        lit = math.sin(t * 3 + i * 2) > -0.4
        pygame.draw.rect(s, (255, 200, 100) if lit else (35, 28, 40), win, border_top_left_radius=30, border_top_right_radius=30)
        pygame.draw.line(s, OUTLINE, (win.centerx, win.y), (win.centerx, win.bottom), 3)
        pygame.draw.line(s, OUTLINE, (win.x, win.y + 35), (win.right, win.y + 35), 3)
    walker = (t * 0.25) % 1.0                                                             # a shadow walks past
    if 0.2 < walker < 0.8 and lit:
        wx = body.x + 40 + int((walker - 0.2) / 0.6 * 240)
        pygame.draw.ellipse(s, (20, 10, 20), (wx, body.y + 52, 22, 56))
    door = pygame.Rect(cx - 32, GROUND_Y - 100, 64, 100)
    box(s, (60, 30, 30), door, radius=30)
    circle(s, GOLD, (door.right - 14, door.centery), 4)
    for x in range(cx - 300, cx + 300, 16):                                               # iron fence
        pygame.draw.line(s, (25, 22, 30), (x, GROUND_Y - 50), (x, GROUND_Y), 3)
        poly(s, (25, 22, 30), [(x - 4, GROUND_Y - 50), (x, GROUND_Y - 60), (x + 4, GROUND_Y - 50)], outline=False)
    pygame.draw.line(s, (25, 22, 30), (cx - 300, GROUND_Y - 40), (cx + 300, GROUND_Y - 40), 3)
    for i in range(4):                                                                    # bats
        x = cx - 200 + i * 130 + int(40 * math.sin(t * 0.8 + i))
        y = 120 + int(14 * math.sin(t * 3 + i))
        flap = 8 if math.sin(t * 12 + i) > 0 else -4
        poly(s, OUTLINE, [(x - 16, y - flap), (x, y + 4), (x + 16, y - flap), (x, y - 2)], outline=False)
    marquee(s, "HAUNTED MANOR", (cx, body.y - 92), font, color=(220, 180, 255), back=(40, 20, 50), t=t)


def log_flume(s, cx, ctx, font):
    """A rocky mountain with a wooden flume: logs ride down the chute and splash into the pool."""
    t = ctx["t"]
    poly(s, (70, 60, 56), [(cx - 300, GROUND_Y), (cx - 260, GROUND_Y - 230), (cx - 160, GROUND_Y - 280),
                           (cx - 60, GROUND_Y - 200), (cx - 20, GROUND_Y)])
    for i in range(4):                                                                    # pine trees on the mountain
        x = cx - 270 + i * 60
        poly(s, (30, 70, 50), [(x, GROUND_Y - 150 - (i % 2) * 40), (x - 18, GROUND_Y - 100 - (i % 2) * 40),
                               (x + 18, GROUND_Y - 100 - (i % 2) * 40)])
    top, bottom = (cx - 200, GROUND_Y - 240), (cx + 150, GROUND_Y - 40)
    for i in range(9):                                                                    # wooden supports
        u = i / 8
        x = top[0] + (bottom[0] - top[0]) * u
        y = top[1] + (bottom[1] - top[1]) * u
        pygame.draw.line(s, shade(WOOD, 0.8), (x, y + 10), (x, GROUND_Y), 5)
    pygame.draw.line(s, WOOD, top, bottom, 22)                                            # the chute
    pygame.draw.line(s, (80, 140, 200), (top[0], top[1] - 4), (bottom[0], bottom[1] - 4), 8)  # water in it
    pool = pygame.Rect(cx + 100, GROUND_Y - 34, 230, 34)
    pygame.draw.rect(s, (40, 90, 140), pool, border_radius=10)
    for i in range(2):                                                                    # logs riding down
        u = (t * 0.28 + i * 0.5) % 1.0
        x = top[0] + (bottom[0] - top[0]) * u
        y = top[1] + (bottom[1] - top[1]) * u
        log = pygame.Surface((80, 30), pygame.SRCALPHA)
        box(log, (150, 95, 55), (0, 6, 80, 22), radius=10)
        circle(log, (200, 150, 100), (8, 17), 9)
        log = pygame.transform.rotate(log, -30)
        s.blit(log, log.get_rect(center=(int(x), int(y) - 14)))
        if u > 0.9:                                                                       # splash!
            for k in range(10):
                angle = k * 0.6
                d = (u - 0.9) * 400
                circle(s, (190, 225, 255), (bottom[0] + 30 + d * math.cos(angle), bottom[1] - 20 - abs(d * math.sin(angle))), 5,
                       outline=False)
    marquee(s, "LOG FLUME", (cx + 60, GROUND_Y - 290), font, color=(170, 230, 255), back=(30, 50, 40), t=t)


WAX_FIGURES = [
    {"name": "GRANNY MAE", "body": (120, 90, 140), "hair": (200, 200, 205), "hair_style": "bun", "extra": "cane",
     "dress": True, "glasses": True},
    {"name": "THE SOLDIER", "body": (180, 30, 40), "legs": (40, 40, 60), "hat": "shako", "extra": "rifle",
     "cross_straps": True, "hair_style": "none"},
    {"name": "THE QUEEN", "body": (90, 40, 140), "hair": (120, 70, 40), "hair_style": "long", "hat": "crown",
     "dress": True, "extra": "flower"},
    {"name": "CAPTAIN", "body": (40, 50, 90), "legs": (220, 210, 190), "hat": "tricorn", "extra": "sword",
     "eye": "patch", "beard": (60, 40, 30), "belt": GOLD, "hair_style": "none"},
    {"name": "THE BALLERINA", "body": (250, 190, 210), "hair": (60, 40, 30), "hair_style": "bun", "extra": "tutu"},
    {"name": "BINGO", "body": (230, 200, 60), "legs": (60, 120, 200), "hat": "clown", "clown_face": True,
     "extra": "balloon", "hair_style": "none"},
    {"name": "STRONGMAN", "body": (200, 60, 60), "legs": (40, 40, 50), "beard": (50, 35, 25), "belt": GOLD,
     "hair_style": "none"},
]


def wax_museum(s, cx, ctx, font):
    """A gallery of wax figures on pedestals, each a different character, with velvet ropes. Now and
    then one of them turns its head."""
    t = ctx["t"]
    hall = pygame.Rect(cx - 330, GROUND_Y - 290, 660, 290)
    box(s, (70, 30, 40), hall)
    for x in range(hall.x + 20, hall.right, 110):                                         # columns
        box(s, (110, 60, 60), (x, hall.y + 20, 16, hall.height - 20), outline=False)
    small = pygame.font.SysFont(None, 13)
    count = len(WAX_FIGURES)
    for i in range(count):
        x = hall.x + 55 + i * 92
        pedestal = pygame.Rect(x - 34, GROUND_Y - 44, 68, 44)
        box(s, (120, 100, 90), pedestal)
        pygame.draw.rect(s, GOLD, (pedestal.x, pedestal.y - 4, pedestal.width, 6))
        plaque = pygame.Rect(x - 42, GROUND_Y - 30, 84, 14)
        pygame.draw.rect(s, CREAM, plaque)
        look = WAX_FIGURES[i]
        turn = 6 if math.sin(t * 0.9 + i * 2.3) > 0.93 else 0                            # a head turns...
        person(s, x, GROUND_Y - 44, look, t, turn=turn)
        label = small.render(look["name"], True, OUTLINE)
        s.blit(label, label.get_rect(center=plaque.center))
    for i in range(count - 1):                                                            # velvet ropes
        a = hall.x + 55 + i * 92 + 34
        pygame.draw.arc(s, (160, 20, 40), (a, GROUND_Y - 64, 24, 20), math.pi, 2 * math.pi, 4)
    marquee(s, "WAX MUSEUM  ·  DO NOT TOUCH", (cx, hall.y - 16), font, color=(240, 210, 170), back=(60, 20, 30), t=t)


def workshop(s, cx, ctx, font):
    """The maintenance workshop: animatronic parts everywhere, chains, turning gears, a blueprint of
    a bear, welding sparks and a flickering bulb."""
    t = ctx["t"]
    room = pygame.Rect(cx - 260, GROUND_Y - 270, 520, 270)
    box(s, (66, 60, 62), room)
    for x in range(room.x, room.right, 40):                                               # brick lines
        pygame.draw.line(s, (58, 52, 54), (x, room.y), (x, room.bottom), 2)
    if math.sin(t * 9) > -0.6:                                                            # flickering bulb
        pygame.draw.circle(s, (255, 230, 150), (cx, room.y + 40), 10)
    pygame.draw.line(s, OUTLINE, (cx, room.y), (cx, room.y + 30), 2)
    blueprint = pygame.Rect(room.x + 30, room.y + 40, 130, 90)                           # blueprint on the wall
    box(s, (40, 80, 140), blueprint)
    circle(s, (180, 210, 255), (blueprint.centerx, blueprint.centery - 8), 22, outline=False)
    circle(s, (40, 80, 140), (blueprint.centerx, blueprint.centery - 8), 20, outline=False)
    for dx in (-18, 18):
        circle(s, (180, 210, 255), (blueprint.centerx + dx, blueprint.y + 18), 8, outline=False)
    for i, (x, y, r) in enumerate(((room.right - 90, room.y + 80, 44), (room.right - 150, room.y + 50, 26),
                                   (room.right - 130, room.y + 130, 20))):               # turning gears
        angle = t * (1.2 if i % 2 == 0 else -1.8)
        for tooth in range(10):
            a = angle + tooth * math.pi / 5
            circle(s, METAL, (x + r * math.cos(a), y + r * math.sin(a)), r // 4, outline=False)
        circle(s, METAL, (x, y), r)
        circle(s, (66, 60, 62), (x, y), r // 3)
    for i in range(3):                                                                    # hanging chains
        x = room.x + 200 + i * 40
        for k in range(6):
            pygame.draw.ellipse(s, METAL, (x - 4 + int(3 * math.sin(t + i)), room.y + k * 14, 8, 14), 2)
    bench = pygame.Rect(room.x + 40, GROUND_Y - 90, 300, 16)                              # workbench with parts
    box(s, WOOD, bench)
    for x in (bench.x + 10, bench.right - 20):
        box(s, WOOD, (x, bench.bottom, 12, GROUND_Y - bench.bottom), outline=False)
    box(s, (150, 100, 60), (bench.x + 30, bench.y - 50, 60, 50), radius=12)               # bear head on the bench
    circle(s, (150, 100, 60), (bench.x + 36, bench.y - 50), 10)
    circle(s, (150, 100, 60), (bench.x + 84, bench.y - 50), 10)
    eye_on = math.sin(t * 4) > 0
    circle(s, (255, 60, 60) if eye_on else (90, 20, 20), (bench.x + 48, bench.y - 30), 5, outline=False)
    circle(s, (255, 60, 60) if eye_on else (90, 20, 20), (bench.x + 72, bench.y - 30), 5, outline=False)
    pygame.draw.line(s, METAL, (bench.x + 120, bench.y - 6), (bench.x + 170, bench.y - 30), 6)   # a loose arm
    circle(s, METAL, (bench.x + 170, bench.y - 30), 8)
    spark_x, spark_y = bench.x + 220, bench.y - 8                                          # welding sparks
    rng = random.Random(int(t * 12))
    for _ in range(10):
        a = rng.uniform(math.pi, 2 * math.pi)
        d = rng.uniform(5, 30)
        pygame.draw.line(s, (255, 230, 140), (spark_x, spark_y), (spark_x + d * math.cos(a), spark_y + d * math.sin(a)), 2)
    pygame.draw.circle(s, (255, 255, 230), (spark_x, spark_y), 5)
    marquee(s, "STAFF ONLY", (cx - 120, room.y - 14), font, color=(240, 220, 120), back=(50, 40, 20), t=t)


def draw_big_gate(c, cx, openness, font):
    """The park's exit: stone pillars with lamps, an iron arch with the park's name, two barred doors.
    openness 0 = closed, 1 = wide open (the doors turn inwards and look narrower)."""
    top = GROUND_Y - 290
    for side in (-1, 1):
        px = cx + side * 190
        box(c, (70, 80, 85), (px - 28, top + 20, 56, GROUND_Y - top - 20))
        box(c, (95, 105, 110), (px - 36, top + 10, 72, 18))
        circle(c, (255, 230, 160), (px, top), 10)
    pygame.draw.arc(c, (40, 45, 50), (cx - 165, top - 40, 330, 140), 0, math.pi, 12)
    sign = font.render("HOLLOWMERE PARK", True, (230, 220, 190))
    c.blit(sign, sign.get_rect(center=(cx, top - 4)))
    door_width = int(160 * (1 - 0.85 * openness))
    for side in (-1, 1):
        hinge = cx + side * 162
        left = hinge if side < 0 else hinge - door_width
        door = pygame.Rect(left, top + 40, door_width, GROUND_Y - top - 40)
        for i in range(0, max(door_width, 1), 14):
            pygame.draw.line(c, (30, 32, 38), (door.x + i, door.y), (door.x + i, door.bottom), 4)
        pygame.draw.line(c, (30, 32, 38), (door.x, door.y + 20), (door.right, door.y + 20), 5)
        pygame.draw.line(c, (30, 32, 38), (door.x, door.bottom - 30), (door.right, door.bottom - 30), 5)


def exit_gate(s, cx, ctx, font):
    """The finale: the big closed gate behind the fight with Walt."""
    draw_big_gate(s, cx, 0.0, font)
