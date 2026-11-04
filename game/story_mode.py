"""
Study 2 (story mode): one night = 7 rooms (normal rooms, two victim rooms, the finale against Walt).

The rooms of each night are fixed (game/victims.py, NIGHTS). Before every room the companion brain
(silent, scripted or LLM Walt) quietly chooses the room's DIFFICULTY and HOW Walt helps, using the
three directors that were compared with bots in Study 1:
  silent   = the fixed director     (always normal, always hint)        Study 1: 55.6% in band
  scripted = the rule director      (skill estimate + if-else rules)    Study 1: 64.0% in band
  llm      = the llm_risk director  (band model shortlist + LLM choice) Study 1: 76.5% in band
So Study 2 tests the Study 1 directors with real players, with the director "embodied" as Walt.

Companion brains provide:
  decide(state)             -> {"difficulty", "help_mode", "say", "reason", "source"}
  observe(state, row)       -> learn from the finished room (skill estimate, memory)
A narrator (the game window, or None for test players) can show the walk, the encounter and the result:
  think(work)                     runs work() (e.g. a slow LLM call) while the window keeps animating
  before_room(state, room_info)   and   after_room(state, row)
"""
import random

import pandas as pd

from . import config as C
from .engine import PlayerState, band_position, hp_lost_ratio, play_room
from .profiles import memory_text
from .risk import FEATURES, load_band_model, option_features
from .skill import SkillEstimator, load_expected_table
from .story import Story
from .victims import NIGHTS, VICTIMS, play_victim_room
from .walt_llm import (HINT_SYSTEM_PROMPT, STORY_SYSTEM_PROMPT, WALT_SYSTEM_PROMPT, check_answer, check_hint,
                       check_story, hint_prompt, study1_room_index, walt_prompt)

LLM_SHORTLIST = 6              # same shortlist size as llm_risk in Study 1
# Hint ladder (part 2). Levels: 0 nothing, 1 the life story, 2 a clearer nudge, 3 exactly what to do.
SCRIPTED_HINT_TURNS = {2: 4, 3: 7}      # scripted Walt: level 2 from turn 4, level 3 from turn 7 (if still not found)
LLM_HINT_CHECKS = (3, 5, 7, 9)          # LLM Walt decides at these turns (at most 4 calls per fight: laptop heat)


class SilentCoach:
    """Silent Walt: no hints during the fight (level 0)."""

    def __init__(self, victim_id):
        self.level = 0

    def opening_line(self):
        return None

    def step(self, fight):
        return self.level, None


class ScriptedCoach:
    """Scripted Walt: tells the fixed life story (level 1), then climbs the ladder on fixed turns."""

    def __init__(self, victim_id):
        self.victim = VICTIMS[victim_id]
        self.level = 1

    def opening_line(self):
        return self.victim["scripted"]

    def step(self, fight):
        if fight["weakness_used"]:
            return self.level, None
        for level in (2, 3):
            if self.level < level and fight["turn"] >= SCRIPTED_HINT_TURNS[level]:
                self.level = level
                return level, self.victim[f"hint{level}"]
        return self.level, None


class LLMCoach(ScriptedCoach):
    """LLM Walt: tells the life story in his own words (the clue fact must be in it), and at a few turns
    decides himself whether to reveal more, from what the player has tried and how hurt they are.
    Invalid answers fall back to the scripted line of that level; every answer is counted."""

    def __init__(self, victim_id, client, think=None, memory=""):
        super().__init__(victim_id)
        self.client = client
        self.memory = memory
        self.think = think or (lambda work: work())       # the window keeps animating while the model works
        self.fallbacks = 0

    def opening_line(self):
        answer = self.think(lambda: self.client.ask(f"The ghost: {self.victim['name']}, the park's "
                                                    f"{self.victim['role']}. The fact: {self.victim['fact']}",
                                                    STORY_SYSTEM_PROMPT, tag="|walt_story"))
        say = check_story(answer, self.victim)
        if say is None:
            self.fallbacks += 1
            return self.victim["scripted"]
        return say

    def step(self, fight):
        if fight["weakness_used"] or fight["turn"] not in LLM_HINT_CHECKS or self.level >= 3:
            return self.level, None
        prompt = hint_prompt(self.victim, fight, self.level, self.memory)
        answer = self.think(lambda: self.client.ask(prompt, HINT_SYSTEM_PROMPT, tag="|walt_hint"))
        self.client.save_cache()
        level, say = check_hint(answer, self.level, self.victim)
        if level is None:                                  # invalid answer: no change this turn
            self.fallbacks += 1
            return self.level, None
        if say is None and level > self.level:             # went up but the sentence failed the check
            self.fallbacks += 1
            say = self.victim[f"hint{level}"]
        self.level = level
        return level, say


