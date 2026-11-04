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
  before_room_deciding(state, room_info, job)   walks to the room while Walt's decision (job) is made
  before_room(state, room_info)   and   after_room(state, row)
LLM calls never stop the game window: they run in the background (Job) and Walt speaks when an answer is
ready. For bots (no window) every call runs at once, so bot results stay repeatable.
"""
import random
import threading

import pandas as pd

from . import config as C
from .chapters import NIGHT_STORY
from .engine import PlayerState, band_position, hp_lost_ratio, play_room
from .profiles import memory_text
from .risk import FEATURES, load_band_model, option_features
from .skill import SkillEstimator, load_expected_table
from .story import Story
from .victims import NIGHTS, VICTIMS, play_victim_room
from .walt_llm import (HINT_SYSTEM_PROMPT, STORY_SYSTEM_PROMPT, WALT_SYSTEM_PROMPT, WaltClient, check_answer,
                       check_hint, check_story, hint_prompt, study1_room_index, walt_prompt)

LLM_SHORTLIST = 6              # same shortlist size as llm_risk in Study 1
# Hint ladder (part 2). Levels: 0 nothing, 1 the life story, 2 a clearer nudge, 3 exactly what to do.
SCRIPTED_HINT_TURNS = {2: 4, 3: 7}      # scripted Walt: level 2 from turn 4, level 3 from turn 7 (if still not found)
LLM_HINT_CHECKS = (3, 6)                # LLM Walt decides at these turns (2 calls per fight: speed and laptop heat)
SILENT_HELP_LINE = "..."                 # silent Walt only shrugs when asked for help
HELP_ASKED_NOTE = "The player just pressed the 'Walt, help!' button: they are asking you for help right now."
GOT_IT_LINE = "You've got it, kid. Keep doing that."
STORY_WAIT_LINE = "Wait... I know that face."           # LLM Walt, if his life story is not ready yet
HELP_WAIT_LINE = "Let me think, kid..."
BUSY_LINE = "Hang on, kid, I'm thinking."
SAID_MEMORY = 3                          # LLM Walt is shown his last 3 sentences, so he does not repeat them


class Job:
    """One piece of slow work (a model call). In the game window it runs in a background thread, so the
    game never waits; for bots it runs at once (same answers in the same order, repeatable).
    Input: work = a function without arguments, background = True for a thread."""

    def __init__(self, work, background=False):
        self.result = None
        self.finished = False
        if background:
            threading.Thread(target=self.run, args=(work,), daemon=True).start()
        else:
            self.run(work)

    def run(self, work):
        self.result = work()
        self.finished = True

    def done(self):
        return self.finished


class SilentCoach:
    """Silent Walt: no hints during the fight (level 0)."""

    def __init__(self, victim_id):
        self.level = 0
        self.fallbacks = 0

    def start_story(self):
        pass

    def opening_line(self):
        return None

    def poll(self):
        return None

    def step(self, fight):
        return self.level, None

    def ask_help(self, fight):
        return self.level, SILENT_HELP_LINE


class ScriptedCoach(SilentCoach):
    """Scripted Walt: tells the fixed life story (level 1), then climbs the ladder on fixed turns."""

    def __init__(self, victim_id):
        super().__init__(victim_id)
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

    def ask_help(self, fight):
        """"Walt, help!": one level up the ladder (fixed lines). At level 3 he repeats the exact move."""
        if fight["weakness_used"]:
            return self.level, GOT_IT_LINE
        self.level = min(3, max(2, self.level + 1))
        return self.level, self.victim[f"hint{self.level}"]


class LLMCoach(ScriptedCoach):
    """LLM Walt: tells the life story in his own words (the clue fact must be in it, prepared as soon as the
    night starts), and at turns 3 and 6 decides himself whether to reveal more, from what the player has
    tried and how hurt they are. Answers arrive whenever the model is done (poll); invalid answers fall
    back to the scripted line of that level and are counted."""

    def __init__(self, victim_id, client, memory="", background=False):
        super().__init__(victim_id)
        self.client = client
        self.memory = memory
        self.background = background
        self.story_job = None
        self.story_waiting = False         # True: the victim is here, but the story was not ready yet
        self.job = None                    # the hint / help question being answered
        self.job_kind = None
        self.job_fight = None

    def start_story(self):
        """Ask for the life story early (the window calls this at the start of the night)."""
        if self.story_job is None:
            text = f"The ghost: {self.victim['name']}, the park's {self.victim['role']}. The fact: {self.victim['fact']}"
            self.story_job = Job(lambda: self.client.ask(text, STORY_SYSTEM_PROMPT, tag="|walt_story"),
                                 self.background)

    def finish_story(self):
        say = check_story(self.story_job.result or {}, self.victim)
        if say is None:
            self.fallbacks += 1
            return self.victim["scripted"]
        return say

    def opening_line(self):
        self.start_story()
        if self.story_job.done():
            return self.finish_story()
        self.story_waiting = True
        return STORY_WAIT_LINE

    def start(self, kind, fight, prompt, tag):
        self.job_kind, self.job_fight = kind, fight
        self.job = Job(lambda: self.client.ask(prompt, HINT_SYSTEM_PROMPT, tag=tag), self.background)

    def poll(self):
        """A finished answer, if there is one. Output: the line Walt should say now, or None."""
        if self.story_waiting and self.story_job.done():
            self.story_waiting = False
            return self.finish_story()
        if self.job is None or not self.job.done():
            return None
        answer, kind, fight = self.job.result or {}, self.job_kind, self.job_fight
        self.job = None
        self.client.save_cache()
        level, say = check_hint(answer, self.level, self.victim)
        if kind == "help" and (level is None or say is None):
            self.fallbacks += 1
            return ScriptedCoach.ask_help(self, fight)[1]
        if level is None:                                  # invalid answer: no change
            self.fallbacks += 1
            return None
        if say is None and level > self.level:             # went up, but the sentence failed the check
            self.fallbacks += 1
            say = self.victim[f"hint{level}"]
        self.level = level
        return say

    def step(self, fight):
        line = self.poll()
        if (line is None and self.job is None and not fight["weakness_used"] and self.level < 3
                and fight["turn"] in LLM_HINT_CHECKS):
            self.start("hint", fight, hint_prompt(self.victim, fight, self.level, self.memory), "|walt_hint")
            line = self.poll()                             # bots: answered at once; window: arrives later
        return self.level, line

    def ask_help(self, fight):
        """"Walt, help!": the model decides how much to reveal, knowing that the player asked."""
        if fight["weakness_used"]:
            return self.level, GOT_IT_LINE
        if self.job is not None:
            return self.level, BUSY_LINE
        prompt = hint_prompt(self.victim, fight, self.level, self.memory) + "\n" + HELP_ASKED_NOTE
        self.start("help", fight, prompt, "|walt_help")
        line = self.poll()
        return self.level, line or HELP_WAIT_LINE


class SilentBrain:
    """Silent Walt = the fixed director: always normal difficulty, always the same help (hint), says
    nothing about the victims."""
    name = "silent"

    def decide(self, state):
        return {"difficulty": "normal", "help_mode": "hint", "say": None, "reason": "fixed", "source": "fixed"}

    def coach(self, victim_id, background=False):
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

    def coach(self, victim_id, background=False):
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
    client = None              # one WaltClient (with its cache) for the whole game

    def __init__(self):
        super().__init__()
        if LLMBrain.client is None:
            LLMBrain.client = WaltClient()
        self.band_model = load_band_model()
        self.table = load_expected_table()
        self.last_hp_lost = 0.0
        self.last_band = None
        self.memory = ""                   # filled by remember() for a returning player
        self.said = []                     # his sentences tonight (so he does not repeat himself)

    def coach(self, victim_id, background=False):
        return LLMCoach(victim_id, LLMBrain.client, self.memory, background)

    def remember(self, profile):
        """Part 3: memory across nights. The profile becomes a few sentences in every prompt, and the
        skill estimate starts where it ended last night instead of at 0 (average)."""
        self.memory = memory_text(profile)
        if profile and "skill_estimate" in profile:
            self.skill.estimate = profile["skill_estimate"]

    def score_options(self, state):
        """Output: every allowed (difficulty, help) option with predicted band shares, best first."""
        help_modes = [C.FINALE_HELP_MODE] if state["walt_is_enemy"] else C.HELP_MODES
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
                             state["walt_is_enemy"], self.memory, self.said[-SAID_MEMORY:])
        answer = LLMBrain.client.ask(prompt, WALT_SYSTEM_PROMPT, tag="|walt")
        LLMBrain.client.save_cache()
        option, say = check_answer(answer, shortlist)
        if option is None:
            fallback["source"] = "fallback"
            return fallback
        if say:
            self.said.append(say)
        return {"difficulty": option["difficulty"], "help_mode": option["help_mode"], "say": say,
                "reason": "", "source": "llm" if say else "llm_no_line"}

    def observe(self, state, row):
        super().observe(state, row)
        self.last_hp_lost = row["hp_lost_ratio"]
        self.last_band = row["band"]


BRAINS = {b.name: b for b in [SilentBrain, ScriptedBrain, LLMBrain]}


def warm_up_llm():
    """Load the model into memory before the night starts (on the test laptop the first answer of a cold
    model took about 24 s). The answer is thrown away and never cached."""
    client = WaltClient(cache_path="data/llm_warmup_unused.json")
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
    background = narrator is not None and getattr(narrator, "background_llm", False)
    coaches = {room: brain.coach(room, background) for room in rooms if room in VICTIMS}
    walt_at_gate = NIGHT_STORY[night]["finale_enemy"] == "walt"      # Night A: Walt is the last enemy
    for index, room in enumerate(rooms):
        info = room_info(room)
        beat = story.get(info["beat_id"])
        is_finale = info["beat_id"] == "finale_gate"
        state = {"night": night, "room_index": index, "rooms": len(rooms), "zone": beat["zone"],
                 "is_finale": is_finale, "walt_is_enemy": is_finale and walt_at_gate,
                 "victim": info["victim"], "beat_id": info["beat_id"],
                 "hp": player.hp, "max_hp": C.PLAYER_MAX_HP, "potions": player.potions,
                 "deaths_total": player.deaths_total, "history": history,
                 "coach": coaches.get(info["victim"])}
        client = getattr(brain, "client", None)                        # LLM Walt only: count model time
        calls_before = (client.calls, client.cache_hits, client.seconds) if client else None

        def decide(state=state):
            """Walt's decision for this room, checked, and written into the state."""
            decision = brain.decide(state)
            help_mode = C.FINALE_HELP_MODE if state["walt_is_enemy"] else decision.get("help_mode")
            if help_mode not in C.HELP_MODES and not state["walt_is_enemy"]:
                help_mode = "hint"                                     # anything invalid: safe default
            difficulty = decision.get("difficulty")
            if difficulty not in C.DIFFICULTY:
                difficulty = "normal"
            decision.update({"help_mode": help_mode, "difficulty": difficulty})
            state.update({"help_mode": help_mode, "difficulty": difficulty, "walt_say": decision.get("say")})
            return decision

        job = Job(decide, background)                                  # window: runs while the player walks
        if index == 0:
            for coach in coaches.values():                             # prepare the life stories early
                coach.start_story()
        if narrator is not None and hasattr(narrator, "before_room_deciding"):
            decision = narrator.before_room_deciding(state, info, job)
        else:
            decision = job.result
            if narrator is not None:
                narrator.before_room(state, info)
        help_mode, difficulty = decision["help_mode"], decision["difficulty"]
        coach = state["coach"]
        if info["victim"]:
            t = play_victim_room(player, info["victim"], help_mode, policy, rng, difficulty, coach)
            t["coach_fallbacks"] = coach.fallbacks
        else:
            t = play_room(player, beat, difficulty, help_mode, policy, rng)
        row = {"night": night, "companion": brain.name, "seed": seed, "room_index": index,
               "zone": beat["zone"], "is_finale": is_finale, "beat_id": info["beat_id"],
               "victim": info["victim"], "difficulty": difficulty, "help_mode": help_mode,
               "decision_source": decision.get("source"), "walt_reason": decision.get("reason"),
               "walt_say": decision.get("say"), **t,
               "hp_lost_ratio": round(hp_lost_ratio(t), 4), "band": band_position(t)}
        row["in_band"] = row["band"] == "in_band"
        if client:                                                     # model calls in this room (decision + hints)
            row["llm_calls"] = client.calls - calls_before[0]
            row["llm_cache_hits"] = client.cache_hits - calls_before[1]
            row["llm_seconds"] = round(client.seconds - calls_before[2], 2)
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
