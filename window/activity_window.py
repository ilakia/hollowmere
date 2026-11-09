"""
The three playable activities of the playtest (game/activities.py has the rules): each STEP of an activity
is one short real-time moment in the window, and returns success (True) or a mistake (False). The engine
counts successes, mistakes and the fail budget exactly as for the bots, and Walt steps in between steps.

  Flashlight Search (Night A): move the beam (mouse or arrow keys), press Space when the marker is lit.
  Lake Crossing (Night B):     press the arrow that shows (left / right stroke) in time; D when a hand grabs.
  Smoke Escape (Night C):      choose the left or right way (arrow keys) before the smoke closes in;
                               the safe way has lighter smoke and no flames.

Walt's settings change the mini-game itself:
  difficulty -> beam size / time window / timer / how clear the clues are
  help       -> point (an arrow to the marker), hold_light (bigger beam), warn (a warning before a hand),
                row_with_you (a longer window), steer (forgives a slip, in the engine), shout_way (Walt calls
                the way), when_asked (he calls it only after a mistake in this part)
"""
import math
import random
import time

import pygame

from window.art import COLORS, HEIGHT, WIDTH, draw_bubble, draw_text

GROUND_Y = 385
CONTROLS = {
    "act_flashlight": "Move the beam with the MOUSE (or the arrow keys). Press SPACE when the glowing marker is in the light.",
    "act_lake": "Press the ARROW that appears (LEFT or RIGHT stroke) before the ring closes. A hand grabs the boat? Press D!",
    "act_smoke": "Pick a way with LEFT or RIGHT before the smoke closes in. Safe smoke is lighter; fire smoke is black, with embers.",
}
FLASH_BEAM = {"easy": 120, "normal": 90, "hard": 66}
FLASH_TIME = {"easy": 6.0, "normal": 4.5, "hard": 3.3}
LAKE_WINDOW = {"easy": 1.4, "normal": 1.0, "hard": 0.72}
LAKE_HAND = {"easy": 0.15, "normal": 0.25, "hard": 0.35}
SMOKE_TIME = {"easy": 6.0, "normal": 4.2, "hard": 2.8}
SMOKE_CLARITY = {"easy": 1.0, "normal": 0.55, "hard": 0.25}     # 1 = black vs white smoke, 0 = the same grey
DEMO_SUCCESS = 0.7


