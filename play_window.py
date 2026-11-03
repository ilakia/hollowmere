"""
Play Hollowmere in a game window (pygame): pixel-art characters, effects, sound, a park map,
a title menu and a timing bar for attacks.

It uses the SAME engine and directors as play.py. Only two things differ from the terminal game:
- Your hit chance comes from the timing bar (40% for a bad press up to 95% in the sweet spot)
  instead of a fixed 75%. The engine is unchanged: the window just sets your accuracy before
  each attack.
- Games are saved to data/window_runs.csv (with an extra timing_score column), so they are never
  mixed with the fixed-aim games in data/human_runs.csv.
Everything is drawn and generated in code (window/ folder), so there are no image or sound files.

  python play_window.py                      # title menu: pick the director there
  python play_window.py --controller rule    # start with this director selected
  python play_window.py --no-sound

Controls: A attack (then Space to stop the timing bar), D defend, P potion, M mute,
Space/Enter continue, Y/N after a death. Closing the window ends the game without saving it.

  python play_window.py --demo figures/screens   # plays by itself and saves screenshots (for testing)
"""
import argparse
import math
import os
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
from play import HumanPolicy
from window.art import (COLORS, HEIGHT, WIDTH, Button, draw_bar, draw_bubble, draw_glow, draw_text, load_sprites,
                        wrap_text)
from window.effects import Flashes, Fog, Particles, Shake, vignette
from window.park_map import draw_park_map
from window.scenery import Scenery
from window.sound import SoundBank

FPS = 30
POPUP_SECONDS = 1.4
GROUND_Y = 385
WINDOW_DIRECTORS = ["fixed", "random", "rule", "bandit", "predictor"]   # no LLM: it overheats the laptop

# Timing bar: hit chance = TIMING_BASE + TIMING_RANGE * timing score (score 1 = sweet spot, 0 = edge).
# A random press averages a score of about 0.5, i.e. ~67% hit chance, close to the old fixed 75%.
TIMING_BASE = 0.40
TIMING_RANGE = 0.55
TIMING_SPEED = 1.1               # marker sweeps per second (slow enough to learn, fast enough to matter)

BAND_TEXT = {"in_band": "in band (a good fight)", "too_easy": "too easy", "too_hard": "too hard"}
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


def close_game():
    """The window was closed: stop everything (the game is not saved)."""
    pygame.quit()
    sys.exit(0)


def ghost_x(index, count):
    """Spread up to 4 ghosts evenly over the right side of the screen."""
    if count <= 1:
        return 730
    return int(600 + index * 240 / (count - 1))