class SilentBrain:
    """Silent Walt = the fixed director: always normal difficulty, always the same help (hint), says
    nothing about the victims."""
    name = "silent"

    def decide(self, state):
        return {"difficulty": "normal", "help_mode": "hint", "say": None, "reason": "fixed", "source": "fixed"}

    def coach(self, victim_id, think=None):
        return SilentCoach(victim_id)

    def remember(self, profile):
        pass                                               # no memory across nights

    def observe(self, state, row):
        pass


class ScriptedBrain:
    """Scripted Walt = the rule director from Study 1 (controllers.RuleController, same thresholds):
    in danger -> easy + heal, struggling -> easy + hint, cruising -> normal + stay back, else normal + hint.
    The room itself is fixed by the night, so only difficulty and help are chosen. His words are fixed,
    hand-written lines (shown by the window)."""
    name = "scripted"

    def __init__(self):
        self.skill = SkillEstimator(load_expected_table())
        self.died_last_room = False

    def decide(self, state):
        if self.died_last_room or state["hp"] / state["max_hp"] < C.RULE_LOW_HP:
            difficulty, help_mode, reason = "easy", "heal", "in danger"
        elif self.skill.estimate > C.RULE_STRUGGLING:
            difficulty, help_mode, reason = "easy", "hint", "struggling"
        elif self.skill.estimate < -C.RULE_CRUISING:
            difficulty, help_mode, reason = "normal", "stay_back", "cruising"
        else:
            difficulty, help_mode, reason = "normal", "hint", "about average"
        return {"difficulty": difficulty, "help_mode": help_mode, "say": None, "reason": reason, "source": "rule"}

    def coach(self, victim_id, think=None):
        return ScriptedCoach(victim_id)

    def remember(self, profile):
        pass                                               # no memory across nights

    def observe(self, state, row):
        self.skill.update(row)
        self.died_last_room = row["deaths"] > 0


class LLMBrain(ScriptedBrain):
    """LLM Walt = the llm_risk director from Study 1 as a talking companion. Every (difficulty, help)
    option for this room is scored by the band model for this player; the LLM picks one of the best
    LLM_SHORTLIST and says one sentence to the player. Invalid answers fall back to scripted Walt."""
    name = "llm"
    client = None              # one LLMClient (with its cache) for the whole game

    def __init__(self):
        super().__init__()
        if LLMBrain.client is None:
            from .llm import LLMClient       # imported here: silent/scripted Walt never need Ollama
            LLMBrain.client = LLMClient()
        self.band_model = load_band_model()
        self.table = load_expected_table()
        self.last_hp_lost = 0.0
        self.last_band = None
        self.memory = ""                   # filled by remember() for a returning player

    def coach(self, victim_id, think=None):
        return LLMCoach(victim_id, LLMBrain.client, think, self.memory)

    def remember(self, profile):
        """Part 3: memory across nights. The profile becomes a few sentences in every prompt, and the
        skill estimate starts where it ended last night instead of at 0 (average)."""
        self.memory = memory_text(profile)
        if profile and "skill_estimate" in profile:
            self.skill.estimate = profile["skill_estimate"]

    def score_options(self, state):
        """Output: every allowed (difficulty, help) option with predicted band shares, best first."""
        help_modes = [C.FINALE_HELP_MODE] if state["is_finale"] else C.HELP_MODES
        threat = Story().get(state["beat_id"])["threat"]
        position = study1_room_index(state["room_index"], state["rooms"])
        options, rows = [], []
        for difficulty in C.DIFFICULTY:
            for help_mode in help_modes:
                expected = self.table.get((state["beat_id"], difficulty, help_mode), self.skill.fallback)
                rows.append(option_features(position, state["hp"], state["potions"], state["deaths_total"],
                                            self.skill.estimate, self.last_hp_lost, self.died_last_room,
                                            threat, difficulty, help_mode, expected))
                options.append({"difficulty": difficulty, "help_mode": help_mode})
        probabilities = self.band_model.predict_proba(pd.DataFrame(rows, columns=FEATURES))
        classes = list(self.band_model.classes_)
        for option, p in zip(options, probabilities):
            for band in ["in_band", "too_easy", "too_hard"]:
                option[band] = p[classes.index(band)]
        options.sort(key=lambda o: o["in_band"], reverse=True)
        return options

    def decide(self, state):
        fallback = super().decide(state)
        shortlist = self.score_options(state)[:LLM_SHORTLIST]
        prompt = walt_prompt(state["night"], state["room_index"], state["rooms"], state["hp"], state["max_hp"],
                             state["potions"], self.skill.estimate, self.last_band, state["victim"], shortlist,
                             state["is_finale"], self.memory)
        answer = LLMBrain.client.ask(prompt, WALT_SYSTEM_PROMPT, tag="|walt")
        LLMBrain.client.save_cache()
        option, say, reason = check_answer(answer, shortlist)
        if option is None:
            fallback["source"] = "fallback"
            return fallback
        return {"difficulty": option["difficulty"], "help_mode": option["help_mode"], "say": say,
                "reason": reason, "source": "llm" if say else "llm_no_line"}

    def observe(self, state, row):
        super().observe(state, row)
        self.last_hp_lost = row["hp_lost_ratio"]
        self.last_band = row["band"]


