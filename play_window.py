"""
Play Hollowmere in a game window (pygame) instead of the terminal.

It uses the SAME engine, directors and telemetry as play.py, so a game played here is saved in
data/human_runs.csv exactly like a terminal game (useful for the playtest). Only the drawing is new.
Everything is drawn with simple shapes in code, so there are no image files.

  python play_window.py                     # fixed director
  python play_window.py --controller rule   # fixed, random, rule or bandit

Controls: A attack, D defend, P potion (or click the buttons). Space or Enter to continue.
Y / N after a death. Closing the window ends the game without saving it.

  python play_window.py --demo figures/screens   # plays by itself and saves screenshots (for testing)
"""
import argparse
import math
import random
import sys
import time
import uuid
from pathlib import Path

import pandas as pd
import pygame

from game import config as C
from game.controllers import CONTROLLERS
from game.engine import play_run
from game.story import Story
from play import WALT_LINES, HumanPolicy

WIDTH, HEIGHT = 960, 540
FPS = 30
POPUP_SECONDS = 1.4

COLORS = {
    "sky_top": (12, 10, 30), "sky_bottom": (40, 20, 55), "ground": (25, 22, 30),
    "text": (235, 230, 220), "dim_text": (160, 150, 170), "panel": (20, 18, 32),
    "player": (70, 190, 200), "walt": (150, 140, 120), "flashlight": (255, 230, 140),
    "hp_good": (90, 200, 110), "hp_low": (220, 90, 80), "bar_back": (60, 55, 70),
    "damage": (240, 90, 80), "heal": (110, 230, 140), "glow": (190, 120, 255), "charge": (255, 190, 60),
    "button": (55, 45, 80), "button_hover": (85, 70, 120), "potion": (200, 60, 120),
    "in_band": (110, 230, 140), "too_easy": (120, 170, 240), "too_hard": (240, 90, 80),
}
BAND_TEXT = {"in_band": "in band (a good fight)", "too_easy": "too easy", "too_hard": "too hard"}
# Walt's speech bubble at the start of a room (short versions; the heal line itself appears when he heals)
WALT_BUBBLE = {
    "stay_back": "You've got this. I'll keep watch.",
    "hint": "Watch the big ones. Duck when they glow.",
    "heal": "I've got bandages if it gets bad.",
    "fight": "Stay behind me.",
}
ENDINGS = {
    "escaped": "The gate creaks open. Dawn. Walt fades into the light. 'Not bad. Not bad at all.'",
    "out_of_lives": "The lights go out. Tomorrow, the photo booth prints a new picture: you, with the 1987 staff.",
    "quit": "You stop walking. The park keeps you.",
}


# ---------------------------------------------------------------- small drawing helpers
def close_game():
    """The window was closed: stop everything (the game is not saved)."""
    pygame.quit()
    sys.exit(0)


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


def draw_text(surface, text, font, color, x, y, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)


def draw_bar(surface, x, y, width, height, share):
    """HP bar: green when above 40%, red below."""
    share = max(0.0, min(1.0, share))
    color = COLORS["hp_good"] if share > 0.4 else COLORS["hp_low"]
    pygame.draw.rect(surface, COLORS["bar_back"], (x, y, width, height), border_radius=4)
    pygame.draw.rect(surface, color, (x, y, int(width * share), height), border_radius=4)


def draw_glow(surface, x, y, radius, color, strength=25):
    """A soft pulsing circle of light behind a figure (transparent layers; strength = opacity per layer)."""
    pulse = 0.75 + 0.25 * math.sin(time.time() * 6)
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for step in range(6):
        r = int(radius * (1 - step / 7) * pulse)
        pygame.draw.circle(glow, color + (strength,), (radius, radius), r)
    surface.blit(glow, (x - radius, y - radius))


def draw_bubble(surface, font, text, x, y):
    """Speech bubble with its tail pointing down to (x, y)."""
    lines = wrap_text(text, font, 260)
    height = 12 + 22 * len(lines)
    box = pygame.Rect(x - 40, y - height - 16, 280, height)
    pygame.draw.rect(surface, COLORS["text"], box, border_radius=10)
    pygame.draw.polygon(surface, COLORS["text"], [(x - 10, box.bottom), (x + 10, box.bottom), (x, y)])
    for i, line in enumerate(lines):
        draw_text(surface, line, font, COLORS["panel"], box.x + 10, box.y + 6 + 22 * i)


