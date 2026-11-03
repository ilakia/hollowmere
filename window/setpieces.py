"""
Scene pieces: every attraction gets its own set dressing (photo strips at the Photo Booth, wax
figures in the Wax Museum, mirrors with live reflections in the Hall of Mirrors...).

A piece is drawn around a centre x on the ground line, behind the characters. While the player walks
up, the piece slides in from the right; during the fight it stays behind the ghosts.
ctx = {"t": time in seconds, "sprites": sprite images, "player_x", "walt_x", "show_walt", "mood"}.
"""
import math

import pygame

GROUND_Y = 385
DARK = (20, 16, 26)
WOOD = (92, 60, 40)
METAL = (110, 110, 125)
CREAM = (235, 225, 200)


def label(surface, text, cx, y, color, font):
    """A small lit sign on the piece."""
    image = font.render(text, True, color)
    board = image.get_rect(center=(cx, y)).inflate(16, 8)
    pygame.draw.rect(surface, DARK, board, border_radius=5)
    pygame.draw.rect(surface, color, board, width=2, border_radius=5)
    surface.blit(image, image.get_rect(center=(cx, y)))


# ---------------------------------------------------------------- zone 1: Entrance & Midway
def ticket_booth(s, cx, ctx, font):
    pygame.draw.rect(s, (120, 40, 50), (cx - 70, GROUND_Y - 170, 140, 170))
    pygame.draw.polygon(s, (170, 60, 70), [(cx - 85, GROUND_Y - 170), (cx, GROUND_Y - 220), (cx + 85, GROUND_Y - 170)])
    pygame.draw.rect(s, (40, 60, 80), (cx - 45, GROUND_Y - 140, 90, 60))                 # window
    pygame.draw.line(s, METAL, (cx - 45, GROUND_Y - 110), (cx + 45, GROUND_Y - 110), 2)
    for i in range(5):                                                                    # ticket roll
        pygame.draw.rect(s, (240, 200, 90), (cx + 50 + i * 3, GROUND_Y - 70 + i * 10, 22, 8))
    label(s, "TICKETS 25c", cx, GROUND_Y - 195, (255, 210, 120), font)
    for side in (-1, 1):                                                                  # turnstiles
        x = cx + side * 130
        pygame.draw.rect(s, METAL, (x - 4, GROUND_Y - 60, 8, 60))
        angle = ctx["t"] * 2 * side
        for arm in range(3):
            a = angle + arm * 2.09
            pygame.draw.line(s, METAL, (x, GROUND_Y - 50), (x + 24 * math.cos(a), GROUND_Y - 50 + 8 * math.sin(a)), 4)


def carousel(s, cx, ctx, font):
    pygame.draw.polygon(s, (190, 60, 90), [(cx - 200, GROUND_Y - 200), (cx, GROUND_Y - 260), (cx + 200, GROUND_Y - 200)])
    for i in range(10):                                                                   # scalloped canopy
        color = (240, 220, 160) if i % 2 else (190, 60, 90)
        pygame.draw.circle(s, color, (cx - 180 + i * 40, GROUND_Y - 198), 20, draw_top_left=False,
                           draw_top_right=False, draw_bottom_left=True, draw_bottom_right=True)
    pygame.draw.rect(s, (60, 40, 50), (cx - 190, GROUND_Y - 12, 380, 12))                # platform
    for i in range(5):                                                                    # horses go up and down
        x = cx - 160 + i * 80
        bob = int(18 * math.sin(ctx["t"] * 2 + i))
        pygame.draw.line(s, (220, 200, 120), (x, GROUND_Y - 198), (x, GROUND_Y - 12), 3)
        body = pygame.Rect(x - 26, GROUND_Y - 110 + bob, 52, 26)
        pygame.draw.ellipse(s, CREAM, body)
        pygame.draw.polygon(s, CREAM, [(x + 20, body.y + 4), (x + 34, body.y - 22), (x + 40, body.y - 14), (x + 30, body.y + 10)])
        for leg in (-16, 14):
            pygame.draw.line(s, CREAM, (x + leg, body.bottom - 4), (x + leg + 4, body.bottom + 18), 4)
        pygame.draw.rect(s, (190, 60, 90), (x - 10, body.y - 4, 18, 6))                  # saddle


