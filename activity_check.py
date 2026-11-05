"""
Check of the six Study 2 activities with bots, and the expected-pressure table.

1) For every activity, difficulty and Walt help, the three bot types play it (no stepping in):
   win rate, mean pressure and the band (too easy / in band / too hard). This shows whether the
   difficulty and help settings really change the activity, and whether a fixed setting can suit
   everyone (it should not: then adapting is worth something).
2) The mean pressure of all bots per (activity, difficulty, help) is saved to
   game/expected_activity.csv. Scripted and LLM Walt's skill estimate compare a player with this
   "average player" value, exactly like Study 1's expected-HP table for the fights.

Seeds 400000+ (Study 2 activity checks). Example:  python activity_check.py --games 200
"""
import argparse
import csv
import random
from pathlib import Path

import pandas as pd

from game.activities import ACTIVITIES, STANDARD_DIFFICULTY, activity_band, play_activity
from game.bots import Bot
from game.engine import PlayerState

TABLE = Path("game/expected_activity.csv")
PROFILES = ("beginner", "average", "expert")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    args = ap.parse_args()
    rows = []
    for activity_id, spec in ACTIVITIES.items():
        for difficulty in STANDARD_DIFFICULTY:
            for help_mode in spec["help"]:
                for profile in PROFILES:
                    for seed in range(400000, 400000 + args.games):
                        rng = random.Random(f"act-{activity_id}-{difficulty}-{help_mode}-{profile}-{seed}")
                        bot = Bot(profile, random.Random(f"bot-{profile}-{seed}"))
                        t = play_activity(PlayerState(), activity_id, difficulty, help_mode, bot, rng)
                        rows.append({"activity": activity_id, "difficulty": difficulty, "help_mode": help_mode,
                                     "bot_type": profile, "won": t["cleared"], "pressure": t["pressure"],
                                     "band": activity_band(t), "steps": t["turns"]})
    df = pd.DataFrame(rows)
    df["in_band"] = df["band"] == "in_band"
    with pd.option_context("display.width", 160, "display.max_rows", 500, "display.float_format", "{:.2f}".format):
        print("In band per bot type (no help, by difficulty):")
        plain = df[df["help_mode"] == "stay_back"]
        print(plain.pivot_table(index=["activity", "difficulty"], columns="bot_type", values="in_band"))
        print("\nMean pressure per bot type (no help):")
        print(plain.pivot_table(index=["activity", "difficulty"], columns="bot_type", values="pressure"))
        print("\nEffect of Walt's help (normal difficulty), in band per bot type:")
        normal = df[df["difficulty"] == "normal"]
        print(normal.pivot_table(index=["activity", "help_mode"], columns="bot_type", values="in_band"))
        best = df.groupby(["activity", "bot_type", "difficulty", "help_mode"])["in_band"].mean().reset_index()
        best = best.loc[best.groupby(["activity", "bot_type"])["in_band"].idxmax()]
        print("\nBest single setting per bot type (what a perfect director would pick):")
        print(best.to_string(index=False))
    expected = df.groupby(["activity", "difficulty", "help_mode"])["pressure"].mean().reset_index()
    with open(TABLE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["beat_id", "difficulty", "help_mode", "expected_hp_lost"])
        for r in expected.itertuples():
            writer.writerow([r.activity, r.difficulty, r.help_mode, round(r.pressure, 4)])
    print(f"\nExpected pressure table saved to {TABLE} ({len(expected)} rows)")


if __name__ == "__main__":
    main()