class Button:
    """A clickable rectangle with a label and the keyboard keys that also press it."""

    def __init__(self, name, label, rect, keys, flashing=False):
        self.name = name
        self.label = label
        self.rect = pygame.Rect(rect)
        self.keys = keys
        self.flashing = flashing      # True: the border blinks (used for Walt's DEFEND warning)

    def draw(self, surface, font):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = COLORS["button_hover"] if hover else COLORS["button"]
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if self.flashing and math.sin(time.time() * 10) > 0:
            pygame.draw.rect(surface, COLORS["charge"], self.rect, width=4, border_radius=8)
        else:
            pygame.draw.rect(surface, COLORS["glow"], self.rect, width=2, border_radius=8)
        draw_text(surface, self.label, font, COLORS["text"], self.rect.centerx, self.rect.centery, center=True)


# ---------------------------------------------------------------- figures (simple shapes)
def draw_player(surface, x, y):
    pygame.draw.rect(surface, COLORS["player"], (x - 18, y - 40, 36, 60), border_radius=10)
    pygame.draw.circle(surface, (230, 200, 170), (x, y - 58), 18)


def draw_walt(surface, x, y, as_ghost=False):
    """Walt, the old mechanic with a flashlight. In the finale he is a ghost (pale, glowing)."""
    coat = (120, 200, 170) if as_ghost else COLORS["walt"]     # no constant glow: it would hide his charge-up
    pygame.draw.rect(surface, coat, (x - 22, y - 44, 44, 66), border_radius=8)
    pygame.draw.circle(surface, (200, 230, 215) if as_ghost else (220, 190, 160), (x, y - 62), 18)
    pygame.draw.rect(surface, (90, 80, 70), (x - 20, y - 82, 40, 8))             # cap
    pygame.draw.polygon(surface, COLORS["flashlight"] + (0,), [(x + 22, y - 20), (x + 70, y - 40), (x + 70, y)])


def draw_ghost(surface, kind, x, y, glowing, mark_font):
    """wisp = small floating light, animatronic = boxy robot, wraith = tall shadow, walt = boss.
    glowing = it is charging a big hit: bright orange glow, shaking, and a "!" above it."""
    if glowing:
        draw_glow(surface, x, y - 30, 95, COLORS["charge"], strength=45)
        x = x + int(5 * math.sin(time.time() * 40))         # fast shaking
        draw_text(surface, "!", mark_font, COLORS["charge"], x, y - 130, center=True)
    bob = int(4 * math.sin(time.time() * 3 + x))           # gentle floating movement
    if kind == "wisp":
        pygame.draw.circle(surface, (170, 220, 255), (x, y - 30 + bob), 16)
        for dx in (-10, 0, 10):
            pygame.draw.circle(surface, (170, 220, 255), (x + dx, y - 16 + bob), 6)
    elif kind == "animatronic":
        pygame.draw.rect(surface, (150, 100, 60), (x - 24, y - 60, 48, 70), border_radius=6)
        pygame.draw.circle(surface, (255, 60, 60), (x - 9, y - 42), 5)
        pygame.draw.circle(surface, (255, 60, 60), (x + 9, y - 42), 5)
    elif kind == "wraith":
        pygame.draw.ellipse(surface, (70, 40, 90), (x - 28, y - 90 + bob, 56, 110))
        pygame.draw.circle(surface, (240, 240, 255), (x - 9, y - 60 + bob), 5)
        pygame.draw.circle(surface, (240, 240, 255), (x + 9, y - 60 + bob), 5)
    else:
        draw_walt(surface, x, y, as_ghost=True)


def make_background():
    """Night sky, distant ferris wheel and a row of fairground lights (drawn once, reused)."""
    background = pygame.Surface((WIDTH, HEIGHT))
    for row in range(HEIGHT):
        share = row / HEIGHT
        color = [int(COLORS["sky_top"][i] * (1 - share) + COLORS["sky_bottom"][i] * share) for i in range(3)]
        pygame.draw.line(background, color, (0, row), (WIDTH, row))
    pygame.draw.circle(background, (50, 40, 65), (780, 200), 120, width=3)      # ferris wheel
    for spoke in range(8):
        angle = spoke * math.pi / 4
        end = (780 + 120 * math.cos(angle), 200 + 120 * math.sin(angle))
        pygame.draw.line(background, (50, 40, 65), (780, 200), end, 2)
    pygame.draw.rect(background, COLORS["ground"], (0, 380, WIDTH, HEIGHT - 380))
    for i in range(16):                                                         # string of lights
        pygame.draw.circle(background, (255, 200, 120), (30 + i * 60, 60 + int(12 * math.sin(i))), 3)
    return background