def cotton_candy(s, cx, ctx, font):
    pygame.draw.rect(s, (230, 120, 170), (cx - 90, GROUND_Y - 120, 180, 120))
    pygame.draw.rect(s, (255, 255, 255), (cx - 100, GROUND_Y - 150, 200, 30))
    for i in range(0, 200, 25):
        pygame.draw.rect(s, (255, 150, 200), (cx - 100 + i, GROUND_Y - 150, 12, 30))
    for i in range(4):                                                                    # cotton candy clouds
        x = cx - 60 + i * 40
        pygame.draw.line(s, CREAM, (x, GROUND_Y - 120), (x, GROUND_Y - 160), 3)
        for dx, dy in ((0, -175), (-10, -168), (10, -168), (0, -162)):
            pygame.draw.circle(s, (255, 180, 220) if i % 2 else (180, 220, 255), (x + dx, GROUND_Y + dy), 12)
    pygame.draw.circle(s, (240, 230, 220), (cx + 140, GROUND_Y - 130), 26)               # mascot head on a pole
    pygame.draw.circle(s, DARK, (cx + 132, GROUND_Y - 134), 4)
    pygame.draw.circle(s, DARK, (cx + 148, GROUND_Y - 134), 4)
    pygame.draw.arc(s, (200, 40, 40), (cx + 124, GROUND_Y - 128, 32, 18), math.pi, 2 * math.pi, 3)
    pygame.draw.line(s, METAL, (cx + 140, GROUND_Y - 104), (cx + 140, GROUND_Y), 4)
    label(s, "COTTON CANDY", cx, GROUND_Y - 185, (255, 180, 220), font)


def photo_booth(s, cx, ctx, font):
    booth = pygame.Rect(cx - 70, GROUND_Y - 210, 140, 210)
    pygame.draw.rect(s, (60, 50, 90), booth, border_radius=6)
    pygame.draw.rect(s, (150, 30, 40), (cx - 50, GROUND_Y - 160, 100, 160))              # curtain
    for i in range(5):
        pygame.draw.line(s, (110, 20, 30), (cx - 40 + i * 20, GROUND_Y - 160), (cx - 40 + i * 20, GROUND_Y), 2)
    label(s, "PHOTOS 4 FOR 10c", cx, GROUND_Y - 185, (255, 230, 150), font)
    if (ctx["t"] % 3) < 0.15:                                                             # the flash goes off
        pygame.draw.rect(s, (255, 255, 230), (cx - 50, GROUND_Y - 160, 100, 160))
    for strip in range(5):                                                                # photo strips on a line
        x = cx + 110 + strip * 34
        y = GROUND_Y - 200 + (strip % 2) * 18
        pygame.draw.line(s, METAL, (x - 17, y - 6), (x + 17, y - 6), 1)
        pygame.draw.rect(s, CREAM, (x - 12, y, 24, 84))
        for frame in range(4):
            pygame.draw.rect(s, (70, 60, 60), (x - 9, y + 4 + frame * 20, 18, 16))
            pygame.draw.circle(s, (200, 190, 170), (x, y + 11 + frame * 20), 4)             # a face in every photo
    for strip in range(3):                                                                # and some on the left
        x = cx - 120 - strip * 34
        pygame.draw.rect(s, CREAM, (x - 12, GROUND_Y - 190, 24, 84))
        for frame in range(4):
            pygame.draw.rect(s, (70, 60, 60), (x - 9, GROUND_Y - 186 + frame * 20, 18, 16))


