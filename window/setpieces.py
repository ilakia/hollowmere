"""
Scene pieces: every attraction gets its own animated set dressing, drawn behind the characters.
The scenes themselves live in pieces_z1.py (Entrance), pieces_z2.py (Funhouse) and pieces_z3.py
(Dark Rides + exit gate), with shared drawing tools in pieces_kit.py. The Laughing Lady is here.

A piece is drawn around a centre x on the ground line. While the player walks up, it slides in from
the right; during the fight it stays behind the ghosts.
ctx = {"t": time in seconds, "sprites": sprite images, "player_x", "walt_x", "show_walt", "mood"}.
"""
import math

import pygame

from .pieces_z1 import carousel, cotton_candy, ferris_base, photo_booth, ring_toss, ticket_booth
from .pieces_z2 import barrel_tunnel, clown_alley, hall_of_mirrors, puppet_theater, tilted_room
from .pieces_z3 import exit_gate, ghost_train, haunted_manor, log_flume, tunnel_boats, wax_museum, workshop

GROUND_Y = 385
DARK = (20, 16, 26)
WOOD = (92, 60, 40)


def label(surface, text, cx, y, color, font):
    """A small lit sign on the piece."""
    image = font.render(text, True, color)
    board = image.get_rect(center=(cx, y)).inflate(16, 8)
    pygame.draw.rect(surface, DARK, board, border_radius=5)
    pygame.draw.rect(surface, color, board, width=2, border_radius=5)
    surface.blit(image, image.get_rect(center=(cx, y)))


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
