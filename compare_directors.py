"""
Compare directors on the same bots and the same dice rolls (paired comparison).

Use NEW seeds for the final comparison: seeds 0-999 were used to build the expected-HP-loss
table (build_tables.py) and to choose the rule thresholds, so they are training seeds.

Example:
  python compare_directors.py --games 1000 --seed-start 100000 --controllers fixed rule
"""
import argparse
from pathlib import Path

import pandas as pd

from game.controllers import CONTROLLERS
from sanity_check import ORDER, summary
from simulate import simulate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=1000, help="runs per controller per bot type")
    ap.add_argument("--seed-start", type=int, default=100000)
    ap.add_argument("--controllers", nargs="+", default=["fixed", "rule"], choices=list(CONTROLLERS))
    ap.add_argument("--out", default="data/director_comparison.csv")
    args = ap.parse_args()

    df = simulate(args.controllers, ORDER, args.games, args.seed_start)
    table = summary(df)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    print(f"Seeds {args.seed_start}-{args.seed_start + args.games - 1}, {args.games} runs per bot type\n")
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print(table.to_string(index=False))
    overall = df.groupby("controller")["in_band"].mean()
    print("\nIn band, all bot types together:", {c: round(v, 3) for c, v in overall.items()})


if __name__ == "__main__":
    main()
