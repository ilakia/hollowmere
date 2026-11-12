"""
The three playable activities of the playtest (game/activities.py has the rules): each STEP of an activity
is one short real-time moment in the window, and returns success (True) or a mistake (False). The engine
counts successes, mistakes and the fail budget exactly as for the bots, and Walt steps in between steps.

  Flashlight Search (Night A): move the beam (mouse or arrow keys), press Space when the marker is lit.
  Lake Crossing (Night B):     steer between three lanes (UP / DOWN) to dodge wrecks and hands from the fog.
  Smoke Escape (Night C):      choose the left or right way (arrow keys) before the smoke closes in;
                               the safe way has lighter smoke and no flames.

Walt's settings change the mini-game itself:
  difficulty -> beam size / time window / timer / how clear the clues are
  help       -> point (an arrow to the marker), hold_light (bigger beam), warn (Walt calls the free lane),
                row_with_you (everything comes slower), steer (forgives a slip, in the engine), shout_way (Walt calls
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
    "act_lake": "Steer the boat with UP and DOWN. Wrecks and drowned hands drift out of the fog: be in a free lane when they reach you.",
    "act_smoke": "Pick a way with LEFT or RIGHT before the smoke closes in. Safe smoke is lighter; fire smoke is black, with embers.",
}
FLASH_BEAM = {"easy": 120, "normal": 90, "hard": 66}
FLASH_TIME = {"easy": 6.0, "normal": 4.5, "hard": 3.3}
LAKE_TIME = {"easy": 2.7, "normal": 1.35, "hard": 0.75}          # seconds from the fog edge to the boat
LAKE_FOG_X = {"easy": 860, "normal": 640, "hard": 520}           # where the fog starts (things come out of it)
LAKE_TWO_BLOCKED = {"easy": 0.0, "normal": 0.4, "hard": 0.8}     # chance that two of the three lanes are blocked
LAKE_LANES = (300, 395, 490)                                     # waterline of the top, middle and bottom lane
LANE_NAMES = ("TOP", "MIDDLE", "BOTTOM")
LAKE_WATER_Y = 240
LAKE_BOAT_X = 300
SMOKE_TIME = {"easy": 6.0, "normal": 4.2, "hard": 2.8}
SMOKE_CLARITY = {"easy": 1.0, "normal": 0.55, "hard": 0.25}     # 1 = black vs white smoke, 0 = the same grey
DEMO_SUCCESS = 0.7
PRACTICE_STEPS = 3                 # practice steps before each activity (not counted)


class ActivityRunner:
    """Runs one step of the current activity in the window. Output of step(): True = success."""

    def __init__(self, window):
        self.w = window
        self.rng = random.Random()
        self.lane = 1                          # lake: the boat's lane (0 top, 1 middle, 2 bottom)
        self.boat_y = float(LAKE_LANES[1])
        self.scroll = 0.0
        self.passing = []                      # lake: [kind, lane, x] of wrecks / hands already passed
        self.segment_mistake = (None, False)   # smoke: (segment, a mistake happened in it)
        self.last_mistakes = 0
        self.message = ""

    # ---- shared pieces
    def hud(self, c, view, title):
        """Top line: the activity, progress and the fail budget as a meter."""
        w = self.w
        w.draw_top_bar(c)
        if view.get("practice"):
            title = "Practice - " + title
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

    def result(self, success, text_ok, text_bad, quiet_success=False):
        w = self.w
        if not success:
            w.sounds.play("hurt")
        elif not quiet_success:                    # the lake: dodging is silent, so the crossing flows
            w.sounds.play("hit")
        self.message = text_ok if success else text_bad
        if not success:
            w.shake.start(6, 0.25)
        return success

    def practice(self, activity):
        """A short practice before the real activity, the same for every Walt version: PRACTICE_STEPS steps
        at the easy setting with no help.
        Nothing is counted or saved. Skipped in demo mode."""
        if self.w.demo_dir is not None:
            return
        mistakes = 0
        for i in range(PRACTICE_STEPS):
            view = {"activity": activity, "difficulty": "easy", "help": None, "progress": i, "goal": PRACTICE_STEPS,
                    "mistakes": mistakes, "budget": PRACTICE_STEPS, "segment": -1, "practice": True}
            if not self.step(view, self.rng):
                mistakes += 1
            pause = time.time()
            while time.time() - pause < 0.6:              # a moment to read "Pull!" / "Too late!"
                self.w.tick()
                draw_text(self.w.canvas, self.message, self.w.font, COLORS["text"], WIDTH // 2, HEIGHT - 40, center=True)
                self.w.present()
        self.lane = 1                                     # the real activity starts fresh
        self.passing = []
        self.segment_mistake = (None, False)
        self.last_mistakes = 0
        self.message = ""

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
        """One step = one wreck or drowned hand drifting out of the fog. The player steers the boat between
        three lanes (UP / DOWN) and must be in a free lane when it arrives. The lane the boat is in is always
        blocked, so every step needs a move. Output: True = dodged."""
        w = self.w
        travel = LAKE_TIME[view["difficulty"]] * (1.3 if view["help"] == "row_with_you" else 1.0)
        fog_x = LAKE_FOG_X[view["difficulty"]]
        blocked = [self.lane]
        if self.rng.random() < LAKE_TWO_BLOCKED[view["difficulty"]]:
            others = [lane for lane in range(3) if lane != self.lane]
            blocked.append(self.rng.choice(others))
        free = [lane for lane in range(3) if lane not in blocked]
        call = min(free, key=lambda lane: abs(lane - self.lane))       # the free lane Walt calls (the closest)
        kinds = {}
        for lane in blocked:
            kinds[lane] = "hand" if self.rng.random() < 0.4 else "wreck"
        start_x = fog_x + 30                                          # comes straight out of the fog: no gap
        speed = (start_x - LAKE_BOAT_X) / travel
        start = time.time()
        while True:
            dt = w.tick()
            elapsed = time.time() - start
            self.scroll += dt * 140
            for event in w.events:                                    # steering
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.lane = max(0, self.lane - 1)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.lane = min(2, self.lane + 1)
            target_y = LAKE_LANES[self.lane]
            self.boat_y += (target_y - self.boat_y) * min(1.0, dt * 14)  # glide to the new lane
            for thing in self.passing:                                # earlier ones drift on past the boat
                thing[2] -= speed * dt
            self.passing = [thing for thing in self.passing if thing[2] > -120]
            share = elapsed / travel
            if share >= 1.0:                                          # it reaches the boat
                hit = self.lane in blocked
                kind = kinds.get(self.lane, "wreck")
                for lane in blocked:
                    if not (hit and lane == self.lane):               # what hit the boat sinks; the rest drift on
                        self.passing.append([kinds[lane], lane, LAKE_BOAT_X])
                return self.result(not hit, "", "A hand grabs the boat!" if kind == "hand" else
                                   "Crash! The boat hits a wreck.", quiet_success=True)
            x = start_x - (start_x - LAKE_BOAT_X) * share
            c = w.canvas
            w.scenery.draw_back(c, 5)
            pygame.draw.rect(c, (20, 36, 52), (0, LAKE_WATER_Y, WIDTH, HEIGHT - LAKE_WATER_Y))
            for lane_y in LAKE_LANES:                                 # moving ripples: the boat is sailing
                for wx in range(-60, WIDTH + 60, 70):
                    rx = (wx - int(self.scroll)) % (WIDTH + 120) - 60
                    pygame.draw.line(c, (60, 92, 116), (rx, lane_y + 12), (rx + 26, lane_y + 12), 2)
            for rope_y in (347, 442):                                 # rope lines with buoys between the lanes
                pygame.draw.line(c, (120, 100, 80), (0, rope_y), (WIDTH, rope_y), 2)
                for bx in range(-40, WIDTH + 40, 80):
                    buoy_x = (bx - int(self.scroll)) % (WIDTH + 80) - 40
                    pygame.draw.circle(c, (200, 70, 60), (buoy_x, rope_y), 6)
            for kind, lane, px in self.passing:
                self.draw_lake_thing(c, kind, int(px), LAKE_LANES[lane], elapsed)
            for lane in blocked:                                      # what drifts at you
                self.draw_lake_thing(c, kinds[lane], int(x), LAKE_LANES[lane], elapsed)
            fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for k in range(14):                                       # the fog bank: soft at the edge, thick behind
                edge = int(fog_x - 40 + k * 18)                       # (each strip has its own alpha: drawing on
                width = 18 if k < 13 else WIDTH                       #  an alpha surface replaces, it doesn't add)
                pygame.draw.rect(fog, (150, 162, 175, 30 + k * 15), (edge, LAKE_WATER_Y - 70, width, HEIGHT))
            for k in range(18):                                       # drifting puffs along the edge
                py = LAKE_WATER_Y - 40 + (k * 37) % (HEIGHT - LAKE_WATER_Y + 20)
                px = int(fog_x - 30 + 25 * math.sin(elapsed * 1.5 + k))
                pygame.draw.circle(fog, (160, 172, 185, 45), (px, py), 46)
            c.blit(fog, (0, 0))
            if view["help"] == "warn":                                # Walt calls the free lane early
                pygame.draw.circle(c, COLORS["flashlight"], (LAKE_BOAT_X + 150, LAKE_LANES[call] - 20), 12)
                draw_bubble(c, w.font_small, f"{LANE_NAMES[call]} lane, kid!", 200, 150)
            self.draw_swan_boat(c, LAKE_BOAT_X, int(self.boat_y + 3 * math.sin(elapsed * 3)))
            self.hud(c, view, "Lake Crossing")
            if not self.message:
                draw_text(c, "UP / DOWN to steer", w.font, COLORS["dim_text"], WIDTH // 2, HEIGHT - 40, center=True)
            w.present()

    def draw_swan_boat(self, c, x, y):
        """The swan boat with Walt and the player in it; y = the waterline."""
        self.w.draw_sprite("walt", x - 35, y - 4)
        self.w.draw_sprite("player", x + 20, y - 4)
        pygame.draw.ellipse(c, (235, 235, 240), (x - 90, y - 34, 180, 50))
        pygame.draw.ellipse(c, (40, 40, 50), (x - 90, y - 34, 180, 50), 2)
        pygame.draw.arc(c, (235, 235, 240), (x + 62, y - 120, 40, 90), math.pi * 0.5, math.pi * 1.5, 10)
        pygame.draw.circle(c, (235, 235, 240), (x + 80, y - 117), 12)
        pygame.draw.polygon(c, (240, 150, 40), [(x + 70, y - 120), (x + 54, y - 115), (x + 70, y - 111)])

    def draw_lake_thing(self, c, kind, x, y, elapsed):
        """A drowned hand reaching up, or a broken old boat, in a lane at x."""
        if kind == "hand":
            sway = int(4 * math.sin(elapsed * 6))
            pygame.draw.rect(c, (110, 140, 130), (x - 10 + sway, y - 52, 20, 58))
            for k in range(4):                                        # grasping fingers
                pygame.draw.line(c, (110, 140, 130), (x - 8 + k * 5 + sway, y - 52), (x - 14 + k * 9 + sway, y - 70), 4)
        else:
            pygame.draw.polygon(c, (92, 64, 44), [(x - 50, y - 26), (x + 46, y - 34), (x + 36, y + 6), (x - 40, y + 6)])
            pygame.draw.line(c, (60, 40, 28), (x - 30, y - 28), (x - 6, y - 70), 6)              # a broken mast
            pygame.draw.line(c, (140, 110, 80), (x - 46, y - 12), (x + 40, y - 18), 3)
        pygame.draw.ellipse(c, (90, 120, 140), (x - 40, y - 2, 80, 12), 2)                     # ripple ring

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
