"""
Build the expected-HP-loss table for the skill estimator (game/skill.py).

For every (attraction, difficulty, Walt mode) it stores the average hp_lost_ratio of the
RANDOM director's runs. Only the random director is used, because its choices do not depend
on the player, so the averages are not biased by any director's habits.

Example:
  python simulate.py --games 1000 --controllers fixed random   # makes data/sim_runs.csv
  python build_tables.py                                         # makes game/expected_hp_lost.csv
"""
import argparse

import pandas as pd

from game.skill import TABLE_PATH


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sim_runs.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    df = df[df["controller"] == "random"]
    table = (df.groupby(["beat_id", "difficulty", "help_mode"])
               .agg(rooms=("hp_lost_ratio", "size"), expected_hp_lost=("hp_lost_ratio", "mean"))
               .reset_index())
    table["expected_hp_lost"] = table["expected_hp_lost"].round(4)
    table.to_csv(TABLE_PATH, index=False)
    print(f"saved {len(table)} combinations (fewest rooms per combination: {table['rooms'].min()}) "
          f"from seeds {df['seed'].min()}-{df['seed'].max()} -> {TABLE_PATH}")


if __name__ == "__main__":
    main()
