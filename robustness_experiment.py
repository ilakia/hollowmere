"""
Two robustness checks for the directors (no LLM, so the laptop stays cool):

1. Held-out bot type: everything that is learned from bot data (expected-HP-loss table,
   band model, bandit) is re-learned WITHOUT one bot type, then all directors are tested on
   that unseen type. Does a director still help a kind of player it never met?
   (The rule thresholds were tuned on all bot types; that is noted, not re-tuned.)

2. +/-20% sensitivity: the game itself is changed at test time (ghost damage, ghost HP,
   rest healing each 20% lower or higher) while every director keeps what it learned on the
   original game. Do the results still hold if the simulator's numbers are a bit wrong?

Directors: fixed, rule, bandit, predictor. Test seeds 100000+.
Outputs: data/heldout_results.csv, data/sensitivity_results.csv

Example:  python robustness_experiment.py --games 300
"""
import argparse
import copy

import pandas as pd
from sklearn.linear_model import LogisticRegression

from bandit_experiment import train as train_bandit
from failure_predictor import build_features
from game import config as C
from game import risk, skill
from game.controllers import BanditController
from sanity_check import ORDER
from simulate import simulate

DIRECTORS = ["fixed", "rule", "bandit", "predictor"]
BANDIT_ALPHA = 1.0          # chosen on validation seeds in bandit_experiment.py
BANDIT_TRAIN_SEEDS = 2000
TEST_SEED_START = 100000


def learn_everything(train_rows, profiles):
    """Re-learn the expected-HP-loss table, the band model and the bandit from the given data
    and bot types, and put them in place of the saved ones (only for this script)."""
    table = (train_rows.groupby(["beat_id", "difficulty", "help_mode"])["hp_lost_ratio"].mean()).to_dict()
    skill._table_cache = table
    X, _, band = build_features(train_rows)
    band_model = LogisticRegression(max_iter=1000)
    band_model.fit(X, band)
    risk._band_model = band_model
    train_bandit(BANDIT_ALPHA, BANDIT_TRAIN_SEEDS, profiles)


def in_band_table(df):
    """In-band share per director (columns) and bot type (rows)."""
    return df.pivot_table(index="bot_type", columns="controller", values="in_band", aggfunc="mean")[DIRECTORS]


def heldout_check(random_rows, games):
    rows = []
    for held_out in ORDER:
        seen = [p for p in ORDER if p != held_out]
        learn_everything(random_rows[random_rows["bot_type"].isin(seen)], seen)
        test = simulate(DIRECTORS, [held_out], games, seed_start=TEST_SEED_START)
        result = test.groupby("controller")["in_band"].mean()
        rows.append({"held_out": held_out, **{d: round(result[d], 3) for d in DIRECTORS}})
        print(f"held out {held_out:13}: " + ", ".join(f"{d} {result[d]:.3f}" for d in DIRECTORS), flush=True)
    return pd.DataFrame(rows)


def sensitivity_check(random_rows, games):
    learn_everything(random_rows, ORDER)                 # learned on the original game, all bot types
    original_enemies = copy.deepcopy(C.ENEMY_TYPES)
    original_rest = C.REST_HEAL
    changes = [("original", None, 1.0)]
    for factor in (0.8, 1.2):
        changes += [("ghost damage", "damage", factor), ("ghost HP", "hp", factor), ("rest heal", "rest", factor)]
    rows = []
    for name, what, factor in changes:
        for kind, values in original_enemies.items():     # start every condition from the original game
            C.ENEMY_TYPES[kind] = dict(values)
        C.REST_HEAL = original_rest
        if what in ("damage", "hp"):
            for kind in C.ENEMY_TYPES:
                C.ENEMY_TYPES[kind][what] = original_enemies[kind][what] * factor
                if what == "damage" and "special_damage" in C.ENEMY_TYPES[kind]:
                    C.ENEMY_TYPES[kind]["special_damage"] = original_enemies[kind]["special_damage"] * factor
        if what == "rest":
            C.REST_HEAL = original_rest * factor
        test = simulate(DIRECTORS, ORDER, games, seed_start=TEST_SEED_START)
        result = test.groupby("controller")["in_band"].mean()
        label = name if what is None else f"{name} x{factor}"
        rows.append({"condition": label, **{d: round(result[d], 3) for d in DIRECTORS}})
        print(f"{label:18}: " + ", ".join(f"{d} {result[d]:.3f}" for d in DIRECTORS), flush=True)
    for kind, values in original_enemies.items():         # put the original game back
        C.ENEMY_TYPES[kind] = dict(values)
    C.REST_HEAL = original_rest
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=300, help="test runs per bot type per condition")
    ap.add_argument("--data", default="data/sim_runs.csv")
    args = ap.parse_args()

    random_rows = pd.read_csv(args.data)
    random_rows = random_rows[random_rows["controller"] == "random"]

    print("1. Held-out bot type (in band on the unseen type)")
    heldout = heldout_check(random_rows, args.games)
    heldout.to_csv("data/heldout_results.csv", index=False)

    print("\n2. +/-20% sensitivity (in band, all bot types; directors learned on the original game)")
    sensitivity = sensitivity_check(random_rows, args.games)
    sensitivity.to_csv("data/sensitivity_results.csv", index=False)


if __name__ == "__main__":
    main()
