"""
Study 2 (story mode): one night = 7 rooms (normal rooms, two victim rooms, the finale against Walt).

The rooms of each night are fixed (game/victims.py, NIGHTS), so the only thing that differs between
players and games is the companion brain (silent, scripted or LLM Walt) and the player. Difficulty is
always "normal" in story mode; the companion only chooses HOW Walt helps (same help modes as Study 1).

Companion brains provide:
  help_mode(state)          -> "stay_back" | "hint" | "heal" | "fight"
  observe(state, row)       -> learn from the finished room (skill estimate, memory)
A narrator (the game window, or None for test players) can show the walk, the encounter and the result:
  before_room(state, room_info)   and   after_room(state, row)
"""
import random

from . import config as C
from .engine import PlayerState, band_position, hp_lost_ratio, play_room
from .skill import SkillEstimator, load_expected_table
from .story import Story
from .victims import NIGHTS, VICTIMS, play_victim_room

STORY_DIFFICULTY = "normal"


class SilentBrain:
    """Silent Walt: always the same help (hint), says nothing about the victims."""
    name = "silent"

    def help_mode(self, state):
        return "hint"

    def observe(self, state, row):
        pass


class ScriptedBrain:
    """Scripted Walt: chooses his help with the rule director's logic from Study 1 (skill estimate,
    low HP, died last room). His words are fixed, hand-written lines (shown by the window)."""
    name = "scripted"

    def __init__(self):
        self.skill = SkillEstimator(load_expected_table())
        self.died_last_room = False

    def help_mode(self, state):
        if self.died_last_room or state["hp"] / state["max_hp"] < C.RULE_LOW_HP:
            return "heal"
        if self.skill.estimate > C.RULE_STRUGGLING:
            return "hint"
        if self.skill.estimate < -C.RULE_CRUISING:
            return "stay_back"
        return "hint"

    def observe(self, state, row):
        self.skill.update(row)
        self.died_last_room = row["deaths"] > 0


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
        help_mode = C.FINALE_HELP_MODE if is_finale else brain.help_mode(state)
        if help_mode not in C.HELP_MODES and not is_finale:
            help_mode = "hint"                                         # anything invalid: safe default
        state["help_mode"] = help_mode
        if narrator is not None:
            narrator.before_room(state, info)
        if info["victim"]:
            t = play_victim_room(player, info["victim"], help_mode, policy, rng)
        else:
            t = play_room(player, beat, STORY_DIFFICULTY, help_mode, policy, rng)
        row = {"night": night, "companion": brain.name, "seed": seed, "room_index": index,
               "zone": beat["zone"], "is_finale": is_finale, "beat_id": info["beat_id"],
               "victim": info["victim"], "difficulty": STORY_DIFFICULTY, "help_mode": help_mode, **t,
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