def ring_toss(s, cx, ctx, font):
    pygame.draw.rect(s, WOOD, (cx - 180, GROUND_Y - 70, 360, 70))
    pygame.draw.rect(s, (200, 60, 60), (cx - 190, GROUND_Y - 230, 380, 24))
    for row in range(4):                                                                  # bottle pyramid
        for i in range(4 - row):
            x = cx - 60 + i * 40 + row * 20
            y = GROUND_Y - 100 - row * 34
            pygame.draw.rect(s, (60, 140, 90), (x - 8, y, 16, 30), border_radius=4)
            pygame.draw.rect(s, (60, 140, 90), (x - 3, y - 10, 6, 12))
    for i in range(3):                                                                    # rings in the air
        x = cx - 150 + i * 30 + int(10 * math.sin(ctx["t"] + i))
        pygame.draw.ellipse(s, (255, 210, 80), (x, GROUND_Y - 150 - i * 10, 26, 12), 3)
    for i in range(3):                                                                    # prize bears with teeth
        x = cx + 120 + i * 30
        pygame.draw.circle(s, (150, 100, 60), (x, GROUND_Y - 180), 13)
        pygame.draw.rect(s, (240, 240, 230), (x - 6, GROUND_Y - 176, 12, 4))
    label(s, "RING TOSS", cx, GROUND_Y - 218, (255, 230, 150), font)


def ferris_base(s, cx, ctx, font):
    """A real turning ferris wheel: rim with blinking bulbs, spokes, gondolas that hang straight down."""
    hub = (cx, GROUND_Y - 150)
    radius = 130
    for side in (-1, 1):                                                                  # A-frame legs
        pygame.draw.line(s, METAL, hub, (cx + side * 95, GROUND_Y), 8)
    pygame.draw.line(s, METAL, (cx - 60, GROUND_Y - 60), (cx + 60, GROUND_Y - 60), 5)
    turn = ctx["t"] * 0.25                                                                # slow rotation
    pygame.draw.circle(s, (170, 60, 90), hub, radius, 5)
    pygame.draw.circle(s, (170, 60, 90), hub, radius - 18, 2)
    for spoke in range(16):
        a = turn + spoke * math.pi / 8
        rim = (hub[0] + radius * math.cos(a), hub[1] + radius * math.sin(a))
        pygame.draw.line(s, (150, 150, 165), hub, rim, 2)
        lit = (spoke + int(ctx["t"] * 4)) % 3 == 0                                       # chasing lights
        pygame.draw.circle(s, (255, 230, 140) if lit else (120, 90, 60), (int(rim[0]), int(rim[1])), 4)
    for car in range(8):                                                                  # gondolas
        a = turn + car * math.pi / 4
        x = hub[0] + radius * math.cos(a)
        y = hub[1] + radius * math.sin(a)
        pygame.draw.line(s, METAL, (x, y), (x, y + 12), 2)
        color = ((220, 70, 90), (70, 150, 220), (240, 200, 70), (110, 200, 120))[car % 4]
        pygame.draw.rect(s, color, (x - 15, y + 12, 30, 20), border_radius=6)
        pygame.draw.rect(s, (40, 30, 50), (x - 10, y + 15, 20, 7))
    pygame.draw.circle(s, METAL, hub, 14)
    pygame.draw.circle(s, (255, 220, 120), hub, 6)
    pygame.draw.rect(s, (60, 50, 60), (cx - 150, GROUND_Y - 22, 300, 22))              # loading platform
    label(s, "THE BIG WHEEL", cx + 185, GROUND_Y - 60, (255, 210, 120), font)