BRAINS = {b.name: b for b in [SilentBrain, ScriptedBrain, LLMBrain]}


def warm_up_llm():
    """Load the model into memory before the night starts (on the test laptop the first answer of a cold
    model took about 24 s, later ones about 6 s). The answer is thrown away and never cached."""
    from .llm import LLMClient
    client = LLMClient(cache_path="data/llm_warmup_unused.json")   # its own empty cache, never saved
    client.cache = {}
    client.ask("hello", WALT_SYSTEM_PROMPT, tag="|warmup")


def room_info(room):
    """What a night's room entry means. Output: dict with beat_id and, for victim rooms, the victim id."""
    if room in VICTIMS:
        return {"beat_id": VICTIMS[room]["beat"], "victim": room}
    return {"beat_id": room, "victim": None}


def play_night(night, brain, policy, seed, narrator=None):
    """Play one night. Output: list of room rows (normal rooms have the Study 1 columns, victim rooms add
    the Study 2 measures)."""
    story = Story()
    rng = random.Random(f"story-{night}-{seed}")
    player = PlayerState()
    rooms = NIGHTS[night]
    history = []
    for index, room in enumerate(rooms):
        info = room_info(room)
        beat = story.get(info["beat_id"])
        is_finale = info["beat_id"] == "finale_gate"
        state = {"night": night, "room_index": index, "rooms": len(rooms), "zone": beat["zone"],
                 "is_finale": is_finale, "victim": info["victim"], "beat_id": info["beat_id"],
                 "hp": player.hp, "max_hp": C.PLAYER_MAX_HP, "potions": player.potions,
                 "deaths_total": player.deaths_total, "history": history}
        if narrator is not None and hasattr(narrator, "think"):
            decision = narrator.think(lambda: brain.decide(state))     # the window keeps moving meanwhile
        else:
            decision = brain.decide(state)
        help_mode = C.FINALE_HELP_MODE if is_finale else decision.get("help_mode")
        if help_mode not in C.HELP_MODES and not is_finale:
            help_mode = "hint"                                         # anything invalid: safe default
        difficulty = decision.get("difficulty")
        if difficulty not in C.DIFFICULTY:
            difficulty = "normal"
        state.update({"help_mode": help_mode, "difficulty": difficulty, "walt_say": decision.get("say")})
        coach = None
        if info["victim"]:
            think = narrator.think if narrator is not None and hasattr(narrator, "think") else None
            coach = brain.coach(info["victim"], think)
            state["coach"] = coach                                     # the window asks it for the life story
        if narrator is not None:
            narrator.before_room(state, info)
        if info["victim"]:
            t = play_victim_room(player, info["victim"], help_mode, policy, rng, difficulty, coach)
            t["coach_fallbacks"] = getattr(coach, "fallbacks", 0)
        else:
            t = play_room(player, beat, difficulty, help_mode, policy, rng)
        row = {"night": night, "companion": brain.name, "seed": seed, "room_index": index,
               "zone": beat["zone"], "is_finale": is_finale, "beat_id": info["beat_id"],
               "victim": info["victim"], "difficulty": difficulty, "help_mode": help_mode,
               "decision_source": decision.get("source"), "walt_reason": decision.get("reason"),
               "walt_say": decision.get("say"), **t,
               "hp_lost_ratio": round(hp_lost_ratio(t), 4), "band": band_position(t)}
        row["in_band"] = row["band"] == "in_band"
        history.append(row)
        brain.observe(state, row)
        if narrator is not None:
            narrator.after_room(state, row)
        policy.end_of_room(index)
        if t["quit"] or t["out_of_lives"]:
            break
        player.hp = min(C.PLAYER_MAX_HP, player.hp + C.REST_HEAL)
    last = history[-1]
    outcome = "quit" if last["quit"] else "out_of_lives" if last["out_of_lives"] else "escaped"
    for r in history:
        r["run_outcome"] = outcome
        r["rooms_played"] = len(history)
    return history
