"""
Train the LinUCB bandit director, record its learning curve, and test it.

1. Training (seeds 0 to TRAIN_SEEDS-1): the bandit plays runs with bot types interleaved
   (beginner, rage_quitter, average, expert, beginner, ...), exploring and learning after every room.
2. Choosing alpha (exploration strength): each candidate is trained the same way, then
   frozen and scored on VALIDATION seeds 50000+. The best one is kept.
3. Test: the frozen bandit vs fixed and rule on the same new seeds as before (100000+).

Outputs: data/bandit_model.npz (+ finale model), data/bandit_learning_curve.csv,
         data/bandit_alpha_choice.csv, data/bandit_comparison.csv,
         figures/bandit_learning_curve.png

Example:  python bandit_experiment.py
"""
import argparse
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # draw straight to a file, no window needed
import matplotlib.pyplot as plt
import pandas as pd

from game.controllers import BanditController
from game.engine import play_run
from game.story import Story
from game.bots import Bot
from sanity_check import ORDER, summary
from simulate import simulate

ALPHAS = [0.1, 0.25, 0.5, 1.0]   # exploration strengths to compare
SMALL_BLOCK = 25                 # runs per learning-curve point during the first EARLY_RUNS runs
EARLY_RUNS = 400
BLOCK = 400                      # runs per learning-curve point after that


def train(alpha, train_seeds):
    """Train a fresh bandit. Output: one row per training room (with its run number)."""
    BanditController.reset(alpha)
    BanditController.learning = True
    story = Story()
    rows = []
    run_number = 0
    for seed in range(train_seeds):
        for profile in ORDER:      # interleave bot types, so the bandit meets every kind of player
            bot = Bot(profile, random.Random(f"bot-{profile}-{seed}"))
            controller = BanditController(rng=random.Random(f"ctrl-{seed}"))
            for row in play_run(controller, bot, story, seed):
                row["run_number"] = run_number
                row["bot_type"] = profile
                rows.append(row)
            run_number += 1
    BanditController.learning = False
    return pd.DataFrame(rows)


def learning_curve(train_rows):
    """In-band share per block of training runs (all bot types together).
    Small blocks (SMALL_BLOCK runs) at the start, where learning is fast, then BLOCK-run blocks.
    Output: table with runs_seen (end of the block) and in_band"""
    run = train_rows["run_number"]
    small_blocks = EARLY_RUNS // SMALL_BLOCK
    block = (run // SMALL_BLOCK).where(run < EARLY_RUNS, small_blocks + (run - EARLY_RUNS) // BLOCK)
    curve = train_rows.groupby(block).agg(in_band=("in_band", "mean"), last_run=("run_number", "max"))
    curve["runs_seen"] = curve["last_run"] + 1
    return curve[["runs_seen", "in_band"]].reset_index(drop=True)


def plot_learning_curve(curve, reference, path):
    """Save the learning curve as a PNG, with fixed and rule as flat reference lines.
    Inputs: curve (runs_seen, in_band), reference = {director name: in-band share}, path"""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(curve["runs_seen"], curve["in_band"], marker="o", markersize=3, label="bandit while learning")
    for name, value in reference.items():
        ax.axhline(value, linestyle="--", linewidth=1, color="grey")
        ax.text(curve["runs_seen"].min(), value + 0.01, f"{name} {value:.1%}", fontsize=9, color="grey")
    ax.set_xscale("log")   # log scale so the fast early learning is visible
    ax.set_xlabel("training runs played (log scale)")
    ax.set_ylabel("share of rooms in band")
    ax.set_title("LinUCB bandit director: learning curve (all bot types)")
    ax.set_ylim(0.3, 0.9)
    ax.legend(loc="lower right")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-seeds", type=int, default=2000, help="seeds; each seed = 4 runs (one per bot type)")
    ap.add_argument("--valid-games", type=int, default=300)
    ap.add_argument("--test-games", type=int, default=1000)
    args = ap.parse_args()

    # 1 + 2: train each alpha, score the frozen bandit on validation seeds
    choice = []
    curves = []
    for alpha in ALPHAS:
        train_rows = train(alpha, args.train_seeds)
        curve = learning_curve(train_rows)
        curve["alpha"] = alpha
        curves.append(curve)
        valid = simulate(["bandit"], ORDER, args.valid_games, seed_start=50000)
        per_bot = valid.groupby("bot_type")["in_band"].mean()
        choice.append({"alpha": alpha, "valid_in_band": round(valid["in_band"].mean(), 4),
                       "valid_worst_bot": round(per_bot.min(), 4),
                       "train_last_block": round(curve["in_band"].iloc[-1], 4)})
        print(f"alpha {alpha}: validation in band {valid['in_band'].mean():.3f}")
    choice = pd.DataFrame(choice)
    best_alpha = choice.sort_values("valid_in_band", ascending=False)["alpha"].iloc[0]
    print(f"\nChosen alpha: {best_alpha}\n")

    # retrain with the chosen alpha and save the model
    final_rows = train(best_alpha, args.train_seeds)
    final_curve = learning_curve(final_rows)
    BanditController.save()
    print("arm usage in training (normal rooms):")
    for (difficulty, help_mode), pulls in zip(BanditController.model.arms, BanditController.model.pulls):
        print(f"  {difficulty:6} {help_mode:9} {pulls}")

    # 3: final test on new seeds, same seeds as the rule-director test
    test = simulate(["fixed", "rule", "bandit"], ORDER, args.test_games, seed_start=100000)
    table = summary(test)
    print(f"\nTest seeds 100000-{100000 + args.test_games - 1}\n")
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print(table.to_string(index=False))
    overall = test.groupby("controller")["in_band"].mean()
    print("\nIn band, all bot types together:", {c: round(v, 3) for c, v in overall.items()})

    reference = {"fixed (test)": overall["fixed"], "rule (test)": overall["rule"]}
    plot_learning_curve(final_curve, reference, "figures/bandit_learning_curve.png")
    print("figure saved -> figures/bandit_learning_curve.png")

    pd.concat(curves).to_csv("data/bandit_learning_curve.csv", index=False)
    choice.to_csv("data/bandit_alpha_choice.csv", index=False)
    table.to_csv("data/bandit_comparison.csv", index=False)


if __name__ == "__main__":
    main()
