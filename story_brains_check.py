"""
Bot check for Study 2's three Walt versions: whole story nights, played by bots, with Walt choosing the
difficulty and his help before every room (game/story_mode.py). Same idea as compare_directors.py in
Study 1, but on the story nights (7 fixed rooms, victim ghosts, finale).

Test players: the three bot types of Study 1 (beginner, average, expert), each in two versions:
  naive : does not know the victims' weaknesses
  listen: understands the weakness only after hearing Walt's hint, with a chance that grows with the
          hint level (UNDERSTAND_CHANCE, an assumption, not measured): level 1 25%, 2 50%, 3 85%
  smart : uses every weakness (story_check.SmartBot)
Measures: share of rooms in band (30-70% HP lost, no death), too hard, too easy, nights escaped.

LLM Walt calls the local model (Ollama) once per room, so run him in small batches (the laptop gets hot):
  python story_brains_check.py --brains silent scripted --games 100
  python story_brains_check.py --brains llm --nights A --games 1   (answers are cached in data/llm_cache.json)
"""
import argparse
import random

import pandas as pd

from game.bots import Bot
from game.story_mode import BRAINS, play_night
from game.victims import NIGHTS
from story_check import SmartBot

PROFILES = ("beginner", "average", "expert")
UNDERSTAND_CHANCE = {0: 0.0, 1: 0.25, 2: 0.5, 3: 0.85}


class ListeningBot(SmartBot):
    """Plays like a normal bot until Walt's hints make it understand the weakness (one roll per new hint
    level), then like SmartBot. A rough stand-in for a human who listens to Walt."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.understood = False
        self.level_seen = 0

    def choose_action(self, view, rng):
        if view.get("turn") == 1:                          # a new fight (or a new attempt): forget
            self.understood, self.level_seen = False, 0
        level = view.get("hint_level", 0)
        if level > self.level_seen:
            self.level_seen = level
            if rng.random() < UNDERSTAND_CHANCE[level]:
                self.understood = True
        if self.understood:
            return super().choose_action(view, rng)
        return Bot.choose_action(self, view, rng)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brains", nargs="+", default=["silent", "scripted"], choices=list(BRAINS))
    ap.add_argument("--games", type=int, default=100, help="nights per night x bot type x naive/smart")
    ap.add_argument("--nights", nargs="+", default=list(NIGHTS), choices=list(NIGHTS))
    ap.add_argument("--first-seed", type=int, default=300000, help="Study 2 bot seeds start at 300000")
    args = ap.parse_args()
    rows = []
    for brain_name in args.brains:
        for night in args.nights:
            for profile in PROFILES:
                for kind, cls in (("naive", Bot), ("listen", ListeningBot), ("smart", SmartBot)):
                    for seed in range(args.first_seed, args.first_seed + args.games):
                        bot = cls(profile, random.Random(f"bot-{profile}-{seed}"))
                        night_rows = play_night(night, BRAINS[brain_name](), bot, seed)
                        for r in night_rows:
                            r.update({"bot_type": profile, "player": kind})
                        rows.extend(night_rows)
            print(f"  {brain_name}: night {night} done")
    df = pd.DataFrame(rows)
    df["too_hard"] = df["band"] == "too_hard"
    df["too_easy"] = df["band"] == "too_easy"
    df["escaped"] = df["run_outcome"] == "escaped"
    table = df.groupby(["companion", "player"]).agg(in_band=("in_band", "mean"), too_hard=("too_hard", "mean"),
                                                    too_easy=("too_easy", "mean"), escaped=("escaped", "mean"))
    choices = pd.crosstab(df["companion"], df["difficulty"], normalize="index")
    fights = df[df["victim"].notna() & (df["player"] == "listen")]
    hints = fights.groupby("companion").agg(weakness_found=("weakness_used", "mean"),
                                            turn_found=("turn_first_used", "mean"),
                                            hint_level_max=("hint_level_max", "mean"),
                                            victim_in_band=("in_band", "mean"))
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print("\nShare of rooms (and of nights escaped), per Walt version:")
        print(table)
        print("\nVictim fights of the 'listen' players (the hint ladder):")
        print(hints)
        print("\nHow often each Walt chose each difficulty:")
        print(choices)
        if "decision_source" in df:
            print("\nWhere the decisions came from:")
            print(df.groupby("companion")["decision_source"].value_counts(normalize=True).round(2))


if __name__ == "__main__":
    main()
