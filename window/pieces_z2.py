"""Attraction scenes of zone 2, the Funhouse. Each function draws one attraction around screen
position cx; ctx["t"] (seconds) drives the animations. (The Laughing Lady stays in setpieces.py.)"""
import math

import pygame

from .pieces_kit import (CREAM, GOLD, GROUND_Y, METAL, OUTLINE, WOOD, awning, box, bulbs, circle, marquee, person,
                         poly, shade, stars_of_light)


def hall_of_mirrors(s, cx, ctx, font):
    """Ornate gold-framed mirrors of different shapes (tall, wavy, round) with warped live reflections.
    Only the player is reflected, never Walt (a silent clue; Walt explains it in the finale flashback)."""
    t = ctx["t"]
    hall = pygame.Rect(cx - 300, GROUND_Y - 280, 600, 280)
    box(s, (40, 46, 80), hall)
    for x in range(hall.x, hall.right, 30):                                               # wallpaper
        pygame.draw.line(s, (50, 58, 96), (x, hall.y), (x, hall.bottom), 6)
    marquee(s, "HALL OF MIRRORS", (cx, hall.y - 6), font, color=(170, 230, 255), back=(30, 40, 80), t=t)
    shapes = ["tall", "wavy", "round", "wavy", "tall"]
    for i, shape in enumerate(shapes):
        frame = pygame.Rect(hall.x + 22 + i * 116, GROUND_Y - 236, 96, 214)
        if shape == "round":
            frame = pygame.Rect(frame.x - 4, GROUND_Y - 220, 104, 150)
        glass = frame.inflate(-16, -16)
        pane = pygame.Surface(glass.size, pygame.SRCALPHA)
        pane.fill((70, 100, 135, 255))
        pygame.draw.rect(pane, (95, 130, 165, 255), (0, 0, glass.width, glass.height // 3))  # sky in the glass
        if shape == "wavy":                                                               # funhouse warp
            stretch = 1.0 + 0.4 * math.sin(t * 1.4 + i)
        elif shape == "round":
            stretch = 0.7
        else:
            stretch = 1.25
        reflected = [("player", ctx["player_x"])]                                       # Walt has no reflection
        middle = sum(x for _, x in reflected) / len(reflected)
        for name, x in reflected:
            image = ctx["sprites"][name][0]
            width = int(image.get_width() * (2.1 - stretch) * 0.7)
            warped = pygame.transform.scale(image, (max(8, width), int(image.get_height() * stretch * 0.7)))
            warped = pygame.transform.flip(warped, True, False)
            warped.set_alpha(225)
            # side by side like in reality, and the pair moves a little when you move
            mirror_x = int(glass.width // 2 + (x - middle) / 4 + (middle - 480) / 30)
            pane.blit(warped, (mirror_x - warped.get_width() // 2, glass.height - warped.get_height() - 4))
        pygame.draw.line(pane, (255, 255, 255, 80), (8, 26), (32, 2), 6)                 # shine
        pygame.draw.line(pane, (255, 255, 255, 50), (8, 48), (48, 8), 3)
        mask = pygame.Surface(glass.size, pygame.SRCALPHA)
        if shape == "round":
            pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
        else:
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=38)
        pane.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        if shape == "round":
            pygame.draw.ellipse(s, GOLD, frame)
            pygame.draw.ellipse(s, OUTLINE, frame, 2)
        else:
            pygame.draw.rect(s, GOLD, frame, border_radius=44)
            pygame.draw.rect(s, OUTLINE, frame, 2, border_radius=44)
        circle(s, shade(GOLD, 1.2), (frame.centerx, frame.y + 4), 10)                     # crest on top
        s.blit(pane, glass)
        stars_of_light(s, (glass.x + 20, glass.y + 30), 7, t + i)


def barrel_tunnel(s, cx, ctx, font):
    """Barrel of Laughs: a long striped barrel seen from the side, turning on rollers, with a giant
    laughing clown mouth as the entrance and a walkway through it."""
    t = ctx["t"]
    barrel = pygame.Rect(cx - 150, GROUND_Y - 205, 420, 150)            # right of centre: the face stays clear of Walt
    for x in (barrel.x + 40, barrel.right - 40):                                         # rollers and frame
        box(s, METAL, (x - 30, GROUND_Y - 56, 60, 56))
        circle(s, (60, 60, 70), (x - 14, GROUND_Y - 58), 12)
        circle(s, (60, 60, 70), (x + 14, GROUND_Y - 58), 12)
    body = pygame.Surface(barrel.size, pygame.SRCALPHA)                                   # turning stripes
    offset = (t * 90) % 60
    for i in range(-2, 12):
        y0 = int(i * 60 - offset)
        colour = (230, 60, 70) if i % 2 else (250, 225, 120)
        pygame.draw.polygon(body, colour, [(0, y0), (barrel.width, y0 + 40), (barrel.width, y0 + 70), (0, y0 + 30)])
    shading = pygame.Surface(barrel.size, pygame.SRCALPHA)                                # round look
    for y in range(barrel.height):
        edge = abs(y - barrel.height / 2) / (barrel.height / 2)
        pygame.draw.line(shading, (0, 0, 0, int(140 * edge ** 2)), (0, y), (barrel.width, y))
    body.blit(shading, (0, 0))
    mask = pygame.Surface(barrel.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=60)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(body, barrel)
    for x in range(barrel.x + 40, barrel.right - 30, 70):                                # metal hoops
        pygame.draw.line(s, METAL, (x, barrel.y + 6), (x, barrel.bottom - 6), 6)
    pygame.draw.rect(s, OUTLINE, barrel, 3, border_radius=60)
    face = (barrel.x - 30, barrel.centery)                                               # clown-mouth entrance
    circle(s, (245, 240, 235), face, 82)
    circle(s, (230, 50, 60), (face[0], face[1] - 10), 12)                                 # nose
    for dx in (-30, 30):
        circle(s, (60, 120, 220), (face[0] + dx, face[1] - 38), 10)
        pygame.draw.line(s, OUTLINE, (face[0] + dx - 12, face[1] - 52), (face[0] + dx + 12, face[1] - 56), 3)
    laugh = abs(math.sin(t * 4))
    mouth = pygame.Rect(face[0] - 46, face[1] + 2, 92, 34 + int(20 * laugh))
    pygame.draw.ellipse(s, (200, 30, 50), mouth)
    pygame.draw.ellipse(s, (40, 10, 20), mouth.inflate(-20, -16))
    for i in range(5):
        pygame.draw.rect(s, CREAM, (mouth.x + 18 + i * 12, mouth.y + 4, 10, 8))
    for side in (-1, 1):
        circle(s, (240, 120, 40), (face[0] + side * 70, face[1] - 50), 22, outline=False)  # orange hair tufts
    marquee(s, "BARREL OF LAUGHS", (cx + 40, barrel.y - 34), font, color=(255, 200, 120), back=(110, 30, 40), t=t)


def tilted_room(s, cx, ctx, font):
    """A crooked funhouse house (upright, with a bent chimney and wonky windows). Through its big
    window you see the tilted room: a sloping checkerboard floor, furniture sliding, a ball rolling."""
    t = ctx["t"]
    house = pygame.Rect(cx - 210, GROUND_Y - 250, 420, 250)
    box(s, (75, 55, 120), house)
    poly(s, (110, 60, 90), [(house.x - 20, house.y), (house.centerx - 40, house.y - 70),
                            (house.right + 20, house.y + 6)])                             # crooked roof
    box(s, (90, 60, 70), (house.right - 90, house.y - 80, 26, 70))                        # bent chimney
    pygame.draw.line(s, (90, 60, 70), (house.right - 77, house.y - 80), (house.right - 60, house.y - 100), 14)
    for i, (x, y, a) in enumerate(((house.x + 22, house.y + 26, 8), (house.right - 70, house.y + 18, -10))):
        win = pygame.Surface((46, 40), pygame.SRCALPHA)                                   # wonky little windows
        box(win, (255, 215, 120), (0, 0, 46, 40), radius=4)
        pygame.draw.line(win, OUTLINE, (23, 0), (23, 40), 3)
        win = pygame.transform.rotate(win, a)
        s.blit(win, (x, y))
    window = pygame.Rect(house.x + 70, house.y + 70, 280, 150)
    room = pygame.Surface((window.width + 80, window.height + 80), pygame.SRCALPHA)       # the tilted room
    room.fill((205, 175, 235, 255))
    for x in range(0, room.get_width(), 26):
        pygame.draw.line(room, (185, 155, 215), (x, 0), (x, room.get_height()), 5)
    floor_y = room.get_height() - 70
    for i in range(16):
        for row in range(3):
            colour = (30, 30, 40) if (i + row) % 2 else (240, 235, 225)
            pygame.draw.rect(room, colour, (i * 26, floor_y + row * 14, 26, 14))
    for i, x in enumerate((50, 170, 290)):
        pygame.draw.rect(room, GOLD, (x, 40 + (i % 2) * 6, 46, 36), 4)
        pygame.draw.circle(room, (230, 210, 180), (x + 23, 58 + (i % 2) * 6), 10)
    slide = int(40 * math.sin(t * 0.7))
    box(room, WOOD, (90 + slide, floor_y - 34, 90, 34), radius=4)
    box(room, (190, 60, 70), (250 + slide // 2, floor_y - 52, 44, 52), radius=6)
    ball_x = 60 + int((math.sin(t * 1.3) + 1) * 150)
    pygame.draw.circle(room, (230, 60, 60), (ball_x, floor_y - 10), 10)
    room = pygame.transform.rotate(room, 15 + 3 * math.sin(t * 0.6))
    clip = pygame.Surface(window.size, pygame.SRCALPHA)
    clip.blit(room, room.get_rect(center=(window.width // 2, window.height // 2)))
    s.blit(clip, window)
    pygame.draw.rect(s, GOLD, window, 6)                                                  # window frame
    pygame.draw.rect(s, OUTLINE, window.inflate(6, 6), 2)
    box(s, (120, 70, 50), (house.x + 20, GROUND_Y - 90, 40, 90), radius=4)               # door
    marquee(s, "THE TILTED ROOM", (cx - 150, house.y - 40), font, color=(220, 190, 255), back=(60, 30, 90), t=t)


def clown_alley(s, cx, ctx, font):
    """An alley under a giant clown-head archway, with bunting, clown posters and balloons."""
    t = ctx["t"]
    for side in (-1, 1):                                                                  # side walls with posters
        wall = pygame.Rect(cx + (side * 160 if side > 0 else -280), GROUND_Y - 200, 120, 200)
        box(s, (60, 70, 110), wall)
        poster = wall.inflate(-30, -80).move(0, -20)
        box(s, CREAM, poster)
        circle(s, (240, 240, 240), (poster.centerx, poster.centery - 4), 24)
        circle(s, (230, 40, 40), (poster.centerx, poster.centery), 7)
        pygame.draw.arc(s, (230, 40, 40), (poster.centerx - 16, poster.centery, 32, 18), math.pi, 2 * math.pi, 3)
    head = (cx, GROUND_Y - 200)                                                            # giant clown head arch
    circle(s, (245, 240, 235), head, 110)
    for dx in (-90, 90):
        circle(s, (60, 180, 220), (head[0] + dx, head[1] - 40), 40, outline=False)        # blue hair
    circle(s, (230, 50, 60), (head[0], head[1] - 10), 18)
    blink = (t % 4) < 0.15
    for dx in (-42, 42):
        if blink:
            pygame.draw.line(s, OUTLINE, (head[0] + dx - 14, head[1] - 46), (head[0] + dx + 14, head[1] - 46), 4)
        else:
            circle(s, CREAM, (head[0] + dx, head[1] - 46), 16)
            look = int(6 * math.sin(t))
            circle(s, OUTLINE, (head[0] + dx + look, head[1] - 46), 6, outline=False)
    mouth = pygame.Rect(cx - 70, GROUND_Y - 160, 140, 160)                                # walk in through the mouth
    pygame.draw.rect(s, (200, 30, 50), mouth, border_top_left_radius=70, border_top_right_radius=70)
    pygame.draw.rect(s, (25, 10, 20), mouth.inflate(-22, -14).move(0, 7), border_top_left_radius=60,
                     border_top_right_radius=60)
    for i in range(6):
        pygame.draw.rect(s, CREAM, (mouth.x + 16 + i * 19, mouth.y + 10, 15, 14))
    for i in range(9):                                                                    # bunting
        x = cx - 280 + i * 70
        poly(s, ((230, 60, 60), (250, 210, 70), (70, 160, 220))[i % 3],
             [(x, GROUND_Y - 300), (x + 60, GROUND_Y - 300 + (i % 2) * 6), (x + 30, GROUND_Y - 270)], outline=False)
    for i in range(4):                                                                    # balloons drifting
        x = cx - 230 + i * 150 + int(8 * math.sin(t + i))
        y = GROUND_Y - 120 + int(10 * math.sin(t * 1.6 + i))
        pygame.draw.line(s, CREAM, (x, y + 18), (x + 4, GROUND_Y - 10), 1)
        pygame.draw.ellipse(s, ((220, 60, 60), (60, 160, 220), (240, 200, 60), (120, 200, 90))[i], (x - 15, y - 20, 30, 38))
        pygame.draw.ellipse(s, OUTLINE, (x - 15, y - 20, 30, 38), 2)
    marquee(s, "CLOWN ALLEY", (cx, GROUND_Y - 330), font, color=(255, 220, 120), back=(120, 30, 50), t=t)


def puppet_theater(s, cx, ctx, font):
    """A grand puppet theater: carved gold frame, velvet curtains with tassels, a painted moonlit
    backdrop, footlights, and three marionettes whose strings run up to wooden cross-bars held by
    pale hands from above."""
    t = ctx["t"]
    frame = pygame.Rect(cx - 210, GROUND_Y - 300, 420, 300)
    box(s, (90, 25, 35), frame, radius=8)
    stage = pygame.Rect(cx - 165, GROUND_Y - 225, 330, 175)
    pygame.draw.rect(s, (30, 30, 70), stage)                                              # painted backdrop: night sky
    pygame.draw.circle(s, (240, 235, 200), (stage.right - 50, stage.y + 40), 22)
    for i in range(5):                                                                    # painted hills and trees
        pygame.draw.circle(s, (30, 60, 50), (stage.x + i * 80, stage.bottom + 10), 60)
        poly(s, (20, 45, 40), [(stage.x + 30 + i * 70, stage.bottom - 30), (stage.x + 45 + i * 70, stage.bottom - 90),
                               (stage.x + 60 + i * 70, stage.bottom - 30)], outline=False)
    for x in range(stage.x, stage.right, 24):                                            # footlights
        pygame.draw.circle(s, (255, 220, 140), (x + 12, stage.bottom - 4), 4)
    hands_y = stage.y + 12
    for i in range(3):                                                                    # marionettes
        x = stage.x + 70 + i * 95
        sway = int(14 * math.sin(t * 1.8 + i * 1.4))
        step = int(10 * math.sin(t * 3.6 + i))
        bar_x = x + sway
        pygame.draw.line(s, WOOD, (bar_x - 26, hands_y), (bar_x + 26, hands_y), 5)        # cross-bar
        pygame.draw.line(s, WOOD, (bar_x, hands_y - 10), (bar_x, hands_y + 10), 5)
        circle(s, (235, 225, 215), (bar_x, hands_y - 16), 9)                              # the hand holding it
        pygame.draw.line(s, (235, 225, 215), (bar_x, hands_y - 24), (bar_x, stage.y - 20), 6)
        body_x, head_y = x + sway // 2, stage.y + 78
        for sx, sy in ((bar_x - 24, body_x - 14), (bar_x + 24, body_x + 14), (bar_x, body_x)):
            pygame.draw.line(s, (200, 200, 200), (sx, hands_y), (sy, head_y), 1)          # strings
        colours = ((60, 90, 160), (170, 50, 60), (70, 140, 80))[i]
        circle(s, (232, 205, 175), (body_x, head_y), 11)
        pygame.draw.circle(s, OUTLINE, (body_x - 4, head_y - 2), 2)
        pygame.draw.circle(s, OUTLINE, (body_x + 4, head_y - 2), 2)
        box(s, colours, (body_x - 10, head_y + 10, 20, 30), radius=4, outline=False)
        pygame.draw.line(s, (232, 205, 175), (body_x - 10, head_y + 14), (body_x - 20, head_y + 30 + step), 3)
        pygame.draw.line(s, (232, 205, 175), (body_x + 10, head_y + 14), (body_x + 20, head_y + 30 - step), 3)
        pygame.draw.line(s, shade(colours, 0.6), (body_x - 5, head_y + 40), (body_x - 7, head_y + 58 + step), 4)
        pygame.draw.line(s, shade(colours, 0.6), (body_x + 5, head_y + 40), (body_x + 7, head_y + 58 - step), 4)
    for side in (-1, 1):                                                                  # velvet curtains with tassels
        for i in range(4):
            x = cx + side * (178 - i * 12)
            pygame.draw.rect(s, (150 - i * 12, 20, 40), (x - 8, stage.y - 10, 16, stage.height + 20))
        pygame.draw.circle(s, GOLD, (cx + side * 150, stage.y + 90), 7)
    awning(s, stage.x - 20, stage.y - 22, stage.width + 40, [(150, 25, 45), (120, 15, 35)], depth=26)
    pygame.draw.rect(s, GOLD, frame, 6, border_radius=8)                                  # carved gold frame
    for x in range(frame.x + 20, frame.right, 40):
        circle(s, shade(GOLD, 1.15), (x, frame.y + 6), 6, outline=False)
    box(s, WOOD, (cx - 200, GROUND_Y - 50, 400, 50))                                      # stage front
    marquee(s, "PUPPET THEATER", (cx, frame.y - 16), font, color=(255, 220, 160), back=(80, 20, 30), t=t)
