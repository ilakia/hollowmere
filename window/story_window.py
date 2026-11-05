"""
Study 2 in the game window: the story mode "Night of the Fire".

It reuses the normal window (walking, fights, voice, flashback) and only adds what is new:
- the victims on screen (names only once Walt has said who they are),
- their tells (the music stops, the camera goes up, the ghost train passes, the lights flicker),
- the story-mode actions: L Shine (flashlight), N Call a name, and choosing which twin to hit,
- Walt's words about each victim: silent Walt says nothing useful, scripted Walt tells the backstory.
The rules of the fights are in game/victims.py; the night itself in game/story_mode.py.
"""
import math
import threading
import time

import pygame

import play_window as PW
from game import config as C
from game.chapters import (FIRE_GLOW_PER_ROOM, KEEPSAKE_BY_ID, KEEPSAKES, NIGHT_STORY, NIGHT_ZONE, ROOM_SKINS,
                           keepsake_for_room)
from window.scenery import ZONE_MOODS
from game.profiles import load_profile, update_profile
from game.story_mode import BRAINS, play_night
from game.victims import BENNY_MUSIC_TURNS, NIGHTS, VICTIMS
from window.art import COLORS, HEIGHT, WIDTH, Button, draw_text

GROUND_Y = PW.GROUND_Y
VICTIM_SPRITE = {"martha": "martha", "benny": "benny", "rosa": "rosa", "henry": "henry", "twins": "lily",
                 "ned": "ned"}
SPRITE_VICTIM = {"martha": "martha", "benny": "benny", "rosa": "rosa", "henry": "henry", "lily": "twins",
                 "lily_reflection": "twins", "ned": "ned"}
SILENT_LINE = "Careful, kid. Something's here."
FINALE_NAMES = {"smoke": "The Smoke", "blaze": "The Blaze"}
for _skins in ROOM_SKINS.values():                    # the short story shown while walking to each new place
    for _piece, _title, _story in _skins.values():
        PW.PLACE_STORIES[_piece] = _story


def draw_music_box(c, w, x, y, playing, turns_left=0):
    """Benny's music box on the ground: the key turns and notes float up while it plays; when it runs
    down the lid drops, the key stops and the notes are gone."""
    box = pygame.Rect(x - 34, y - 34, 68, 34)
    pygame.draw.rect(c, (110, 70, 40), box, border_radius=4)
    pygame.draw.rect(c, (215, 175, 80), box, 2, border_radius=4)
    lid_open = 22 if playing else 0
    pygame.draw.polygon(c, (130, 85, 50), [(box.x, box.y), (box.right, box.y),
                                           (box.right - 6, box.y - lid_open), (box.x + 6, box.y - lid_open)])
    if playing:                                                     # a tiny dancer turning on top
        turn = math.sin(time.time() * 6)
        pygame.draw.line(c, (250, 220, 230), (x, box.y - 4), (x + int(6 * turn), box.y - 20), 3)
        for i in range(3):                                          # notes floating up
            phase = (time.time() * 0.8 + i / 3) % 1.0
            nx = x + 30 + int(14 * math.sin(phase * 6 + i))
            ny = box.y - 10 - int(phase * 60)
            pygame.draw.circle(c, (255, 230, 150), (nx, ny), 4)
            pygame.draw.line(c, (255, 230, 150), (nx + 4, ny), (nx + 4, ny - 12), 2)
    key_angle = time.time() * 3 * turns_left if playing else 0.0    # the key slows down as it runs down
    kx, ky = box.right + 8, box.centery
    pygame.draw.line(c, (200, 200, 210), (box.right, ky), (kx, ky), 3)
    for side in (-1, 1):
        pygame.draw.line(c, (200, 200, 210), (kx, ky),
                         (kx + int(10 * math.cos(key_angle) * side), ky + int(10 * math.sin(key_angle) * side)), 4)
    if playing:                                                     # how long until it runs down
        label = "runs down next turn!" if turns_left == 1 else f"runs down in {turns_left} turns"
        color = COLORS["charge"] if turns_left == 1 else COLORS["dim_text"]
    else:
        label, color = "silent", COLORS["charge"]
    draw_text(c, label, w.font_small, color, x, y + 14, center=True)