# ---------------------------------------------------------------- the window
class GameWindow:
    """Everything the screens share: window, fonts, sprites, effects, sound, and what room we are in.
    demo_dir != None: no waiting for input; the game plays itself and saves screenshots."""

    def __init__(self, director_name, demo_dir=None, sound_on=True):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hollowmere")
        # the scene is drawn here, then shaken onto the screen. Depth 24 = no transparency channel: on a Mac the
        # display format has one, and without this the whole scene showed up black in the real window
        self.canvas = pygame.Surface((WIDTH, HEIGHT), 0, 24)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_big = pygame.font.SysFont(None, 44)
        self.font_mark = pygame.font.SysFont(None, 80)
        self.font_title = pygame.font.SysFont(None, 110)
        self.scenery = Scenery()         # layered park per zone, with lighting
        self.zone = 1
        self.sprites = load_sprites()
        self.fog = Fog()
        self.vignette = vignette()
        self.particles = Particles()
        self.shake = Shake()
        self.flashes = Flashes()
        self.sounds = SoundBank(enabled=sound_on and demo_dir is None)
        self.director_name = director_name
        self.room_label = ""
        self.help_mode = None
        self.difficulty = "normal"
        self.is_finale = False
        self.bubble = ""
        self.popups = []                 # (text, colour, x, y, start time)
        self.last_frame = time.time()
        self.demo_dir = demo_dir
        self.demo_shots = 0
        self.demo_choice = None

    # ---- small shared pieces
    def popup(self, text, color, x, y):
        self.popups = [p for p in self.popups if (p[2], p[3]) != (x, y)]   # newest number wins at one spot
        self.popups.append((text, color, x, y, time.time()))

    def draw_popups(self, surface):
        now = time.time()
        self.popups = [p for p in self.popups if now - p[4] < POPUP_SECONDS]
        for text, color, x, y, start in self.popups:
            rise = int((now - start) * 30)                                   # numbers float up as they fade
            draw_text(surface, text, self.font_big, color, x, y - rise, center=True)

    def draw_top_bar(self, surface):
        pygame.draw.rect(surface, COLORS["panel"], (0, 0, WIDTH, 40))
        draw_text(surface, self.room_label, self.font, COLORS["text"], 16, 11)
        sound = "muted (M)" if self.sounds.muted else "sound on (M)"
        draw_text(surface, f"director: {self.director_name}   ·   {sound}", self.font_small,
                  COLORS["dim_text"], WIDTH - 300, 13)

    def draw_sprite(self, name, x, y_bottom, flash=False, flip=False, dy=0):
        """Draw a sprite standing on the ground at x (its centre). flash = white hit silhouette."""
        image, white, outline = self.sprites[name]
        if flash:
            image = white
        if flip:
            image = pygame.transform.flip(image, True, False)
            outline = pygame.transform.flip(outline, True, False)
        left = x - image.get_width() // 2
        top = y_bottom - image.get_height() + dy
        shadow = pygame.Surface((image.get_width(), 16), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
        self.canvas.blit(shadow, (left, y_bottom - 8))
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):        # thin light outline: stands out from the night
            self.canvas.blit(outline, (left + ox, top + oy))
        self.canvas.blit(image, (left, top))

    # ---- drawing loop
    def wait_for(self, draw_scene, buttons):
        """Keep drawing until a button is clicked or its key is pressed. Output: the button's name.
        draw_scene(dt) draws the picture onto self.canvas; dt = seconds since the last frame."""
        if self.demo_dir is not None:
            return self.demo_step(draw_scene, buttons)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.sounds.toggle_mute()
                    continue
                if event.type == pygame.KEYDOWN:
                    for button in buttons:
                        if event.key in button.keys:
                            self.sounds.play("click")
                            return button.name
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for button in buttons:
                        if button.rect.collidepoint(event.pos):
                            self.sounds.play("click")
                            return button.name
            self.show_frame(draw_scene, buttons)
            self.clock.tick(FPS)

    def show_frame(self, draw_scene, buttons):
        now = time.time()
        dt = min(0.1, now - self.last_frame)
        self.last_frame = now
        draw_scene(dt)
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.canvas, self.shake.offset())
        self.screen.blit(self.vignette, (0, 0))
        for button in buttons:
            button.draw(self.screen, self.font)
        pygame.display.flip()

    def demo_step(self, draw_scene, buttons):
        """Demo mode: draw one frame, save it as a screenshot, choose automatically."""
        pygame.event.pump()
        self.show_frame(draw_scene, buttons)
        if self.demo_shots < 400:
            Path(self.demo_dir).mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.screen, str(Path(self.demo_dir) / f"screen_{self.demo_shots:03d}.png"))
            self.demo_shots += 1
        names = [b.name for b in buttons]
        if self.demo_choice in names:
            return self.demo_choice
        return names[0]

    def card(self, title, paragraphs, button_label="Continue  [Space]", side=None):
        """A story or result card. side = function(surface, rect) drawing extra content on the right
        (the park map). Waits for Continue."""
        def draw_scene(dt):
            self.scenery.draw_back(self.canvas, self.zone)
            self.fog.draw(self.canvas, dt)
            self.scenery.draw_front(self.canvas, self.zone, [])
            self.draw_top_bar(self.canvas)
            panel = pygame.Rect(60, 70, 840, 370)
            pygame.draw.rect(self.canvas, COLORS["panel"], panel, border_radius=14)
            pygame.draw.rect(self.canvas, COLORS["glow"], panel, width=2, border_radius=14)
            text_width = 440 if side else 780
            draw_text(self.canvas, title, self.font_big, COLORS["text"], panel.x + 30, panel.y + 22)
            y = panel.y + 76
            for text, color in paragraphs:
                for line in wrap_text(text, self.font, text_width):
                    draw_text(self.canvas, line, self.font, color, panel.x + 30, y)
                    y += 26
                y += 10
            if side:
                side(self.canvas, pygame.Rect(panel.x + 500, panel.y + 60, 320, 290))
        button = Button("continue", button_label, (WIDTH // 2 - 120, 460, 240, 48), [pygame.K_SPACE, pygame.K_RETURN])
        self.wait_for(draw_scene, [button])


# ---------------------------------------------------------------- title menu
def title_menu(w, director):
    """Title screen. The player can pick the director and switch sound. Output: chosen director."""
    index = WINDOW_DIRECTORS.index(director) if director in WINDOW_DIRECTORS else 0
    lineup = ["player", "walt", "wisp", "animatronic", "wraith"]

    def draw_scene(dt):
        w.scenery.draw_back(w.canvas, 1)
        for i, name in enumerate(lineup):
            bob = int(5 * math.sin(time.time() * 2 + i))
            w.draw_sprite(name, 230 + i * 125, 345, dy=bob if i >= 2 else 0)
        w.fog.draw(w.canvas, dt)
        w.scenery.draw_front(w.canvas, 1, [(355, 260, 160, COLORS["flashlight"])])
        flicker = 200 + int(55 * math.sin(time.time() * 3))
        draw_glow(w.canvas, WIDTH // 2, 120, 220, (120, 60, 160), strength=18)
        draw_text(w.canvas, "HOLLOWMERE", w.font_title, (flicker, 220, 255), WIDTH // 2, 115, center=True)
        draw_text(w.canvas, "One night in a haunted theme park. Walt knows the way out... or does he?",
                  w.font, COLORS["dim_text"], WIDTH // 2, 175, center=True)
        draw_text(w.canvas, "A attack (stop the timing bar with Space)   ·   D defend when a ghost glows   ·   "
                  "P potion   ·   M mute", w.font_small, COLORS["dim_text"], WIDTH // 2, 365, center=True)

    while True:
        sound = "off" if w.sounds.muted else "on"
        buttons = [Button("start", "Start  [Space]", (130, 410, 220, 50), [pygame.K_SPACE, pygame.K_RETURN]),
                   Button("director", f"Director: {WINDOW_DIRECTORS[index]}  < >", (370, 410, 250, 50),
                          [pygame.K_LEFT, pygame.K_RIGHT]),
                   Button("sound", f"Sound: {sound}  [S]", (640, 410, 190, 50), [pygame.K_s]),
                   Button("quit", "Quit  [Esc]", (370, 470, 250, 40), [pygame.K_ESCAPE])]
        choice = w.wait_for(draw_scene, buttons)
        if choice == "start":
            return WINDOW_DIRECTORS[index]
        if choice == "director":
            index = (index + 1) % len(WINDOW_DIRECTORS)
        if choice == "sound":
            w.sounds.toggle_mute()
        if choice == "quit":
            close_game()


# ---------------------------------------------------------------- director wrapper (cards + map)
class WindowNarrator:
    """Wraps any director: shows the story card with the park map before each room and a
    result card after it, and adds the room's timing score to the saved row."""

    def __init__(self, inner, story, window, policy):
        self.inner = inner
        self.story = story
        self.window = window
        self.policy = policy
        self.last_mode = None
        self.visited = []

    def decide(self, state):
        decision = self.inner.decide(state)
        beat = self.story.by_id.get(decision.get("beat_id"))
        if beat is None:                      # invalid choice: the engine repairs it, nothing to show
            return decision
        w = self.window
        zone = C.ZONE_NAMES[state["zone"]]
        w.room_label = f"Room {state['room_index'] + 1}/{C.ROOMS_PER_RUN}  ·  {zone}: {beat['title']}"
        w.is_finale = state["is_finale"]
        w.zone = state["zone"]
        w.help_mode = None if state["is_finale"] else decision.get("help_mode")
        w.difficulty = decision.get("difficulty") if decision.get("difficulty") in C.DIFFICULTY else "normal"
        paragraphs = [(beat["text"], COLORS["text"])]
        if w.help_mode and w.help_mode != self.last_mode:      # Walt only speaks when his behaviour changes
            paragraphs.append((f"Walt: '{WALT_BUBBLE.get(w.help_mode, '')}'", COLORS["flashlight"]))
            self.last_mode = w.help_mode
        walt_text = "Walt is the enemy now" if state["is_finale"] else f"Walt: {w.help_mode}"
        paragraphs.append((f"Director's choice: {w.difficulty} difficulty  ·  {walt_text}", COLORS["dim_text"]))

        def park_map(surface, rect):
            draw_park_map(surface, rect, self.story.beats, self.visited, beat["id"], w.font_small)

        w.card(beat["title"], paragraphs, side=park_map)
        w.bubble = WALT_BUBBLE.get(w.help_mode, "")
        return decision

    def observe(self, state, decision, row):
        self.visited.append(row["beat_id"])
        row["timing_score"] = self.policy.take_room_timing()
        band = row["band"]
        result = "cleared" if row["cleared"] else "not cleared"
        text = f"{result}, deaths {row['deaths']}, HP lost {row['hp_lost_ratio']:.0%}"
        self.window.sounds.play("win" if band == "in_band" else "click")
        self.window.card("Room result", [(text, COLORS["text"]), (f"This room was {BAND_TEXT[band]}.", COLORS[band])])
        self.inner.observe(state, decision, row)


# ---------------------------------------------------------------- the human player
class WindowPolicy(HumanPolicy):
    """The human player in the window. Dodge is inherited from HumanPolicy (10%); accuracy is set
    by the timing bar before every attack."""

    def __init__(self, window):
        self.window = window
        self.accuracy = TIMING_BASE + TIMING_RANGE * 0.5
        self.previous_hp = None
        self.previous_ghosts = None
        self.previous_wind_up = False
        self.last_action = None
        self.room_timing = []

    def take_room_timing(self):
        """Mean timing score of this room's attacks (None if no attack), then start a new room."""
        scores = self.room_timing
        self.room_timing = []
        if not scores:
            return None
        return round(sum(scores) / len(scores), 3)

    def choose_action(self, view, rng):
        w = self.window
        self.show_what_happened(view)
        ghosts = view["enemies"]                       # only the ghosts still alive
        hp_mult = C.DIFFICULTY[w.difficulty]["hp_mult"]
        charging = view["wind_up"]
        if charging and not self.previous_wind_up:
            w.sounds.play("charge")
        self.previous_wind_up = charging
        if charging and view["warning"]:
            w.bubble = "It's glowing, DEFEND!"
        elif w.bubble == "It's glowing, DEFEND!":      # the glow is over: back to his normal line
            w.bubble = WALT_BUBBLE.get(w.help_mode, "")

        def draw_scene(dt):
            # 1) scenery behind, 2) characters, 3) fog and lighting, 4) interface on top (always readable)
            c = w.canvas
            w.scenery.draw_back(c, w.zone)
            lights = []
            lunge = w.flashes.progress("lunge", 0.3)
            dx = int(40 * math.sin(math.pi * lunge)) if lunge is not None else 0   # step forward and back
            w.draw_sprite("player", 170 + dx, GROUND_Y, flash=w.flashes.active("player_hit"))
            if not w.is_finale:
                bob = int(2 * math.sin(time.time() * 2))
                w.draw_sprite("walt", 300, GROUND_Y, dy=bob)
                lights.append((380, GROUND_Y - 70, 150, COLORS["flashlight"]))    # Walt's flashlight
            ghost_marks = []
            for i, (kind, hp) in enumerate(ghosts):
                x = ghost_x(i, len(ghosts))
                glowing = charging and kind in ("wraith", "walt")
                if glowing:
                    draw_glow(c, x, GROUND_Y - 50, 100, COLORS["charge"], strength=45)
                    lights.append((x, GROUND_Y - 60, 190, COLORS["charge"]))
                    x = x + int(5 * math.sin(time.time() * 40))                      # fast shaking
                elif kind == "wisp":
                    lights.append((x, GROUND_Y - 40, 90, (150, 200, 255)))          # wisps glow softly
                bob = int(5 * math.sin(time.time() * 3 + i)) if kind in ("wisp", "wraith") else 0
                sprite = "walt_ghost" if kind == "walt" else kind
                w.draw_sprite(sprite, x, GROUND_Y, flash=w.flashes.active(f"ghost{i}"), flip=True, dy=bob)
                ghost_marks.append((kind, hp, x, glowing))
            w.fog.draw(c, dt)
            w.scenery.draw_front(c, w.zone, lights, finale=w.is_finale)

            w.draw_top_bar(c)
            draw_bar(c, 110, GROUND_Y + 12, 120, 12, view["hp"] / view["max_hp"])
            draw_text(c, f"{view['hp']:.0f}/{view['max_hp']} HP", w.font_small, COLORS["text"], 110, GROUND_Y + 30)
            for i in range(view["potions"]):                                       # one bottle per potion
                pygame.draw.rect(c, COLORS["potion"], (110 + i * 18, GROUND_Y + 52, 12, 18), border_radius=3)
            if not w.is_finale:
                draw_text(c, f"Walt: {w.help_mode}", w.font_small, COLORS["dim_text"], 262, GROUND_Y + 12)
                if w.bubble:
                    draw_bubble(c, w.font_small, w.bubble, 300, 245)
            for kind, hp, x, glowing in ghost_marks:
                if glowing:
                    draw_text(c, "!", w.font_mark, COLORS["charge"], x, GROUND_Y - 175, center=True)
                full_hp = C.ENEMY_TYPES[kind]["hp"] * hp_mult
                draw_bar(c, x - 40, GROUND_Y + 12, 80, 10, hp / full_hp)
                draw_text(c, kind, w.font_small, COLORS["dim_text"], x, GROUND_Y + 34, center=True)
            if charging and not view["warning"]:            # no Walt warning: only the glow and this line
                draw_text(c, "Something is glowing brighter and brighter...", w.font_big,
                          COLORS["charge"], WIDTH // 2, 105, center=True)
            w.particles.draw(c, dt)
            w.draw_popups(c)

        buttons = [Button("attack", "A  Attack", (150, 470, 200, 50), [pygame.K_a]),
                   Button("defend", "D  Defend", (380, 470, 200, 50), [pygame.K_d],
                          flashing=charging and view["warning"]),          # only Walt's hint flashes it
                   Button("potion", "P  Potion", (610, 470, 200, 50), [pygame.K_p])]
        if w.demo_dir is not None:      # demo player: defend on a glow, potion when low, else attack
            if charging:
                w.demo_choice = "defend"
            elif view["hp"] < 35 and view["potions"] > 0:
                w.demo_choice = "potion"
            else:
                w.demo_choice = "attack"
        action = w.wait_for(draw_scene, buttons)
        if action == "attack":
            score = self.timing_bar(draw_scene)
            self.accuracy = TIMING_BASE + TIMING_RANGE * score
            self.room_timing.append(score)
            w.flashes.start("lunge", 0.3)
            w.scenery.kick = 25
        self.last_action = action
        self.previous_hp = view["hp"]
        self.previous_ghosts = list(ghosts)
        return action

    def timing_bar(self, draw_scene):
        """A marker sweeps across a bar; the player stops it. Output: timing score 0..1 (1 = centre)."""
        w = self.window
        start = time.time()
        bar = pygame.Rect(230, 100, 500, 34)

        def marker_position():
            # starts at the left edge (the -pi/2), so pressing at once is NOT a perfect hit
            return 0.5 + 0.5 * math.sin(2 * math.pi * TIMING_SPEED * (time.time() - start) - math.pi / 2)

        def draw_with_bar(dt):
            draw_scene(dt)
            c = w.canvas
            panel = bar.inflate(40, 70)
            pygame.draw.rect(c, COLORS["panel"], panel, border_radius=10)
            draw_text(c, "Stop in the middle!  [Space]", w.font, COLORS["text"], bar.centerx, bar.y - 18, center=True)
            pygame.draw.rect(c, COLORS["bar_back"], bar, border_radius=6)
            pygame.draw.rect(c, (200, 170, 60), bar.inflate(-bar.width * 0.5, 0), border_radius=6)   # good zone
            pygame.draw.rect(c, COLORS["hp_good"], bar.inflate(-bar.width * 0.8, 0), border_radius=6)  # sweet spot
            x = bar.x + int(marker_position() * bar.width)
            pygame.draw.rect(c, COLORS["text"], (x - 3, bar.y - 8, 6, bar.height + 16))

        stop = Button("stop", "Strike!  [Space]", (WIDTH // 2 - 110, 160, 220, 44), [pygame.K_SPACE])
        w.wait_for(draw_with_bar, [stop])
        score = max(0.0, 1 - abs(marker_position() - 0.5) / 0.5)
        if score > 0.8:
            label, color = "Perfect!", COLORS["heal"]
        elif score > 0.5:
            label, color = "Good", COLORS["charge"]
        else:
            label, color = "Clumsy...", COLORS["dim_text"]
        w.popup(f"{label} {TIMING_BASE + TIMING_RANGE * score:.0%}", color, 470, 330)
        return score

    def show_what_happened(self, view):
        """Compare with the last turn: numbers, effects and sounds for damage, heals and hits."""
        w = self.window
        if self.previous_hp is None:
            return
        change = view["hp"] - self.previous_hp
        if change < 0:
            blocked = self.last_action == "defend"
            w.popup(f"{change:.0f} HP blocked!" if blocked else f"{change:.0f} HP", COLORS["damage"], 150, 210)
            w.shake.start(3 if blocked else 8, 0.25)
            w.flashes.start("player_hit", 0.15)
            w.sounds.play("block" if blocked else "hurt")
        elif change > 0 and self.last_action == "potion":
            w.popup(f"+{change:.0f} potion", COLORS["heal"], 150, 210)
            w.particles.rise(170, GROUND_Y - 60, COLORS["potion"])
            w.sounds.play("potion")
        elif change > 0:
            w.popup(f"+{change:.0f} Walt heals", COLORS["heal"], 150, 210)
            w.particles.rise(170, GROUND_Y - 60, COLORS["heal"])
            w.bubble = "You're hurt. Hold still, kid."
            w.sounds.play("heal")
        self.show_ghost_hits(view["enemies"])

    def show_ghost_hits(self, ghosts):
        """Effects over the ghosts: the damage you (and Walt, in fight mode) did last turn."""
        w = self.window
        before = self.previous_ghosts
        if not before:
            return
        if len(ghosts) < len(before):                  # the front ghost was defeated (attacks hit the front one)
            x = ghost_x(0, len(before))
            w.popups = [p for p in w.popups if p[3] != 300]
            w.popup("defeated!", COLORS["heal"], x, 300)
            w.particles.burst(x, GROUND_Y - 50, COLORS["glow"], count=40, speed=220)
            w.sounds.play("defeat")
            return
        hit_any = False
        for i, ((kind, hp), (_, old_hp)) in enumerate(zip(ghosts, before)):
            if hp < old_hp:
                x = ghost_x(i, len(ghosts))
                w.popup(f"-{old_hp - hp:.0f}", COLORS["text"], x + 50, 300)
                w.flashes.start(f"ghost{i}", 0.15)
                w.particles.burst(x, GROUND_Y - 50, (255, 240, 200), count=10, speed=140, lifetime=0.4, size=3)
                hit_any = True
        if hit_any:
            w.sounds.play("hit")
        elif self.last_action == "attack":
            w.popup("miss", COLORS["dim_text"], ghost_x(0, len(ghosts)) + 50, 300)
            w.sounds.play("miss")

    def wants_to_quit(self, consecutive_deaths):
        w = self.window
        self.previous_hp = None        # the room restarts with fresh HP, that is not healing
        self.previous_ghosts = None
        w.sounds.play("death")

        def draw_scene(dt):
            w.canvas.fill((0, 0, 0))
            w.fog.draw(w.canvas, dt)
            draw_text(w.canvas, "Everything goes dark...", w.font_big, COLORS["damage"], WIDTH // 2, 200, center=True)
            draw_text(w.canvas, "Try this attraction again?", w.font, COLORS["text"], WIDTH // 2, 260, center=True)

        buttons = [Button("yes", "Y  Try again", (260, 330, 200, 50), [pygame.K_y]),
                   Button("no", "N  Give up", (500, 330, 200, 50), [pygame.K_n])]
        return w.wait_for(draw_scene, buttons) == "no"

    def end_of_room(self, room_index):
        self.previous_hp = None        # resting between rooms heals you, that is not Walt
        self.previous_ghosts = None
        self.previous_wind_up = False
        self.window.popups = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controller", default="rule", choices=WINDOW_DIRECTORS, help="pre-selected in the menu")
    ap.add_argument("--out", default="data/window_runs.csv")
    ap.add_argument("--no-sound", action="store_true")
    ap.add_argument("--demo", default=None, help="folder for screenshots: plays by itself, saves no game")
    args = ap.parse_args()
    if args.demo is not None:
        os.environ["SDL_AUDIODRIVER"] = "dummy"       # demo runs silently

    story = Story()
    seed = random.randrange(10**6)
    player_id = uuid.uuid4().hex[:6]       # anonymous, not linked to any name
    window = GameWindow(args.controller, demo_dir=args.demo, sound_on=not args.no_sound)
    window.sounds.start_music()
    director = title_menu(window, args.controller)
    window.director_name = director
    window.room_label = "Hollowmere Park, midnight"
    window.card("Midnight", [
        ("You wake up inside Hollowmere Park. The gates are locked.", COLORS["text"]),
        ("An old mechanic with a flashlight finds you. 'Name's Walt. Stick with me, I know the way out.'",
         COLORS["flashlight"])], button_label="Follow Walt  [Space]")

    policy = WindowPolicy(window)
    controller = WindowNarrator(CONTROLLERS[director](rng=random.Random(seed)), story, window, policy)
    rows = play_run(controller, policy, story, seed)

    outcome = rows[-1]["run_outcome"]
    window.sounds.play("win" if outcome == "escaped" else "death")
    window.room_label = "The end"
    window.card("Escaped!" if outcome == "escaped" else "Trapped", [(ENDINGS[outcome], COLORS["text"])],
                button_label="Close  [Space]")
    pygame.quit()

    if args.demo is not None:
        print(f"demo finished ({outcome}), screenshots in {args.demo}")
        return
    for r in rows:
        r.update({"run_id": f"window-{player_id}-{seed}", "controller": director,
                  "bot_type": "human", "player_id": player_id})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
    print(f"Game saved to {out}")


if __name__ == "__main__":
    main()