# ---------------------------------------------------------------- zone 2: The Funhouse
def hall_of_mirrors(s, cx, ctx, font):
    """Mirror panels with live, warped reflections of the player. Walt has NO reflection: the story
    says "A hundred of you. No Walt in any mirror." (a first hint that he is a ghost)."""
    for i in range(5):
        frame = pygame.Rect(cx - 280 + i * 115, GROUND_Y - 230, 95, 220)
        pygame.draw.rect(s, (200, 170, 90), frame, border_radius=40)                     # gold frame
        glass = frame.inflate(-14, -14)
        pane = pygame.Surface(glass.size, pygame.SRCALPHA)
        pygame.draw.rect(pane, (70, 100, 130, 255), pane.get_rect(), border_radius=34)     # dark glass: reflections show
        for name, x in (("player", ctx["player_x"]),):
            image = ctx["sprites"][name][0]
            stretch = 1.0 + 0.35 * math.sin(ctx["t"] * 1.3 + i * 1.7)                   # funhouse warp
            warped = pygame.transform.scale(image, (int(image.get_width() * (2 - stretch)), int(image.get_height() * stretch * 0.8)))
            warped = pygame.transform.flip(warped, True, False)
            mirror_x = glass.width // 2 + (x - 480) // 8                                 # moves when you move
            warped.set_alpha(220)
            pane.blit(warped, (mirror_x - warped.get_width() // 2, glass.height - warped.get_height() - 6))
        shine = pygame.Surface(glass.size, pygame.SRCALPHA)
        pygame.draw.line(shine, (255, 255, 255, 70), (10, 30), (40, 0), 6)
        pane.blit(shine, (0, 0))
        mask = pygame.Surface(glass.size, pygame.SRCALPHA)                               # keep the rounded shape
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=34)
        pane.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(pane, glass)


def barrel_tunnel(s, cx, ctx, font):
    rect = pygame.Rect(cx - 200, GROUND_Y - 200, 400, 200)
    pygame.draw.ellipse(s, (60, 30, 30), rect.inflate(30, 30))
    spin = ctx["t"] * 2.5
    for i in range(12):                                                                   # rotating stripes
        a = spin + i * math.pi / 6
        end = (rect.centerx + 220 * math.cos(a), rect.centery + 110 * math.sin(a))
        pygame.draw.line(s, (220, 60, 60) if i % 2 else (240, 220, 200), rect.center, end, 18)
    pygame.draw.ellipse(s, (20, 10, 20), rect.inflate(-160, -80))
    label(s, "BARREL OF LAUGHS", cx, GROUND_Y - 230, (255, 120, 120), font)


def tilted_room(s, cx, ctx, font):
    room = pygame.Surface((420, 240), pygame.SRCALPHA)
    room.fill((90, 70, 120, 255))
    for x in range(0, 420, 30):
        pygame.draw.line(room, (110, 90, 140), (x, 0), (x, 240), 2)                     # wallpaper stripes
    for i, (x, y) in enumerate(((40, 40), (180, 30), (300, 60))):                         # crooked frames
        pygame.draw.rect(room, (200, 170, 90), (x, y, 70, 54), 5)
        pygame.draw.circle(room, (230, 210, 180), (x + 35, y + 26), 12)
    pygame.draw.rect(room, WOOD, (40, 170, 120, 70))                                      # table and chair
    pygame.draw.rect(room, WOOD, (250, 150, 40, 90))
    tilted = pygame.transform.rotate(room, 12 + 2 * math.sin(ctx["t"] * 0.7))
    s.blit(tilted, tilted.get_rect(midbottom=(cx, GROUND_Y + 30)))


def laughing_stage(s, cx, ctx, font):
    """Laughing Lady: a giant animatronic lady bust on a stage. Curly red hair, lipstick, pearls,
    earrings, a polka-dot dress; she rocks from side to side and her mouth and eyes laugh."""
    pygame.draw.rect(s, WOOD, (cx - 220, GROUND_Y - 40, 440, 40))
    for side in (-1, 1):                                                                  # red curtains
        for i in range(5):
            x = cx + side * (200 - i * 16)
            pygame.draw.rect(s, (150 - i * 10, 20, 40), (x - 9, GROUND_Y - 290, 18, 250))
    pygame.draw.rect(s, (120, 20, 40), (cx - 220, GROUND_Y - 300, 440, 30))
    beam = pygame.Surface((320, 300), pygame.SRCALPHA)                                    # spotlight
    pygame.draw.polygon(beam, (255, 240, 180, 35), [(160, 0), (40, 300), (280, 300)])
    s.blit(beam, (cx - 160, GROUND_Y - 300))
    laugh = abs(math.sin(ctx["t"] * 7))                                                   # 0 = closed, 1 = open
    rock = int(10 * math.sin(ctx["t"] * 3))                                               # she rocks side to side
    hx, hy = cx + rock, GROUND_Y - 175
    skin, lips, hair = (245, 210, 190), (200, 30, 60), (190, 70, 40)
    # dress and shoulders
    pygame.draw.polygon(s, (200, 40, 70), [(cx - 95, GROUND_Y - 40), (cx - 70, GROUND_Y - 120),
                                           (cx + 70, GROUND_Y - 120), (cx + 95, GROUND_Y - 40)])
    for dot_x, dot_y in ((-50, -70), (0, -90), (45, -65), (-20, -55), (30, -100), (-60, -100)):
        pygame.draw.circle(s, (255, 230, 235), (cx + dot_x, GROUND_Y + dot_y), 6)
    for side in (-1, 1):                                                                  # arms holding her belly
        pygame.draw.line(s, skin, (cx + side * 70, GROUND_Y - 112), (cx + side * 95, GROUND_Y - 70), 14)
        pygame.draw.line(s, skin, (cx + side * 95, GROUND_Y - 70), (cx + side * 30, GROUND_Y - 62), 12)
    pygame.draw.rect(s, skin, (hx - 14, hy + 40, 28, 26))                                 # neck
    for i in range(7):                                                                    # pearl necklace
        pygame.draw.circle(s, (250, 250, 240), (hx - 30 + i * 10, hy + 66 + abs(i - 3) * -2 + 6), 5)
    # big curly hair behind the face
    for dx, dy, r in ((-48, -10, 26), (48, -10, 26), (-38, -40, 28), (38, -40, 28), (0, -55, 32),
                      (-55, 20, 22), (55, 20, 22)):
        pygame.draw.circle(s, hair, (hx + dx, hy + dy), r)
    pygame.draw.ellipse(s, skin, (hx - 44, hy - 50, 88, 104))                             # face
    for side in (-1, 1):
        pygame.draw.circle(s, (255, 200, 60), (hx + side * 46, hy + 18), 7)               # gold earrings
        pygame.draw.circle(s, (240, 150, 150), (hx + side * 24, hy + 14), 9)              # rosy cheeks
        ex = hx + side * 18
        pygame.draw.arc(s, (40, 25, 30), (ex - 11, hy - 16, 22, 16), 0, math.pi, 3)      # laughing, squeezed eyes
        for lash in range(3):
            pygame.draw.line(s, (40, 25, 30), (ex - 8 + lash * 8, hy - 14), (ex - 10 + lash * 10, hy - 22), 2)
        pygame.draw.arc(s, hair, (ex - 13, hy - 32, 26, 12), 0, math.pi, 3)              # eyebrows
    mouth_h = 10 + int(28 * laugh)
    pygame.draw.ellipse(s, lips, (hx - 24, hy + 22, 48, mouth_h))                        # lipstick mouth
    pygame.draw.ellipse(s, (90, 10, 30), (hx - 17, hy + 27, 34, max(4, mouth_h - 12)))
    pygame.draw.rect(s, (255, 255, 250), (hx - 15, hy + 26, 30, 6))                      # teeth
    if laugh > 0.6:                                                                       # "HA HA" floats up
        for i, word in enumerate(("HA!", "HA!")):
            image = font.render(word, True, (255, 230, 120))
            rise = int((ctx["t"] * 40 + i * 30) % 60)
            s.blit(image, (hx + 60 + i * 30, hy - 40 - rise))
    label(s, "LAUGHING LADY", cx, GROUND_Y - 312, (255, 200, 200), font)


def clown_alley(s, cx, ctx, font):
    for i in range(4):                                                                    # clown posters
        x = cx - 210 + i * 140
        pygame.draw.rect(s, CREAM, (x, GROUND_Y - 230, 90, 120))
        pygame.draw.circle(s, (240, 240, 240), (x + 45, GROUND_Y - 180), 28)
        pygame.draw.circle(s, (230, 40, 40), (x + 45, GROUND_Y - 176), 8)
        pygame.draw.circle(s, (60, 120, 220), (x + 33, GROUND_Y - 190), 5)
        pygame.draw.circle(s, (60, 120, 220), (x + 57, GROUND_Y - 190), 5)
        pygame.draw.arc(s, (230, 40, 40), (x + 25, GROUND_Y - 176, 40, 22), math.pi, 2 * math.pi, 4)
    for i in range(5):                                                                    # balloons drifting
        x = cx - 160 + i * 80
        y = GROUND_Y - 110 + int(10 * math.sin(ctx["t"] * 1.5 + i))
        pygame.draw.line(s, CREAM, (x, y + 18), (x + 4, GROUND_Y - 30), 1)
        pygame.draw.ellipse(s, ((220, 60, 60), (60, 160, 220), (240, 200, 60), (120, 200, 90), (200, 90, 200))[i], (x - 14, y - 18, 28, 36))


def puppet_theater(s, cx, ctx, font):
    pygame.draw.rect(s, (110, 40, 40), (cx - 170, GROUND_Y - 250, 340, 250))
    pygame.draw.rect(s, (30, 20, 30), (cx - 130, GROUND_Y - 210, 260, 140))             # the stage opening
    pygame.draw.rect(s, (200, 170, 90), (cx - 170, GROUND_Y - 250, 340, 22))
    for i in range(3):                                                                    # dangling puppets
        x = cx - 80 + i * 80
        sway = int(10 * math.sin(ctx["t"] * 2 + i * 1.3))
        for dx in (-10, 10):
            pygame.draw.line(s, CREAM, (x + dx, GROUND_Y - 228), (x + dx + sway, GROUND_Y - 150), 1)
        pygame.draw.circle(s, (230, 200, 170), (x + sway, GROUND_Y - 150), 12)
        pygame.draw.rect(s, ((60, 90, 160), (160, 60, 60), (70, 140, 80))[i], (x + sway - 10, GROUND_Y - 138, 20, 30))
        pygame.draw.line(s, (230, 200, 170), (x + sway - 6, GROUND_Y - 108), (x + sway - 10, GROUND_Y - 90), 3)
        pygame.draw.line(s, (230, 200, 170), (x + sway + 6, GROUND_Y - 108), (x + sway + 10, GROUND_Y - 90), 3)
    label(s, "PUPPET THEATER", cx, GROUND_Y - 262, (255, 220, 160), font)


# ---------------------------------------------------------------- zone 3: The Dark Rides
def ghost_train(s, cx, ctx, font):
    for x in range(cx - 300, cx + 300, 24):                                               # track
        pygame.draw.rect(s, WOOD, (x, GROUND_Y - 12, 14, 12))
    pygame.draw.line(s, METAL, (cx - 300, GROUND_Y - 12), (cx + 300, GROUND_Y - 12), 3)
    pygame.draw.polygon(s, (40, 30, 40), [(cx + 60, GROUND_Y), (cx + 60, GROUND_Y - 230), (cx + 160, GROUND_Y - 280),
                                         (cx + 260, GROUND_Y - 230), (cx + 260, GROUND_Y)])
    pygame.draw.rect(s, (10, 5, 10), (cx + 110, GROUND_Y - 150, 100, 150))               # dark tunnel mouth
    drive = int(20 * math.sin(ctx["t"] * 0.8))
    for i in range(2):                                                                    # empty carts
        x = cx - 220 + i * 110 + drive
        pygame.draw.rect(s, (130, 30, 40), (x, GROUND_Y - 70, 90, 50), border_radius=8)
        pygame.draw.circle(s, METAL, (x + 20, GROUND_Y - 16), 10)
        pygame.draw.circle(s, METAL, (x + 70, GROUND_Y - 16), 10)
    label(s, "GHOST TRAIN", cx + 160, GROUND_Y - 250, (255, 90, 70), font)


def tunnel_boats(s, cx, ctx, font):
    pygame.draw.rect(s, (30, 50, 70), (cx - 300, GROUND_Y - 30, 600, 30))               # water channel
    for i in range(12):
        x = cx - 290 + i * 50 + int(10 * math.sin(ctx["t"] * 2 + i))
        pygame.draw.arc(s, (90, 140, 180), (x, GROUND_Y - 26, 30, 12), 0, math.pi, 2)
    pygame.draw.arc(s, (70, 50, 60), (cx - 160, GROUND_Y - 300, 320, 560), 0, math.pi, 30)   # tunnel arch
    float_y = int(4 * math.sin(ctx["t"] * 2))
    pygame.draw.polygon(s, (180, 120, 60), [(cx - 90, GROUND_Y - 40 + float_y), (cx + 90, GROUND_Y - 40 + float_y),
                                           (cx + 70, GROUND_Y - 10 + float_y), (cx - 70, GROUND_Y - 10 + float_y)])
    pygame.draw.polygon(s, (230, 220, 200), [(cx + 80, GROUND_Y - 40 + float_y), (cx + 110, GROUND_Y - 80 + float_y),
                                            (cx + 95, GROUND_Y - 40 + float_y)])      # swan neck at the front


def haunted_manor(s, cx, ctx, font):
    pygame.draw.polygon(s, (50, 40, 60), [(cx - 200, GROUND_Y), (cx - 200, GROUND_Y - 200), (cx - 100, GROUND_Y - 270),
                                         (cx, GROUND_Y - 200), (cx + 100, GROUND_Y - 270), (cx + 200, GROUND_Y - 200),
                                         (cx + 200, GROUND_Y)])
    for i, x in enumerate((cx - 150, cx - 70, cx + 50, cx + 130)):                        # flickering windows
        lit = math.sin(ctx["t"] * 3 + i * 2) > -0.3
        pygame.draw.rect(s, (255, 200, 100) if lit else (40, 30, 40), (x, GROUND_Y - 170, 30, 44))
        pygame.draw.line(s, DARK, (x + 15, GROUND_Y - 170), (x + 15, GROUND_Y - 126), 2)
    pygame.draw.rect(s, (30, 20, 30), (cx - 30, GROUND_Y - 90, 60, 90), border_top_left_radius=30,
                     border_top_right_radius=30)
    for i in range(3):                                                                    # bats
        x = cx - 120 + i * 120 + int(30 * math.sin(ctx["t"] + i))
        y = 150 + int(10 * math.sin(ctx["t"] * 3 + i))
        pygame.draw.polygon(s, DARK, [(x - 14, y - 4), (x, y + 4), (x + 14, y - 4), (x, y - 1)])


def log_flume(s, cx, ctx, font):
    pygame.draw.polygon(s, WOOD, [(cx - 260, GROUND_Y - 200), (cx - 220, GROUND_Y - 200), (cx + 120, GROUND_Y - 20),
                                  (cx + 80, GROUND_Y - 20)])                              # the chute
    for x in range(cx - 250, cx + 110, 40):                                               # supports
        y = int(GROUND_Y - 200 + (x - (cx - 250)) * 180 / 360)
        pygame.draw.line(s, (70, 45, 30), (x, y), (x, GROUND_Y), 4)
    pygame.draw.rect(s, (40, 80, 120), (cx + 60, GROUND_Y - 24, 240, 24))                # splash pool
    slide = (ctx["t"] * 0.4) % 1.0                                                        # a log slides down
    lx = int(cx - 240 + slide * 340)
    ly = int(GROUND_Y - 210 + slide * 180)
    pygame.draw.ellipse(s, (140, 90, 50), (lx, ly, 70, 24))
    if slide > 0.9:
        for i in range(6):
            pygame.draw.circle(s, (170, 210, 240), (lx + 40 + i * 10, GROUND_Y - 30 - i % 3 * 10), 5)


def wax_museum(s, cx, ctx, font):
    """Pale wax figures on pedestals. Now and then one of them turns its head."""
    for i in range(5):
        x = cx - 240 + i * 120
        pygame.draw.rect(s, (110, 90, 80), (x - 34, GROUND_Y - 40, 68, 40))               # pedestal
        pygame.draw.rect(s, (200, 170, 90), (x - 34, GROUND_Y - 44, 68, 6))
        wax = (226, 214, 196)
        pygame.draw.rect(s, (90 + i * 20, 60, 80), (x - 20, GROUND_Y - 140, 40, 96), border_radius=6)   # clothes
        look = 4 if math.sin(ctx["t"] * 0.9 + i * 2.5) > 0.92 else 0                     # a head turns...
        pygame.draw.circle(s, wax, (x + look, GROUND_Y - 160), 18)
        pygame.draw.circle(s, DARK, (x - 6 + look * 2, GROUND_Y - 162), 3)
        pygame.draw.circle(s, DARK, (x + 6 + look * 2, GROUND_Y - 162), 3)
        pygame.draw.line(s, wax, (x - 20, GROUND_Y - 130), (x - 34, GROUND_Y - 90), 6)  # arms
        pygame.draw.line(s, wax, (x + 20, GROUND_Y - 130), (x + 34, GROUND_Y - 100 - (i % 2) * 30), 6)
        pygame.draw.rect(s, CREAM, (x - 22, GROUND_Y - 30, 44, 12))                      # name plaque
    label(s, "WAX MUSEUM  ·  DO NOT TOUCH", cx, GROUND_Y - 220, (230, 210, 180), font)


def workshop(s, cx, ctx, font):
    pygame.draw.rect(s, (70, 60, 60), (cx - 220, GROUND_Y - 240, 440, 240))
    pygame.draw.rect(s, WOOD, (cx - 180, GROUND_Y - 80, 260, 16))                         # workbench
    pygame.draw.rect(s, WOOD, (cx - 170, GROUND_Y - 64, 12, 64))
    pygame.draw.rect(s, WOOD, (cx + 60, GROUND_Y - 64, 12, 64))
    for i, (x, y, r) in enumerate(((cx + 140, GROUND_Y - 170, 40), (cx + 90, GROUND_Y - 200, 24))):   # turning gears
        angle = ctx["t"] * (1 if i == 0 else -1.6)
        pygame.draw.circle(s, METAL, (x, y), r)
        for tooth in range(8):
            a = angle + tooth * math.pi / 4
            pygame.draw.circle(s, METAL, (int(x + r * math.cos(a)), int(y + r * math.sin(a))), r // 4)
        pygame.draw.circle(s, (70, 60, 60), (x, y), r // 3)
    for i in range(5):                                                                    # tools on the wall
        x = cx - 170 + i * 40
        pygame.draw.line(s, METAL, (x, GROUND_Y - 200), (x, GROUND_Y - 150), 4)
        pygame.draw.rect(s, (150, 40, 40) if i % 2 else METAL, (x - 8, GROUND_Y - 206, 16, 10))
    pygame.draw.rect(s, (200, 200, 150), (cx - 120, GROUND_Y - 120, 60, 40))             # an animatronic head on the bench
    pygame.draw.circle(s, (255, 60, 60), (cx - 104, GROUND_Y - 104), 4)
    pygame.draw.circle(s, (255, 60, 60), (cx - 76, GROUND_Y - 104), 4)
    label(s, "STAFF ONLY", cx - 60, GROUND_Y - 222, (240, 220, 120), font)


def exit_gate(s, cx, ctx, font):
    pygame.draw.rect(s, (40, 70, 60), (cx - 220, GROUND_Y - 30, 440, 30))
    label(s, "EXIT", cx, GROUND_Y - 250, (150, 255, 200), font)


from .pieces_z1 import carousel, cotton_candy, ferris_base, photo_booth, ring_toss, ticket_booth   # noqa: E402
from .pieces_z2 import barrel_tunnel, clown_alley, hall_of_mirrors, puppet_theater, tilted_room   # noqa: E402
from .pieces_z3 import (exit_gate, ghost_train, haunted_manor, log_flume, tunnel_boats, wax_museum,  # noqa: E402
                        workshop)

SET_PIECES = {
    "z1_ticket_booth": ticket_booth, "z1_carousel": carousel, "z1_cotton_candy": cotton_candy,
    "z1_photo_booth": photo_booth, "z1_ring_toss": ring_toss, "z1_ferris_wheel": ferris_base,
    "z2_mirrors": hall_of_mirrors, "z2_barrel": barrel_tunnel, "z2_tilted_room": tilted_room,
    "z2_laughing_stage": laughing_stage, "z2_clown_alley": clown_alley, "z2_puppet_theater": puppet_theater,
    "z3_ghost_train": ghost_train, "z3_tunnel_boats": tunnel_boats, "z3_haunted_manor": haunted_manor,
    "z3_log_flume": log_flume, "z3_wax_museum": wax_museum, "z3_workshop": workshop,
    "finale_gate": exit_gate,
}


def draw_set_piece(surface, beat_id, cx, ctx, font):
    """Draw the scene piece of one attraction around screen position cx (nothing if it has none)."""
    piece = SET_PIECES.get(beat_id)
    if piece is not None and -400 < cx < 1400:
        piece(surface, int(cx), ctx, font)
