"""
The three playable activities of the playtest (game/activities.py has the rules): each STEP of an activity
is one short real-time moment in the window, and returns success (True) or a mistake (False). The engine
counts successes, mistakes and the fail budget exactly as for the bots, and Walt steps in between steps.

  Flashlight Search (Night A): move the beam (mouse or arrow keys), press Space when the marker is lit.
  Lake Crossing (Night B):     steer between three lanes (UP / DOWN) to dodge wrecks and hands from the fog.
  Bucket Brigade (Night C):    run along four burning stalls (LEFT / RIGHT), throw water (SPACE) at the fire
                               that flares up before it spreads. (Replaced the Smoke Escape after the pilot.)
  Smoke Escape (not used):      two doors in the burning street: LEFT or RIGHT before the smoke ceiling comes
                               down; the safe door has cool light and thin haze, the other one fire.

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
    "act_flashlight": "Move the light with the MOUSE (or the arrow keys). Find the green EXIT sign. When it is inside your light, press SPACE.",
    "act_lake": "Steer the boat with UP and DOWN. Wrecks and drowned hands drift out of the fog: be in a free lane when they reach you.",
    "act_bucket": "Run with LEFT and RIGHT along the stalls. When a fire flares up, stand in front of it and press SPACE to throw water before it spreads.",
    "act_smoke": "Two doors: press LEFT or RIGHT before the smoke comes down. The safe door has cool light and thin haze; the other one has fire.",
}
FLASH_BEAM = {"easy": 120, "normal": 90, "hard": 76}            # hard 66 -> 76 after the pilot (too hard)
FLASH_TIME = {"easy": 6.0, "normal": 4.5, "hard": 3.9}       # hard 3.3 -> 3.9 after the pilot
FLASH_GLINT = {"easy": 1.0, "normal": 0.5, "hard": 0.0}          # how clearly the sign twinkles through the dark
LAKE_TIME = {"easy": 2.7, "normal": 1.35, "hard": 0.75}          # seconds from the fog edge to the boat
LAKE_FOG_X = {"easy": 860, "normal": 640, "hard": 520}           # where the fog starts (things come out of it)
LAKE_TWO_BLOCKED = {"easy": 0.0, "normal": 0.4, "hard": 0.8}     # chance that two of the three lanes are blocked
LAKE_LANES = (300, 395, 490)                                     # waterline of the top, middle and bottom lane
LANE_NAMES = ("TOP", "MIDDLE", "BOTTOM")
LAKE_WATER_Y = 240
LAKE_BOAT_X = 300
BUCKET_TIME = {"easy": 3.2, "normal": 2.2, "hard": 1.5}          # seconds before the flaring fire spreads
BUCKET_DECOY = {"easy": 0.1, "normal": 0.5, "hard": 0.9}         # how high the other fires burn (hard: alike)
BUCKET_STALLS = (180, 380, 580, 780)                             # x of the four burning stalls
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
        self.puffs = {}                        # smoke: soft puff images, made once
        self.stall = 1                         # bucket: the stall the player stands at (0..3)
        self.runner_x = float(BUCKET_STALLS[1])
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
        self.stall = 1
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
        if view["activity"] == "act_bucket":
            return self.bucket(view)
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
                    return self.result(lit, "Found it! On to the next one.", "Not lit yet! Get the EXIT sign inside your light first.")
            if elapsed > limit:
                return self.result(False, "", "Too slow! A cold hand grabs you in the dark.")
            c = w.canvas
            w.scenery.draw_back(c, 3)
            w.draw_piece(170, 300, True)
            pulse = 0.6 + 0.4 * abs(math.sin(elapsed * 5))           # the target: a glowing EXIT sign
            sign = pygame.Rect(marker[0] - 40, marker[1] - 18, 80, 36)
            pygame.draw.rect(c, (int(60 * pulse), int(170 * pulse), int(80 * pulse)), sign, border_radius=6)
            pygame.draw.rect(c, (230, 255, 230), sign, 2, border_radius=6)
            draw_text(c, "EXIT >", w.font, (240, 255, 240), marker[0], marker[1], center=True)
            dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 245))
            pygame.draw.circle(dark, (0, 0, 0, 0), (int(x), int(y)), beam)
            pygame.draw.circle(dark, (0, 0, 0, 120), (int(x), int(y)), beam, 18)   # soft edge
            c.blit(dark, (0, 0))
            glint = FLASH_GLINT[view["difficulty"]]                   # a green twinkle through the dark
            twinkle = max(0.0, math.sin(elapsed * 4))
            if glint > 0 and not lit and twinkle > 0.3:
                pygame.draw.circle(c, (90, 255, 120), marker, int(2 + 4 * glint * twinkle))
            if lit:                                                   # it is in the light: press now
                ring = 44 + int(6 * math.sin(elapsed * 10))
                pygame.draw.circle(c, COLORS["flashlight"], marker, ring, 3)
                draw_text(c, "SPACE!", w.font_big, COLORS["flashlight"], marker[0], marker[1] - 60, center=True)
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
            draw_text(c, "time", w.font_small, COLORS["dim_text"], timer.x - 40, timer.y - 4)
            self.hud(c, view, "Flashlight Search")
            if not self.message:
                draw_text(c, "Move the light (mouse or arrows). Find the green EXIT sign. When it's lit, press SPACE.",
                          w.font_small, COLORS["text"], WIDTH // 2, HEIGHT - 26, center=True)
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
        """One step = one fork in the burning street: two doors, LEFT or RIGHT. Behind one is clear air, behind
        the other the fire. A ceiling of smoke comes down: choose before it reaches you. Difficulty sets the
        time and how clearly the doors differ (easy: blue light vs. flames; hard: nearly the same grey).
        Output: True = the safe door."""
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
            chosen = None
            for event in w.events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_a):
                    chosen = "left"
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RIGHT, pygame.K_d):
                    chosen = "right"
            if chosen is not None:
                self.run_through(chosen == safe)
                return self.result(chosen == safe, "", "Flames! You burn your arm getting back.", quiet_success=True)
            if elapsed > limit:
                return self.result(False, "", "The smoke closes in! You stumble out coughing.")
            self.draw_smoke_street(elapsed, elapsed / limit, safe, clarity)
            if shouts and elapsed > 0.6:
                draw_bubble(w.canvas, w.font_small, f"{safe.upper()}, kid! This way!", 470, 300)
            self.hud(w.canvas, view, "Smoke Escape")
            if not self.message:
                draw_text(w.canvas, "LEFT or RIGHT: pick the door with clear air", w.font, COLORS["text"],
                          WIDTH // 2, HEIGHT - 30, center=True)
            w.present()

    def draw_smoke_street(self, elapsed, share, safe, clarity):
        """The burning street with two doors and the smoke ceiling coming down (share 0 -> 1)."""
        w = self.w
        c = w.canvas
        w.scenery.draw_back(c, 6)
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((20, 8, 4, 120))
        c.blit(shade, (0, 0))
        pygame.draw.rect(c, (62, 44, 40), (150, 120, WIDTH - 300, GROUND_Y - 120))          # the building front
        for row in range(120, GROUND_Y, 22):                                              # bricks
            pygame.draw.line(c, (48, 34, 30), (150, row), (WIDTH - 150, row), 2)
        pygame.draw.rect(c, (40, 30, 26), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))        # the street
        for side in ("left", "right"):
            x = 300 if side == "left" else 660
            self.draw_door(c, x, side == safe, clarity, elapsed)
            key = "<  LEFT" if side == "left" else "RIGHT  >"
            draw_text(c, key, w.font_big, COLORS["text"], x, GROUND_Y + 28, center=True)
        for k in range(14):                                                               # embers rising
            ex = (k * 71 + int(elapsed * 30)) % WIDTH
            ey = HEIGHT - int((elapsed * 90 + k * 47) % (HEIGHT - 60))
            pygame.draw.circle(c, (255, 150, 60), (ex, ey), 2)
        w.draw_sprite("walt", 440, HEIGHT - 50)
        w.draw_sprite("player", 520, HEIGHT - 50)
        ceiling = 40 + int((GROUND_Y - 40) * share)                                        # the smoke comes down
        smoke = pygame.Surface((WIDTH, ceiling), pygame.SRCALPHA)
        smoke.fill((34, 30, 30, 215))
        c.blit(smoke, (0, 0))
        for k in range(16):                                                               # its soft lower edge
            px = k * 64 + int(14 * math.sin(elapsed * 2 + k))
            c.blit(self.puff((50, 44, 44), 120), (px - 60, ceiling - 60))

    def draw_door(self, c, x, is_safe, clarity, elapsed):
        """One doorway. Safe: cool light and thin pale haze. Fire: an orange glow, flames and dark smoke;
        the lower the clarity, the more alike the two doors look."""
        door = pygame.Rect(x - 80, GROUND_Y - 220, 160, 220)
        if is_safe:
            inside = (int(40 + 30 * clarity), int(50 + 40 * clarity), int(60 + 70 * clarity))
        else:
            flicker = 0.85 + 0.15 * math.sin(elapsed * 9 + x)
            inside = (int((60 + 160 * clarity) * flicker), int((48 + 50 * clarity) * flicker), 40)
        pygame.draw.rect(c, inside, door, border_top_left_radius=70, border_top_right_radius=70)
        if not is_safe:
            for k in range(1 + int(6 * clarity)):                                         # flames inside
                fx = door.x + 20 + k * 22
                height = int(30 + 40 * clarity * abs(math.sin(elapsed * 6 + k * 1.3)))
                pygame.draw.polygon(c, (255, 140 + (k % 2) * 60, 40),
                                    [(fx - 10, door.bottom), (fx + 10, door.bottom), (fx, door.bottom - height)])
        grey = int(140 + 70 * clarity) if is_safe else int(140 - 90 * clarity)          # smoke out of the door
        for k in range(5):
            rise = (elapsed * 0.5 + k / 5) % 1.0
            c.blit(self.puff((grey, grey, grey), 110),
                   (x - 55 + int(20 * math.sin(k + elapsed)), door.y + 60 - int(rise * 160)))
        pygame.draw.rect(c, (30, 20, 18), door, 8, border_top_left_radius=70, border_top_right_radius=70)

    def puff(self, color, size):
        """A soft round smoke puff (see-through towards the edge), made once per colour and size."""
        key = (color, size)
        if key not in self.puffs:
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            for k in range(10):                                   # outer rings first, each one more solid
                radius = int(size / 2 * (1 - k / 10))
                pygame.draw.circle(surface, (*color, 10 + k * 10), (size // 2, size // 2), radius)
            self.puffs[key] = surface
        return self.puffs[key]

    def run_through(self, safe):
        """After a choice: a short fade, as if running through the door (clear air or into the flames)."""
        w = self.w
        colour = (0, 0, 0) if safe else (120, 40, 10)
        start = time.time()
        while time.time() - start < 0.3:
            w.tick()
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((*colour, int(255 * (time.time() - start) / 0.3)))
            w.canvas.blit(veil, (0, 0))
            w.present()

    # ---- Night C: Bucket Brigade
    def bucket(self, view):
        """One step = one fire flaring up in one of four burning stalls. The player runs left / right along
        the stalls and throws water (SPACE) at the flaring one before it spreads. Difficulty: less time, and
        the other fires burn almost as high (harder to see which one flares). Help 'point_fire': Walt points
        at it. Help 'throw_too': Walt throws as well (the engine may count a miss as his hit).
        Output: True = the flaring fire was put out in time."""
        w = self.w
        limit = BUCKET_TIME[view["difficulty"]]
        decoy = BUCKET_DECOY[view["difficulty"]]                 # how high the other fires burn (0..1)
        others = [stall for stall in range(4) if stall != self.stall]
        flaring = self.rng.choice(others)                        # never right in front of the player
        start = time.time()
        while True:
            dt = w.tick()
            elapsed = time.time() - start
            for event in w.events:
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.stall = max(0, self.stall - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.stall = min(3, self.stall + 1)
                if event.key == pygame.K_SPACE:
                    hit = self.stall == flaring
                    self.throw_water(flaring, decoy, elapsed / limit, hit)
                    return self.result(hit, "", "Wrong stall! The fire jumps to the next roof.", quiet_success=True)
            if elapsed > limit:
                return self.result(False, "", "Too slow! The fire spreads.")
            target_x = BUCKET_STALLS[self.stall]
            self.runner_x += (target_x - self.runner_x) * min(1.0, dt * 16)    # run to the stall
            self.draw_stalls(elapsed, flaring, decoy, elapsed / limit, view)
            self.hud(w.canvas, view, "Bucket Brigade")
            if not self.message:
                draw_text(w.canvas, "LEFT / RIGHT to run, SPACE to throw at the fire that flares up", w.font,
                          COLORS["text"], WIDTH // 2, HEIGHT - 26, center=True)
            w.present()

    def draw_stalls(self, elapsed, flaring, decoy, share, view, splash=None):
        """Main Street in June 1987: four burning stalls, one fire flaring (share 0 -> 1 = about to spread)."""
        w = self.w
        c = w.canvas
        w.scenery.draw_back(c, 6)
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((20, 8, 4, 110))
        c.blit(shade, (0, 0))
        pygame.draw.rect(c, (40, 30, 26), (0, GROUND_Y + 20, WIDTH, HEIGHT - GROUND_Y - 20))       # the street
        for stall, x in enumerate(BUCKET_STALLS):
            pygame.draw.rect(c, (70, 50, 44), (x - 70, GROUND_Y - 120, 140, 140))                   # the stall
            for k in range(5):                                                                     # its awning
                colour = (150, 50, 40) if k % 2 == 0 else (200, 190, 170)
                pygame.draw.rect(c, colour, (x - 76 + k * 30, GROUND_Y - 140, 30, 24))
            if stall == flaring:
                size = 0.55 + 0.45 * share                       # grows until it spreads
            else:
                size = 0.25 + 0.35 * decoy * (0.8 + 0.2 * math.sin(elapsed * 3 + stall))
            if splash is not None and stall == splash:
                size = max(0.1, size * 0.3)                      # just doused
            self.draw_fire(c, x, GROUND_Y - 140, size, elapsed + stall)
            if stall == flaring and decoy < 0.6:                 # easy / normal: a heat meter shows which one
                pygame.draw.rect(c, COLORS["bar_back"], (x - 40, GROUND_Y - 250, 80, 8), border_radius=3)
                pygame.draw.rect(c, COLORS["damage"], (x - 40, GROUND_Y - 250, int(80 * share), 8), border_radius=3)
        if view["help"] == "point_fire" and elapsed > 0.4:      # Walt points at the flaring fire
            fx = BUCKET_STALLS[flaring]
            bounce = int(6 * math.sin(elapsed * 8))
            pygame.draw.polygon(c, COLORS["flashlight"], [(fx - 14, 110 + bounce), (fx + 14, 110 + bounce), (fx, 132 + bounce)])
        walt_x = 60 if self.runner_x > 200 else WIDTH - 60
        w.draw_sprite("walt", walt_x, HEIGHT - 40)
        if view["help"] == "throw_too":                          # Walt with his own bucket
            pygame.draw.rect(c, (120, 120, 130), (walt_x + 18, HEIGHT - 80, 18, 20))
        w.draw_sprite("player", int(self.runner_x), HEIGHT - 40)
        pygame.draw.rect(c, (120, 120, 130), (int(self.runner_x) + 18, HEIGHT - 80, 18, 20))      # the bucket

    def draw_fire(self, c, x, y_bottom, size, t):
        """Flames on a roof: size 0..1 sets how high and wide they burn."""
        count = 3 + int(5 * size)
        for k in range(count):
            fx = x - 60 + int(120 * (k + 0.5) / count)
            height = int((30 + 110 * size) * (0.75 + 0.25 * abs(math.sin(t * 7 + k * 1.7))))
            pygame.draw.polygon(c, (255, 120 + (k % 3) * 45, 30),
                                [(fx - 13, y_bottom), (fx + 13, y_bottom), (fx, y_bottom - height)])
        if size > 0.5:
            glow = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 140, 40, int(70 * size)), (100, 100), 90)
            c.blit(glow, (x - 100, y_bottom - 150))

    def throw_water(self, flaring, decoy, share, hit):
        """The water flies from the bucket to the stall (0.3 s); a hit puts that fire down."""
        w = self.w
        start = time.time()
        x0, y0 = self.runner_x + 26, HEIGHT - 80
        x1, y1 = BUCKET_STALLS[self.stall], GROUND_Y - 160
        while time.time() - start < 0.3:
            w.tick()
            p = (time.time() - start) / 0.3
            self.draw_stalls(time.time(), flaring, decoy, share, {"help": None}, splash=self.stall if hit and p > 0.7 else None)
            for k in range(8):                                   # a curved splash of water
                q = max(0.0, p - k * 0.03)
                x = x0 + (x1 - x0) * q
                y = y0 + (y1 - y0) * q - 120 * math.sin(math.pi * q)
                pygame.draw.circle(w.canvas, (120, 180, 255), (int(x), int(y)), 6 - k // 2)
            w.present()
