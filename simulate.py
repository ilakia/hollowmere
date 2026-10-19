"""
Let bots play many runs and save one CSV row per room.

Example:
  python simulate.py --games 1000 --controllers fixed random --out data/sim_runs.csv

The same seed gives the same bot and the same random events, so every controller
is tested against exactly the same set of players (a paired comparison).
"""
import argparse
import random
from pathlib import Path

import pandas as pd

from game.bots import PROFILES, Bot
from game.controllers import CONTROLLERS
from game.engine import play_run
from game.story import Story


def simulate(controllers, profiles, games, seed_start=0):
    story = Story()
    rows = []
    for cname in controllers:
        for profile in profiles:
            for seed in range(seed_start, seed_start + games):
                bot = Bot(profile, random.Random(f"bot-{profile}-{seed}"))
                controller = CONTROLLERS[cname](rng=random.Random(f"ctrl-{seed}"))
                for row in play_run(controller, bot, story, seed):
                    row.update({"run_id": f"{cname}-{profile}-{seed}",
                                "controller": cname, "bot_type": profile, **bot.params()})
                    rows.append(row)
    df = pd.DataFrame(rows)
    first = ["run_id", "controller", "bot_type", "seed", "room_index"]
    return df[first + [c for c in df.columns if c not in first]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=500, help="runs per controller per bot type")
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--controllers", nargs="+", default=["fixed"], choices=list(CONTROLLERS))
    ap.add_argument("--profiles", nargs="+", default=list(PROFILES), choices=list(PROFILES))
    ap.add_argument("--out", default="data/sim_runs.csv")
    args = ap.parse_args()

    df = simulate(args.controllers, args.profiles, args.games, args.seed_start)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"saved {len(df)} room rows from {df['run_id'].nunique()} runs -> {args.out}")


if __name__ == "__main__":
    main()