# ---------------------------------------------------------------- the window and its screens
class GameWindow:
    """Everything the screens share: the window, fonts, what room we are in, Walt's bubble,
    the floating damage numbers. demo_dir != None: no waiting for input, screenshots instead."""

    def __init__(self, director_name, demo_dir=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hollowmere")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_big = pygame.font.SysFont(None, 44)
        self.font_mark = pygame.font.SysFont(None, 80)      # the "!" above a charging ghost
        self.background = make_background()
        self.director_name = director_name
        self.room_label = ""
        self.help_mode = None
        self.difficulty = "normal"
        self.is_finale = False
        self.bubble = ""
        self.popups = []            # (text, color, x, y, start time)
        self.demo_dir = demo_dir
        self.demo_shots = 0
        self.demo_choice = None     # what the demo player "presses" on the next screen

    def popup(self, text, color, x, y):
        # a new number replaces an older one at the same spot, so fast clicking does not stack them
        self.popups = [p for p in self.popups if (p[2], p[3]) != (x, y)]
        self.popups.append((text, color, x, y, time.time()))

    def draw_popups(self):
        now = time.time()
        self.popups = [p for p in self.popups if now - p[4] < POPUP_SECONDS]
        for text, color, x, y, start in self.popups:
            rise = int((now - start) * 30)       # numbers float upwards while they fade out
            draw_text(self.screen, text, self.font_big, color, x, y - rise, center=True)

    def wait_for(self, draw_scene, buttons):
        """Keep drawing the scene until a button is clicked or its key is pressed.
        Inputs: draw_scene = function that draws the picture, buttons = list of Button
        Output: the name of the chosen button"""
        if self.demo_dir is not None:
            return self.demo_step(draw_scene, buttons)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()
                if event.type == pygame.KEYDOWN:
                    for button in buttons:
                        if event.key in button.keys:
                            return button.name
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for button in buttons:
                        if button.rect.collidepoint(event.pos):
                            return button.name
            draw_scene()
            for button in buttons:
                button.draw(self.screen, self.font)
            pygame.display.flip()
            self.clock.tick(FPS)

    def demo_step(self, draw_scene, buttons):
        """Demo mode: draw one frame, save the first screenshots, choose automatically."""
        pygame.event.pump()
        draw_scene()
        for button in buttons:
            button.draw(self.screen, self.font)
        pygame.display.flip()
        if self.demo_shots < 400:
            Path(self.demo_dir).mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.screen, str(Path(self.demo_dir) / f"screen_{self.demo_shots:02d}.png"))
            self.demo_shots += 1
        names = [b.name for b in buttons]
        if self.demo_choice in names:
            return self.demo_choice
        return names[0]

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, COLORS["panel"], (0, 0, WIDTH, 40))
        draw_text(self.screen, self.room_label, self.font, COLORS["text"], 16, 11)
        right = f"director: {self.director_name}"
        draw_text(self.screen, right, self.font_small, COLORS["dim_text"], WIDTH - 200, 13)

    def card(self, title, paragraphs, button_label="Continue  [Space]", extra=None):
        """A story or result card in the middle of the screen; waits for Continue."""
        def draw_scene():
            self.screen.blit(self.background, (0, 0))
            self.draw_top_bar()
            panel = pygame.Rect(140, 80, 680, 360)
            pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=14)
            pygame.draw.rect(self.screen, COLORS["glow"], panel, width=2, border_radius=14)
            draw_text(self.screen, title, self.font_big, COLORS["text"], panel.centerx, panel.y + 40, center=True)
            y = panel.y + 80
            for text, color in paragraphs:
                for line in wrap_text(text, self.font, 620):
                    draw_text(self.screen, line, self.font, color, panel.x + 30, y)
                    y += 26
                y += 10
            if extra:
                extra()
        button = Button("continue", button_label, (WIDTH // 2 - 110, 455, 220, 46), [pygame.K_SPACE, pygame.K_RETURN])
        self.wait_for(draw_scene, [button])


class WindowNarrator:
    """Wraps any director: shows a story card before each room and a result card after it."""

    def __init__(self, inner, story, window):
        self.inner = inner
        self.story = story
        self.window = window
        self.last_mode = None

    def decide(self, state):
        decision = self.inner.decide(state)
        beat = self.story.by_id.get(decision.get("beat_id"))
        if beat is None:          # invalid choice: the engine repairs it, nothing to show yet
            return decision
        w = self.window
        zone = C.ZONE_NAMES[state["zone"]]
        w.room_label = f"Room {state['room_index'] + 1}/{C.ROOMS_PER_RUN}  ·  {zone}: {beat['title']}"
        w.is_finale = state["is_finale"]
        w.help_mode = None if state["is_finale"] else decision.get("help_mode")
        w.difficulty = decision.get("difficulty") if decision.get("difficulty") in C.DIFFICULTY else "normal"
        paragraphs = [(beat["text"], COLORS["text"])]
        if w.help_mode and w.help_mode != self.last_mode:      # Walt only speaks when his behaviour changes
            paragraphs.append((WALT_LINES.get(w.help_mode, ""), COLORS["flashlight"]))
            self.last_mode = w.help_mode
        walt_text = "Walt is the enemy now" if state["is_finale"] else f"Walt: {w.help_mode}"
        paragraphs.append((f"Director's choice: {decision.get('difficulty')} difficulty  ·  {walt_text}",
                           COLORS["dim_text"]))
        w.card(beat["title"], paragraphs)
        w.bubble = WALT_BUBBLE.get(w.help_mode, "")
        return decision

    def observe(self, state, decision, row):
        band = row["band"]
        result = "cleared" if row["cleared"] else "not cleared"
        text = f"{result}, deaths {row['deaths']}, HP lost {row['hp_lost_ratio']:.0%}"
        self.window.card("Room result", [(text, COLORS["text"]),
                                         (f"This room was {BAND_TEXT[band]}.", COLORS[band])])
        self.inner.observe(state, decision, row)


class WindowPolicy(HumanPolicy):
    """The human player, but choices come from the window instead of typed letters.
    Same accuracy and dodge as the terminal version (inherited from HumanPolicy)."""

    def __init__(self, window):
        self.window = window
        self.previous_hp = None
        self.previous_ghosts = None
        self.last_action = None

    def choose_action(self, view, rng):
        w = self.window
        self.show_what_happened(view)
        ghosts = view["enemies"]          # only the ghosts still alive
        hp_mult = C.DIFFICULTY[w.difficulty]["hp_mult"]
        glowing_kinds = ("wraith", "walt") if view["wind_up"] else ()
        if view["wind_up"] and view["warning"]:
            w.bubble = "It's glowing, DEFEND!"
        elif w.bubble == "It's glowing, DEFEND!":          # the glow is over: back to his normal line
            w.bubble = WALT_BUBBLE.get(w.help_mode, "")

        def draw_scene():
            w.screen.blit(w.background, (0, 0))
            w.draw_top_bar()
            draw_player(w.screen, 180, 340)
            draw_bar(w.screen, 120, 375, 120, 12, view["hp"] / view["max_hp"])
            draw_text(w.screen, f"{view['hp']:.0f}/{view['max_hp']} HP", w.font_small, COLORS["text"], 120, 392)
            for i in range(view["potions"]):                      # one bottle per potion left
                pygame.draw.rect(w.screen, COLORS["potion"], (120 + i * 18, 414, 12, 18), border_radius=3)
            if not w.is_finale:
                draw_walt(w.screen, 300, 340)
                draw_text(w.screen, f"Walt: {w.help_mode}", w.font_small, COLORS["dim_text"], 265, 375)
                if w.bubble:
                    draw_bubble(w.screen, w.font_small, w.bubble, 300, 250)
            for i, (kind, hp) in enumerate(ghosts):
                full_hp = C.ENEMY_TYPES[kind]["hp"] * hp_mult    # a ghost's HP at the start of the room
                x = 600 + i * 120
                draw_ghost(w.screen, kind, x, 340, kind in glowing_kinds, w.font_mark)
                draw_bar(w.screen, x - 40, 375, 80, 10, hp / full_hp)
                draw_text(w.screen, kind, w.font_small, COLORS["dim_text"], x, 398, center=True)
            if view["wind_up"] and not view["warning"]:      # no Walt warning: only the glow and this line
                draw_text(w.screen, "Something is glowing brighter and brighter...", w.font_big,
                          COLORS["charge"], WIDTH // 2, 105, center=True)
            w.draw_popups()

        buttons = [Button("attack", "A  Attack", (150, 460, 200, 50), [pygame.K_a]),
                   Button("defend", "D  Defend", (380, 460, 200, 50), [pygame.K_d],
                          flashing=view["wind_up"] and view["warning"]),      # only Walt's hint flashes it
                   Button("potion", "P  Potion", (610, 460, 200, 50), [pygame.K_p])]
        if w.demo_dir is not None:      # demo player: defend on a glow, potion when low, else attack
            if view["wind_up"]:
                w.demo_choice = "defend"
            elif view["hp"] < 35 and view["potions"] > 0:
                w.demo_choice = "potion"
            else:
                w.demo_choice = "attack"
        self.last_action = w.wait_for(draw_scene, buttons)
        self.previous_hp = view["hp"]
        self.previous_ghosts = list(ghosts)
        return self.last_action

    def show_what_happened(self, view):
        """Compare HP with the last turn and show floating numbers (and Walt's heal line)."""
        w = self.window
        if self.previous_hp is None:
            return
        change = view["hp"] - self.previous_hp
        if change < 0 and self.last_action == "defend":
            w.popup(f"{change:.0f} HP blocked!", COLORS["damage"], 150, 185)
        elif change < 0:
            w.popup(f"{change:.0f} HP", COLORS["damage"], 150, 185)
        elif change > 0 and self.last_action == "potion":
            w.popup(f"+{change:.0f} potion", COLORS["heal"], 150, 185)
        elif change > 0:
            w.popup(f"+{change:.0f} Walt heals", COLORS["heal"], 150, 185)
            w.bubble = "You're hurt. Hold still, kid."
        self.show_ghost_hits(view["enemies"])

    def show_ghost_hits(self, ghosts):
        """Floating numbers over the ghosts: the damage you (and Walt, in fight mode) did last turn."""
        w = self.window
        before = self.previous_ghosts
        if not before:
            return
        if len(ghosts) < len(before):              # the front ghost was defeated (attacks hit the front one)
            w.popup("defeated!", COLORS["heal"], 600, 300)
            return
        for i, ((kind, hp), (_, old_hp)) in enumerate(zip(ghosts, before)):
            if hp < old_hp:
                w.popup(f"-{old_hp - hp:.0f}", COLORS["text"], 650 + i * 120, 300)

    def wants_to_quit(self, consecutive_deaths):
        w = self.window
        self.previous_hp = None        # the room restarts with fresh HP, that is not healing
        self.previous_ghosts = None

        def draw_scene():
            w.screen.fill((0, 0, 0))
            draw_text(w.screen, "Everything goes dark...", w.font_big, COLORS["damage"], WIDTH // 2, 200, center=True)
            draw_text(w.screen, "Try this attraction again?", w.font, COLORS["text"], WIDTH // 2, 260, center=True)

        buttons = [Button("yes", "Y  Try again", (260, 330, 200, 50), [pygame.K_y]),
                   Button("no", "N  Give up", (500, 330, 200, 50), [pygame.K_n])]
        return w.wait_for(draw_scene, buttons) == "no"

    def end_of_room(self, room_index):
        self.previous_hp = None        # resting between rooms heals you, that is not Walt
        self.previous_ghosts = None
        self.window.popups = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controller", default="fixed", choices=["fixed", "random", "rule", "bandit"])
    ap.add_argument("--out", default="data/human_runs.csv")
    ap.add_argument("--demo", default=None, help="folder for screenshots: plays by itself, saves nothing")
    args = ap.parse_args()

    story = Story()
    seed = random.randrange(10**6)
    player_id = uuid.uuid4().hex[:6]       # anonymous, not linked to any name
    window = GameWindow(args.controller, demo_dir=args.demo)
    window.room_label = "Hollowmere Park, midnight"
    window.card("Hollowmere", [
        ("Midnight. You wake up inside Hollowmere Park. The gates are locked.", COLORS["text"]),
        ("An old mechanic with a flashlight finds you. 'Name's Walt. Stick with me, I know the way out.'",
         COLORS["flashlight"]),
        ("Controls: A attack, D defend (halves damage, best when a ghost glows), P potion (+35 HP, 3 per run).",
         COLORS["dim_text"])], button_label="Start  [Space]")

    controller = WindowNarrator(CONTROLLERS[args.controller](rng=random.Random(seed)), story, window)
    rows = play_run(controller, WindowPolicy(window), story, seed)

    outcome = rows[-1]["run_outcome"]
    window.room_label = "The end"
    window.card("Escaped!" if outcome == "escaped" else "Trapped", [(ENDINGS[outcome], COLORS["text"])],
                button_label="Close  [Space]")
    pygame.quit()

    if args.demo is not None:
        print(f"demo finished ({outcome}), screenshots in {args.demo}")
        return
    for r in rows:
        r.update({"run_id": f"human-{player_id}-{seed}", "controller": args.controller,
                  "bot_type": "human", "player_id": player_id})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
    print(f"Telemetry saved to {out}")


if __name__ == "__main__":
    main()