class StoryPolicy(PW.WindowPolicy):
    """The human player in story mode: the normal fight screen plus the victims' tells and actions."""

    def __init__(self, window, names_known):
        super().__init__(window)
        self.names_known = names_known      # victims whose names Walt has told (so the label can show them)
        self.coach = None                   # Walt's hint coach in the current victim fight (set by the narrator)
        self.finale_enemy = None            # Night B / C: what Walt and the player fight at the gate
        self.help_asks = 0                  # "Walt, help!" presses in the current room

    def choose_action(self, view, rng):
        """Walt's hint ladder: a new hint line (view["walt_line"]) is spoken before the player chooses."""
        if view.get("walt_line"):
            self.window.speak(view["walt_line"])
        return super().choose_action(view, rng)

    def on_help(self, view):
        """"Walt, help!" (victim fights): Walt's coach answers (silent: '...', scripted: the next fixed hint,
        LLM: his own decision). Costs no turn. Counted for the study."""
        self.help_asks += 1
        coach = self.coach
        if coach is None:
            return
        fight = {"turn": view.get("turn", 1), "weakness_used": view.get("weakness_used", False),
                 "hp_share": view["hp"] / view["max_hp"], "tried": view.get("tried", {})}
        level, line = coach.ask_help(fight)
        self.window.bubble = ""
        self.window.speak(line)

    def take_help_asks(self):
        count, self.help_asks = self.help_asks, 0
        return count

    def display_ghosts(self, view):
        if not view.get("victim"):
            if self.finale_enemy:                                # same fight as Walt's, shown as the fire
                return [(self.finale_enemy if kind == "walt" else kind, hp) for kind, hp in view["enemies"]]
            return view["enemies"]
        if view.get("targets"):              # Lily and her reflection
            return [("lily" if side == "real" else "lily_reflection",
                     view["victim_hp"] if side == "real" else view["victim_max_hp"]) for side in view["targets"]]
        return [(VICTIM_SPRITE[view["victim"]], view["victim_hp"])]

    def full_hp(self, kind, view, hp_mult):
        if view.get("victim"):
            return view["victim_max_hp"]
        if kind in FINALE_NAMES:
            return C.ENEMY_TYPES["walt"]["hp"] * hp_mult
        return super().full_hp(kind, view, hp_mult)

    def ghost_label(self, kind):
        if kind in FINALE_NAMES:
            return FINALE_NAMES[kind]
        victim = SPRITE_VICTIM.get(kind)
        if victim is None:
            return kind
        if victim in self.names_known:
            return VICTIMS[victim]["name"].split()[0]
        return "???"

    def draw_cues(self, c, view, ghost_marks):
        """The tells: what a watchful player can see this turn. Also: LLM Walt's late answers are spoken
        the moment they arrive (the fight never waits for him)."""
        w = self.window
        if self.coach is not None:
            line = self.coach.poll()
            if line:
                w.bubble = ""
                w.speak(line)
        cue = view.get("cue")
        victim = view.get("victim")
        if not victim:
            return
        x = ghost_marks[0][2] if ghost_marks else 730
        if victim == "benny":
            stopped = cue == "music_stopped"
            w.sounds.carousel_music(playing=not stopped)             # the waltz plays / goes silent
            period = BENNY_MUSIC_TURNS                                 # the music stops every 2nd turn
            turns_left = period - view.get("turn", 1) % period
            draw_music_box(c, w, 470, GROUND_Y + 2, playing=not stopped, turns_left=turns_left)
            if stopped:
                draw_text(c, "The music box runs down... silence. Benny stands still.", w.font_big,
                          COLORS["charge"], WIDTH // 2, 62, center=True)
            else:
                for i in range(3):                                   # motion lines: the ride keeps spinning
                    a = time.time() * 8 + i * 2.1
                    pygame.draw.arc(c, (220, 220, 255), (x - 60, GROUND_Y - 150 + i * 30, 120, 40),
                                    a % 6.28, a % 6.28 + 1.6, 3)
                draw_text(c, "The music box plays... the carousel spins, Benny with it.", w.font,
                          COLORS["dim_text"], WIDTH // 2, 62, center=True)
        if victim == "rosa" and cue == "camera_up":
            PW.draw_glow(c, x + 20, GROUND_Y - 80, 70, (255, 255, 220), strength=60)
            draw_text(c, "Rosa lifts her camera...", w.font_big, COLORS["charge"], WIDTH // 2, 62, center=True)
        if victim == "ned" and cue == "whistle":
            speed = (time.time() * 900) % (WIDTH + 400)              # the ghost train rushes past
            train_x = int(speed) - 300
            for car in range(4):
                car_x = train_x - car * 110
                pygame.draw.rect(c, (150, 25, 40), (car_x, GROUND_Y - 60, 100, 46), border_radius=8)
                pygame.draw.circle(c, (90, 90, 100), (car_x + 20, GROUND_Y - 12), 10)
                pygame.draw.circle(c, (90, 90, 100), (car_x + 80, GROUND_Y - 12), 10)
            draw_text(c, "WHOOO! The ghost train comes past, Ned at the front!", w.font_big, COLORS["charge"],
                      WIDTH // 2, 62, center=True)
        if victim == "martha" and cue == "lights_flicker":
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 90 if int(time.time() * 10) % 2 else 30))
            c.blit(dim, (0, 0))
            draw_text(c, "The lights flicker... Martha grows taller in the dark.", w.font, COLORS["dim_text"],
                      WIDTH // 2, 62, center=True)
        if view.get("stunned"):
            word = "calm... (for now)" if victim == "henry" else "frozen!"
            draw_text(c, word, w.font_big, (200, 230, 255), x, GROUND_Y - 170, center=True)
        if view.get("blind"):
            haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            haze.fill((255, 255, 240, 120))
            c.blit(haze, (0, 0))
            draw_text(c, "Blinded by the flash! You can't see!", w.font_big, COLORS["damage"], WIDTH // 2, 440, center=True)
        if victim == "henry" and not view.get("stunned") and int(time.time()) % 4 == 0:
            PW.draw_bubble(c, w.font_small, "WHO AM I?! SAY MY NAME!", x, 230)

    def extra_buttons(self, view, buttons):
        """Victim rooms get two more buttons: L Shine and N Call a name (same row, a bit narrower)."""
        if not view.get("victim"):
            return buttons
        names = {b.name: b for b in buttons}
        row = [names["attack"], names["defend"], names["potion"],
               Button("shine", "L  Shine", (0, 0, 1, 1), [pygame.K_l]),
               Button("call", "N  Call name", (0, 0, 1, 1), [pygame.K_n]),
               Button("help", "H  Help!", (0, 0, 1, 1), [pygame.K_h])]
        if "rest" in names:
            row.append(names["rest"])
        width = (WIDTH - 20 - 8 * (len(row) - 1)) // len(row)
        for i, button in enumerate(row):
            button.rect = pygame.Rect(10 + i * (width + 8), 470, width, 50)
        return row

    def resolve_action(self, action, draw_scene, view):
        w = self.window
        if action == "call":
            choices = VICTIMS["henry"]["name_choices"]
            buttons = [Button(f"call:{name}", f"{i + 1}  {name}", (110 + i * 250, 300, 240, 50), [pygame.K_1 + i])
                       for i, name in enumerate(choices)]

            def ask(dt):
                draw_scene(dt)
                draw_text(w.canvas, "Call out a name:", w.font_big, COLORS["text"], WIDTH // 2, 260, center=True)
            if w.demo_dir is not None:
                w.demo_choice = buttons[0].name
            return w.wait_for(ask, buttons)
        if action == "attack" and view.get("targets") and len(view["targets"]) > 1:
            buttons = [Button(f"attack:{i}", f"{i + 1}  this one", (PW.ghost_x(i, 2) - 80, 300, 160, 46), [pygame.K_1 + i])
                       for i in range(2)]

            def ask(dt):
                draw_scene(dt)
                draw_text(w.canvas, "Which Lily do you strike?", w.font_big, COLORS["text"], WIDTH // 2, 250, center=True)
            if w.demo_dir is not None:
                w.demo_choice = buttons[0].name
            return w.wait_for(ask, buttons)
        return action


class StoryNarrator(PW.WindowNarrator):
    """Shows a story-mode night: zone cards, walking, the victims appearing, Walt's words, the result."""
    background_llm = True                    # play_night: LLM calls run in the background, never freeze

    def __init__(self, story, window, policy, brain_name, night):
        super().__init__(None, story, window, policy)
        self.brain_name = brain_name
        self.night = night
        self.room_titles = []
        self.chapter = NIGHT_STORY[night]
        self.keepsakes = []                  # Night B: ids of the keepsakes picked up tonight
        self.keepsakes_before = []           # Night C: keepsakes found in Night B (from the player's profile)
        self.keepsake_state = None           # the keepsake on the current walk: None, "lying", "taken"
        self.job = None                      # Walt's decision for the current room (made while walking)
        self.applied = True

    def before_room_deciding(self, state, info, job):
        """Zone card and walk while Walt decides (job). His decision is applied the moment it is ready; the
        ghosts only wait at the end of the walk if it is still not ready. Output: the decision."""
        self.job, self.applied = job, False
        self.before_room(state, info)
        return job.result

    def apply_decision(self, state):
        """Walt's decision has arrived: set difficulty and help, and let him say his line."""
        w = self.window
        self.applied = True
        w.difficulty = state["difficulty"]                       # chosen by Walt's brain, never shown
        w.help_mode = state["help_mode"] if not self.walt_is_enemy(state) else None
        if state["is_finale"]:
            return                                               # at the gate the story lines speak
        if state.get("walt_say"):                                # LLM Walt's own sentence
            w.speak(state["walt_say"])
        elif w.help_mode != self.last_mode:                      # scripted/silent: explain a new behaviour
            w.speak(PW.WALT_BUBBLE.get(w.help_mode, ""))
        self.last_mode = w.help_mode

    def walk_tick(self, state):
        if not self.applied and self.job.done():
            self.apply_decision(state)

    def ready_to_appear(self, state):
        return self.applied

    def walt_is_enemy(self, state):
        return state["walt_is_enemy"]

    def travel_line(self, state):
        lines = self.chapter["travel_lines"]
        return lines[state["room_index"] % len(lines)]

    def before_room(self, state, info):
        w = self.window
        beat = self.story.get(info["beat_id"])
        skin = ROOM_SKINS.get(self.night, {}).get(info["beat_id"])       # Night B / C: a new place
        place_zone = NIGHT_ZONE.get(self.night, state["zone"])
        zone = ZONE_MOODS[place_zone]["name"]
        w.room_label = f"Night {self.night}  ·  Room {state['room_index'] + 1}/{state['rooms']}  ·  {zone}"
        if self.chapter["fire"]:
            w.fire_level = FIRE_GLOW_PER_ROOM * (state["room_index"] + 1)     # the park burns a bit more
        self.walk_keepsake = keepsake_for_room(self.night, state["room_index"])
        self.keepsake_state = "lying" if self.walk_keepsake else None
        w.is_finale = self.walt_is_enemy(state)                  # B / C: Walt stays at your side at the gate
        w.zone = place_zone
        w.help_mode = self.last_mode                             # unknown until Walt has decided
        if state["zone"] != self.zone_seen:
            if skin is None:                                     # Night A: the park map card per zone
                self.zone_card(state, beat)
            self.zone_seen = state["zone"]
            self.zone_titles = []
            w.scenery.world_x = 0.0
        shown = dict(beat)
        if skin is not None:
            shown["id"], shown["title"] = skin[0], skin[1]
        victim = info["victim"]
        if victim == "twins":
            shown["enemies"] = ["lily", "lily_reflection"]
        elif victim:
            shown["enemies"] = [VICTIM_SPRITE[victim]]
        elif state["is_finale"] and not self.walt_is_enemy(state):
            shown["enemies"] = [self.chapter["finale_enemy"]]     # the smoke / the blaze
        if state["is_finale"] and self.chapter["flashback"] == "fire":
            self.flashback()                                     # Night C: first what happened, then the fight
        self.walk_and_meet(state, shown)
        if not self.applied:
            self.apply_decision(state)
        if state["is_finale"]:
            if self.chapter["flashback"] == "clues":             # Night A: the reveal, then the signs
                self.flashback()
            w.bubble = ""
            w.speak(w.finale_start, ghost=self.walt_is_enemy(state))
        elif victim:
            self.tell_about(victim, state.get("coach"))
        elif not state.get("walt_say"):
            w.bubble = PW.WALT_BUBBLE.get(w.help_mode, "")
        self.policy.coach = state.get("coach") if victim else None
        self.policy.finale_enemy = None if self.walt_is_enemy(state) or not state["is_finale"] \
            else self.chapter["finale_enemy"]

    def draw_walk(self, state, beat, walked, appear, stepping, moved):
        """The normal walk, plus (Night B) a keepsake that glints on the ground halfway: press E while it is
        near to pick it up. Walk past it and it is gone for tonight."""
        super().draw_walk(state, beat, walked, appear, stepping, moved)
        if walked >= PW.WALK_DISTANCE and appear is None and not self.applied:
            dots = "." * (1 + int(time.time() * 3) % 3)
            draw_text(self.window.canvas, f"Walt is thinking{dots}", self.window.font, COLORS["flashlight"],
                      WIDTH // 2, 440, center=True)
        if self.keepsake_state != "lying":
            return
        if appear is not None:                   # the ghosts are here: walked past it, gone for tonight
            self.keepsake_state = "missed"
            return
        w = self.window
        c = w.canvas
        x = int(700 - walked)                    # lies on the ground ahead and comes closer with the ground
        glint = abs(math.sin(time.time() * 4))
        PW.draw_glow(c, x, GROUND_Y - 6, 40, (255, 220, 140), strength=int(10 + 30 * glint))
        pygame.draw.ellipse(c, (120, 90, 60), (x - 12, GROUND_Y - 12, 24, 12))
        pygame.draw.circle(c, (255, 240, 200), (x + 4, GROUND_Y - 10), 2 + int(3 * glint))
        near = x < 420
        if near:
            draw_text(c, "E  pick it up", w.font, COLORS["charge"], x, GROUND_Y - 60, center=True)
        pressed = pygame.key.get_pressed()[pygame.K_e] or w.demo_dir is not None
        if near and pressed:
            self.keepsake_state = "taken"
            self.keepsakes.append(self.walk_keepsake["id"])
            w.sounds.play("win")
            w.popup(f"Found: {self.walk_keepsake['name']}", COLORS["charge"], x, GROUND_Y - 90)
            w.speak(self.walk_keepsake["memory"])

    def flashback(self):
        """At the gate. Night A: the clue rooms (as in the normal game). Night B: what each keepsake found
        tonight reminds Walt of. Night C: the fire of 1987, one scene per keepsake found in Night B, a
        burnt-out frame for each one that was missed, then the truth."""
        kind = self.chapter["flashback"]
        if kind == "clues":
            super().flashback()
            return
        story = self.chapter
        self.memory_scene(None, story["flashback_intro"])
        if kind == "keepsakes":
            if not self.keepsakes:
                self.memory_scene(None, story["flashback_none"])
                return
            for keepsake_id in self.keepsakes:
                keepsake = KEEPSAKE_BY_ID[keepsake_id]
                self.memory_scene(keepsake["beat"], keepsake["memory"], style="keepsake")
            self.memory_scene(None, story["flashback_end"])
            return
        for keepsake in KEEPSAKES:                                   # Night C, in the order of that night
            if keepsake["id"] in self.keepsakes_before:
                self.memory_scene(keepsake["beat"], keepsake["fire"], style="fire")
            else:
                self.memory_scene(None, story["flashback_missing"], style="burnt")
        self.memory_scene(None, story["flashback_end"])

    def tell_about(self, victim, coach):
        """What Walt says when a victim appears (hint level 1). Silent Walt: nothing useful. Scripted Walt:
        the fixed life story. LLM Walt: the life story in his own words. From then on the name is shown."""
        w = self.window
        w.bubble = ""
        line = coach.opening_line() if coach is not None else None
        if line is None:
            w.speak(SILENT_LINE)
            return
        w.speak(line)
        self.policy.names_known.add(victim)

    def after_room(self, state, row):
        self.window.sounds.end_carousel()
        if state["is_finale"] and row["cleared"] and self.chapter["flashback"] == "keepsakes":
            self.flashback()                                     # Night B: the gate is open, Walt remembers
        self.visited.append(row["beat_id"])
        self.room_titles.append(self.story.by_id[row["beat_id"]]["title"])
        self.zone_titles.append(self.story.by_id[row["beat_id"]]["title"])
        row["timing_score"] = self.policy.take_room_timing()
        row["help_asks"] = self.policy.take_help_asks()
        band = row["band"]
        result = "cleared" if row["cleared"] else "not cleared"
        self.last_result = (f"{result}, HP lost {row['hp_lost_ratio']:.0%}, {PW.BAND_TEXT[band]}", band)
        self.window.sounds.play("win" if band == "in_band" else "click")

    def draw_track(self, c, state, beat, walked):
        """Progress through the night (7 rooms): rooms played, this room, '?' for the rest."""
        w = self.window
        count = state["rooms"]
        index = state["room_index"]
        track = pygame.Rect(180, 500, 600, 8)
        start = max(0.0, index - 0.5)                            # walking from the last room to this one
        end = index + 0.5
        share = (start + (end - start) * walked / PW.WALK_DISTANCE) / count
        pygame.draw.rect(c, COLORS["bar_back"], track, border_radius=4)
        pygame.draw.rect(c, COLORS["flashlight"], (track.x, track.y, int(track.width * share), 8), border_radius=4)
        for i in range(count):
            x = track.x + int(track.width * (i + 0.5) / count)
            pygame.draw.circle(c, COLORS["charge"] if i == index else COLORS["text"], (x, track.centery), 6)
        draw_text(c, f"Night {self.night}: room {index + 1} of {count}", w.font_small, COLORS["dim_text"],
                  track.centerx, track.y + 22, center=True)


def play_story_night(window, story, night, brain_name):
    """Play one story-mode night in the window. Output: the room rows."""
    names_known = set()
    policy = StoryPolicy(window, names_known)
    narrator = StoryNarrator(story, window, policy, brain_name, night)
    brain = BRAINS[brain_name]()
    profile = load_profile(window.player_id)
    brain.remember(profile)                                  # only LLM Walt uses it (part 3)
    narrator.keepsakes_before = (profile or {}).get("keepsakes", [])
    chapter = NIGHT_STORY[night]
    window.walt_is_ghost = chapter["walt_is_ghost"]
    window.gate_line, window.reveal_line = chapter["gate_line"], chapter["reveal_line"]
    window.finale_start, window.farewell = chapter["finale_start"], chapter["farewell"]
    window.true_ending = night == "C"
    window.fire_level = 0
    seed = int(time.time()) % 1000000
    try:
        rows = play_night(night, brain, policy, seed, narrator=narrator)
    finally:
        window.fire_level = 0                               # the ending scene and the menus do not burn
        window.walt_is_ghost = False
    for r in rows:                                          # Night B measure: keepsakes found tonight
        r["keepsakes_found"] = len(narrator.keepsakes) if night == "B" else None
    if window.demo_dir is None:                             # demo runs never change a player's profile
        skill = brain.skill.estimate if hasattr(brain, "skill") else 0.0
        update_profile(window.player_id, rows, skill, keepsakes=getattr(narrator, "keepsakes", None))
    window.last_result = narrator.last_result
    return rows, seed


# ---------------------------------------------------------------- questions after each night (Study 2)
RATING_QUESTIONS = [
    ("fun", "How much fun was this night?", ["1 no fun", "2", "3", "4", "5 great fun"]),
    ("walt_helped", "Did Walt help you?", ["1 not at all", "2", "3", "4", "5 a lot"]),
    ("walt_companion", "Did Walt feel like a real companion?", ["1 not at all", "2", "3", "4", "5 very much"]),
    ("difficulty_felt", "How hard was this night?", ["1 far too easy", "2 a bit easy", "3 just right",
                                                     "4 a bit hard", "5 far too hard"]),
]


def ask_question(window, number, total, text, options):
    """One question on its own screen, answers as buttons (keys 1-5). Output: index of the chosen answer."""
    w = window
    count = len(options)
    width = min(240, (WIDTH - 40 - 10 * (count - 1)) // count)
    start = (WIDTH - (count * width + 10 * (count - 1))) // 2
    buttons = [Button(f"answer:{i}", option, (start + i * (width + 10), 330, width, 54), [pygame.K_1 + i])
               for i, option in enumerate(options)]

    def draw_scene(dt):
        w.scenery.draw_back(w.canvas, 1)
        w.fog.draw(w.canvas, dt)
        panel = pygame.Rect(60, 90, 840, 320)
        pygame.draw.rect(w.canvas, COLORS["panel"], panel, border_radius=14)
        pygame.draw.rect(w.canvas, COLORS["glow"], panel, width=2, border_radius=14)
        draw_text(w.canvas, f"Question {number} of {total}", w.font_small, COLORS["dim_text"], WIDTH // 2, 120, center=True)
        for i, line in enumerate(PW.wrap_text(text, w.font_big, 760)):
            draw_text(w.canvas, line, w.font_big, COLORS["text"], WIDTH // 2, 180 + 40 * i, center=True)
        draw_text(w.canvas, f"Click an answer or press 1-{count}", w.font_small, COLORS["dim_text"],
                  WIDTH // 2, 300, center=True)
    if w.demo_dir is not None:
        w.demo_choice = buttons[0].name
    choice = w.wait_for(draw_scene, buttons)
    return int(choice.split(":")[1])


def post_night_questions(window, rows):
    """After a story night: 4 ratings and one comprehension question per victim met (3 answers in a fixed
    shuffled order). Output: dict of answers (saved by play_window.py to data/story_answers.csv)."""
    victims = [r["victim"] for r in rows if r.get("victim")]
    total = len(RATING_QUESTIONS) + len(victims)
    answers = {}
    window.room_label = "A few questions"
    for number, (key, text, options) in enumerate(RATING_QUESTIONS, start=1):
        answers[key] = ask_question(window, number, total, text, options) + 1          # 1-5
    for i, victim in enumerate(victims):
        question, right, wrong = VICTIMS[victim]["question"]
        options = [right] + list(wrong)
        order = sorted(range(3), key=lambda k: hash_order(victim, k))                    # same order for everyone
        shown = [options[k] for k in order]
        picked = ask_question(window, len(RATING_QUESTIONS) + i + 1, total, question, shown)
        answers[f"understood_{victim}"] = shown[picked] == right
    return answers


def hash_order(victim, k):
    """A fixed, victim-specific shuffle key (so the right answer is not always the first button)."""
    return (len(victim) * 7 + k * 5 + ord(victim[0]) * k) % 11


NIGHT_CHOICES = list(NIGHTS)
COMPANIONS = list(BRAINS)