class ActivityRunner:
    """Runs one step of the current activity in the window. Output of step(): True = success."""

    def __init__(self, window):
        self.w = window
        self.rng = random.Random()
        self.stroke = 0                        # lake: left / right strokes alternate
        self.boat_x = 0.0
        self.segment_mistake = (None, False)   # smoke: (segment, a mistake happened in it)
        self.last_mistakes = 0
        self.message = ""

    # ---- shared pieces
    def hud(self, c, view, title):
        """Top line: the activity, progress and the fail budget as a meter."""
        w = self.w
        w.draw_top_bar(c)
        draw_text(c, f"{title}: {view['progress']} of {view['goal']}", w.font_big, COLORS["charge"], 30, 52)
        draw_text(c, "danger", w.font_small, COLORS["dim_text"], WIDTH - 280, 58)
        meter = pygame.Rect(WIDTH - 220, 56, 190, 16)
        pygame.draw.rect(c, COLORS["bar_back"], meter, border_radius=6)
        share = view["mistakes"] / view["budget"]
        pygame.draw.rect(c, COLORS["damage"], (meter.x, meter.y, int(meter.width * share), meter.height), border_radius=6)
        if self.message:
            draw_text(c, self.message, w.font, COLORS["text"], WIDTH // 2, HEIGHT - 40, center=True)
        if w.bubble:
            draw_bubble(c, w.font_small, w.bubble, 300, 250)

    def result(self, success, text_ok, text_bad):
        w = self.w
        w.sounds.play("hit" if success else "hurt")
        self.message = text_ok if success else text_bad
        if not success:
            w.shake.start(6, 0.25)
        return success

    def step(self, view, rng):
        if self.w.demo_dir is not None:                         # demo: fast, and the same every time
            self.w.tick()
            return rng.random() < DEMO_SUCCESS
        if view["activity"] == "act_flashlight":
            return self.flashlight(view)
        if view["activity"] == "act_lake":
            return self.lake(view)
        return self.smoke(view)

    # ---- Night A: Flashlight Search
    def flashlight(self, view):
        w = self.w
        beam = FLASH_BEAM[view["difficulty"]] + (35 if view["help"] == "hold_light" else 0)
        limit = FLASH_TIME[view["difficulty"]]
        marker = (self.rng.randint(90, WIDTH - 90), self.rng.randint(130, GROUND_Y - 20))
        eyes = [(self.rng.randint(40, WIDTH - 40), self.rng.randint(110, GROUND_Y)) for _ in range(6)]
        x, y = pygame.mouse.get_pos()
        start = time.time()
        while True:
            dt = w.tick()
            elapsed = time.time() - start
            keys = pygame.key.get_pressed()
            moved = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT], keys[pygame.K_DOWN] - keys[pygame.K_UP])
            if moved != (0, 0):
                x, y = x + moved[0] * 420 * dt, y + moved[1] * 420 * dt
            elif pygame.mouse.get_focused():
                x, y = pygame.mouse.get_pos()
            x, y = max(0, min(WIDTH, x)), max(40, min(HEIGHT, y))
            lit = math.hypot(x - marker[0], y - marker[1]) < beam * 0.75
            for event in w.events:
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == pygame.MOUSEBUTTONDOWN:
                    return self.result(lit, "Found it! On to the next one.", "Nothing there... something brushes past you.")
            if elapsed > limit:
                return self.result(False, "", "Too slow! A cold hand grabs you in the dark.")
            c = w.canvas
            w.scenery.draw_back(c, 3)
            w.draw_piece(170, 300, True)
            pulse = 0.6 + 0.4 * abs(math.sin(elapsed * 5))           # the marker: a glowing arrow sign
            pygame.draw.polygon(c, (int(255 * pulse), int(220 * pulse), 90),
                                [(marker[0] - 18, marker[1] - 10), (marker[0] + 8, marker[1] - 10), (marker[0] + 8, marker[1] - 20),
                                 (marker[0] + 26, marker[1]), (marker[0] + 8, marker[1] + 20), (marker[0] + 8, marker[1] + 10),
                                 (marker[0] - 18, marker[1] + 10)])
            dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 245))
            pygame.draw.circle(dark, (0, 0, 0, 0), (int(x), int(y)), beam)
            pygame.draw.circle(dark, (0, 0, 0, 120), (int(x), int(y)), beam, 18)   # soft edge
            c.blit(dark, (0, 0))
            for ex, ey in eyes:                                       # eyes in the dark
                if math.hypot(ex - x, ey - y) > beam and int(elapsed * 2 + ex) % 5:
                    pygame.draw.circle(c, (220, 40, 40), (ex - 6, ey), 3)
                    pygame.draw.circle(c, (220, 40, 40), (ex + 6, ey), 3)
            if view["help"] == "point" and elapsed > 0.8:            # Walt points the way
                angle = math.atan2(marker[1] - y, marker[0] - x)
                tip = (x + 60 * math.cos(angle), y + 60 * math.sin(angle))
                pygame.draw.line(c, COLORS["flashlight"], (x, y), tip, 4)
                pygame.draw.circle(c, COLORS["flashlight"], (int(tip[0]), int(tip[1])), 7)
            timer = pygame.Rect(WIDTH // 2 - 150, 90, 300, 10)
            pygame.draw.rect(c, COLORS["bar_back"], timer, border_radius=4)
            pygame.draw.rect(c, COLORS["flashlight"], (timer.x, timer.y, int(timer.width * (1 - elapsed / limit)), 10),
                             border_radius=4)
            self.hud(c, view, "Flashlight Search")
            w.present()

    # ---- Night B: Lake Crossing
    def lake(self, view):
        w = self.w
        window = LAKE_WINDOW[view["difficulty"]] + (0.35 if view["help"] == "row_with_you" else 0.0)
        hand = self.rng.random() < LAKE_HAND[view["difficulty"]]
        warning = 0.7 if hand and view["help"] == "warn" else 0.0
        wanted = pygame.K_d if hand else (pygame.K_LEFT if self.stroke % 2 == 0 else pygame.K_RIGHT)
        label = "D" if hand else ("<-" if wanted == pygame.K_LEFT else "->")
        start = time.time()
        while True:
            dt = w.tick()
            elapsed = time.time() - start
            live = elapsed - warning - 0.35                           # a short pause, (warning), then the cue
            for event in w.events:
                if event.type != pygame.KEYDOWN or live < 0 or event.key not in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_d):
                    continue
                ok = event.key == wanted
                if ok and not hand:
                    self.stroke += 1
                    self.boat_x += 1
                return self.result(ok, "Pull!" if not hand else "Shook it off!",
                                   "Wrong stroke, the boat lurches!" if not hand else "The hand drags at the boat!")
            if live > window:
                return self.result(False, "", "Too late! The boat drifts." if not hand else "The hand grabs the boat!")
            c = w.canvas
            w.scenery.draw_back(c, 5)
            water_y = GROUND_Y - 30                                   # the lake covers the boardwalk here
            pygame.draw.rect(c, (20, 36, 52), (0, water_y, WIDTH, HEIGHT - water_y))
            for row in range(5):
                for wx in range(0, WIDTH, 60):
                    shift = int(14 * math.sin(elapsed * 2 + wx * 0.05 + row))
                    pygame.draw.line(c, (60, 92, 116), (wx + shift, water_y + 14 + row * 26), (wx + shift + 24, water_y + 14 + row * 26), 2)
            boat_x = 180 + int(560 * view["progress"] / max(1, view["goal"]))
            bob = int(4 * math.sin(elapsed * 3))
            deck = GROUND_Y + 10 + bob
            w.draw_sprite("walt", boat_x - 50, deck - 6)                  # sitting in the boat
            w.draw_sprite("player", boat_x + 10, deck - 6)
            pygame.draw.ellipse(c, (235, 235, 240), (boat_x - 110, deck - 46, 230, 70))   # the swan boat in front
            pygame.draw.ellipse(c, (40, 40, 50), (boat_x - 110, deck - 46, 230, 70), 2)
            pygame.draw.arc(c, (235, 235, 240), (boat_x + 80, deck - 150, 50, 110), math.pi * 0.5, math.pi * 1.5, 12)
            pygame.draw.circle(c, (235, 235, 240), (boat_x + 102, deck - 146), 15)
            pygame.draw.polygon(c, (240, 150, 40), [(boat_x + 88, deck - 148), (boat_x + 70, deck - 142), (boat_x + 88, deck - 138)])
            stroke = (self.stroke % 2) * 2 - 1                                # the oar moves with each stroke
            pygame.draw.line(c, (130, 90, 60), (boat_x + 10, deck - 60), (boat_x + 10 + 50 * stroke, deck + 30), 6)
            if hand and live >= 0:                                    # a drowned hand rises
                rise = min(1.0, live / 0.3)
                hx, base = boat_x - 150, water_y + 30
                pygame.draw.rect(c, (110, 140, 130), (hx, base - int(90 * rise), 20, int(90 * rise)))
                for k in range(4):                                    # grasping fingers
                    pygame.draw.line(c, (110, 140, 130), (hx + 2 + k * 5, base - int(90 * rise)),
                                     (hx - 4 + k * 8, base - int(90 * rise) - 18), 4)
            if warning and elapsed < warning + 0.35:
                draw_text(c, "Walt: HAND, kid! Get ready for D!", w.font_big, COLORS["damage"], WIDTH // 2, 140, center=True)
            if live >= 0:                                             # the cue with a closing ring
                share = max(0.0, 1 - live / window)
                pygame.draw.circle(c, COLORS["charge"], (WIDTH // 2, 210), int(30 + 60 * share), 4)
                draw_text(c, label, w.font_title, COLORS["damage"] if hand else COLORS["text"], WIDTH // 2, 210, center=True)
            self.hud(c, view, "Lake Crossing")
            w.present()

    # ---- Night C: Smoke Escape
    def smoke(self, view):
        w = self.w
        if self.segment_mistake[0] != view["segment"]:
            self.segment_mistake = (view["segment"], False)
        if view["mistakes"] > self.last_mistakes:
            self.segment_mistake = (view["segment"], True)
        self.last_mistakes = view["mistakes"]
        limit = SMOKE_TIME[view["difficulty"]]
        clarity = SMOKE_CLARITY[view["difficulty"]]
        safe = self.rng.choice(("left", "right"))
        shouts = view["help"] == "shout_way" or (view["help"] == "when_asked" and self.segment_mistake[1])
        start = time.time()
        while True:
            w.tick()
            elapsed = time.time() - start
            for event in w.events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    chosen = "left" if event.key == pygame.K_LEFT else "right"
                    return self.result(chosen == safe, "Clear air! Keep going.", "Flames! You burn your arm getting back.")
            if elapsed > limit:
                return self.result(False, "", "The smoke closes in! You stumble out coughing.")
            c = w.canvas
            w.scenery.draw_back(c, 6)
            for side in ("left", "right"):                            # two alleys with smoke
                x = 260 if side == "left" else 700
                is_safe = side == safe
                grey = 150 + int(80 * clarity) if is_safe else 150 - int(110 * clarity)
                for k in range(7):
                    puff = (elapsed * 0.6 + k / 7) % 1.0
                    pygame.draw.circle(c, (grey, grey, grey), (x + int(30 * math.sin(k + elapsed)), GROUND_Y - int(puff * 260)),
                                       30 + int(puff * 30))
                if not is_safe and self.rng.random() < 0.2 + 0.6 * clarity:   # embers in the fire smoke
                    pygame.draw.circle(c, (255, 140, 40), (x + self.rng.randint(-40, 40), GROUND_Y - self.rng.randint(20, 240)), 3)
                pygame.draw.rect(c, (40, 30, 30), (x - 70, GROUND_Y - 280, 140, 280), 6, border_radius=10)
                draw_text(c, "LEFT" if side == "left" else "RIGHT", w.font_big, COLORS["text"], x, GROUND_Y + 30, center=True)
            w.draw_sprite("player", 480, GROUND_Y)
            w.draw_sprite("walt", 400, GROUND_Y)
            if shouts and elapsed > 0.8:
                draw_bubble(c, w.font_small, f"{safe.upper()}, kid! This way!", 400, 250)
            timer = pygame.Rect(WIDTH // 2 - 150, 90, 300, 10)
            pygame.draw.rect(c, COLORS["bar_back"], timer, border_radius=4)
            pygame.draw.rect(c, COLORS["damage"], (timer.x, timer.y, int(timer.width * (1 - elapsed / limit)), 10),
                             border_radius=4)
            self.hud(c, view, "Smoke Escape")
            w.present()
