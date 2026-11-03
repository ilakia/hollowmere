"""
Balance check for Study 2's victim ghosts: does using the weakness make a clear difference?

Two test players per bot type (same settings, same dice):
  naive : a normal bot (game/bots.py) that does not know the weaknesses
  smart : the same bot, but it uses each victim's weakness
For every victim: turns needed, HP lost, deaths and the band, naive vs smart.

Example:  python story_check.py --games 300
"""
import argparse
import random

import pandas as pd

from game.bots import Bot
from game.engine import PlayerState, band_position, hp_lost_ratio
from game.victims import VICTIMS, play_victim_room


class SmartBot(Bot):
    """A bot that knows every victim's weakness (an upper bound for 'the player understood the clue')."""

    def choose_action(self, view, rng):
        victim = view.get("victim")
        if view["potions"] > 0 and view["hp"] / view["max_hp"] < self.potion_at:
            return "potion"
        if victim == "martha" and not view["stunned"]:
            return "shine"
        if victim == "rosa" and view["cue"] == "camera_up":
            return "shine"
        if victim == "benny":
            return "attack" if view["cue"] == "music_stopped" else "defend"
        if victim == "ned":
            return "attack" if view["cue"] == "whistle" else "defend"
        if victim == "henry":
            return "call:" + VICTIMS["henry"]["true_name"]
        if victim == "twins":
            return f"attack:{view['targets'].index('real')}"
        return super().choose_action(view, rng)


def fight(victim, bot, seed):
    player = PlayerState()
    t = play_victim_room(player, victim, "hint", bot, random.Random(f"fight-{victim}-{seed}"))
    t["hp_lost_ratio"] = hp_lost_ratio(t)
    t["band"] = band_position(t)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=300)
    args = ap.parse_args()
    rows = []
    for victim in VICTIMS:
        for profile in ("beginner", "average", "expert"):
            for seed in range(args.games):
                for kind, cls in (("naive", Bot), ("smart", SmartBot)):
                    bot = cls(profile, random.Random(f"bot-{profile}-{seed}"))
                    t = fight(victim, bot, seed)
                    rows.append({"victim": victim, "bot_type": profile, "player": kind, "turns": t["turns"],
                                 "hp_lost": t["hp_lost_ratio"], "deaths": t["deaths"],
                                 "in_band": t["band"] == "in_band", "too_hard": t["band"] == "too_hard",
                                 "weakness_used": t["weakness_used"]})
    df = pd.DataFrame(rows)
    table = df.groupby(["victim", "player"]).agg(turns=("turns", "mean"), hp_lost=("hp_lost", "median"),
                                                 deaths=("deaths", "mean"), in_band=("in_band", "mean"),
                                                 too_hard=("too_hard", "mean"), weakness=("weakness_used", "mean"))
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print(table)


if __name__ == "__main__":
    main()
