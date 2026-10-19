"""
Checks that the game is working before any AI is built on top of it.

1. Determinism: the same seed must give exactly the same result.
2. Skill ordering: beginners must struggle more than experts.
3. Summary table: where each bot type lands relative to the target band.

Example:  python sanity_check.py --games 500
"""
import argparse

import pandas as pd

from simulate import simulate

ORDER = ["beginner", "rage_quitter", "average", "expert"]


def check_determinism():
    a = simulate(["fixed", "random"], ["average"], games=20)
    b = simulate(["fixed", "random"], ["average"], games=20)
    assert a.equals(b), "same seeds gave different results"
    print("1. Determinism: OK (same seeds -> identical data)")


def summary(df):
    runs = df.groupby("run_id").first()
    per_run = runs.groupby(["controller", "bot_type"]).agg(
        runs=("run_outcome", "size"),
        escaped=("run_outcome", lambda s: (s == "escaped").mean()),
        quit=("run_outcome", lambda s: (s == "quit").mean()),
    )
    per_room = df.groupby(["controller", "bot_type"]).agg(
        deaths_per_room=("deaths", "mean"),
        hp_lost=("hp_lost_ratio", "median"),
        too_easy=("band", lambda s: (s == "too_easy").mean()),
        in_band=("band", lambda s: (s == "in_band").mean()),
        too_hard=("band", lambda s: (s == "too_hard").mean()),
    )
    finale = df[df["is_finale"]].groupby(["controller", "bot_type"]).agg(
        finale_close_win=("band", lambda s: (s == "in_band").mean()),
    )
    out = per_run.join(per_room).join(finale).reset_index()
    out["bot_type"] = pd.Categorical(out["bot_type"], ORDER, ordered=True)
    return out.sort_values(["controller", "bot_type"])


def check_skill_order(table):
    for ctrl, t in table.groupby("controller"):
        t = t.set_index("bot_type")
        ok = (t.loc["beginner", "deaths_per_room"] > t.loc["average", "deaths_per_room"]
              > t.loc["expert", "deaths_per_room"])
        print(f"2. Skill ordering [{ctrl}]: {'OK' if ok else 'FAILED'} "
              f"(deaths per room: beginner {t.loc['beginner', 'deaths_per_room']:.2f}, "
              f"average {t.loc['average', 'deaths_per_room']:.2f}, "
              f"expert {t.loc['expert', 'deaths_per_room']:.2f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=500)
    args = ap.parse_args()

    check_determinism()
    df = simulate(["fixed", "random"], ORDER, games=args.games)
    table = summary(df)
    check_skill_order(table)
    print("\n3. Summary (rates are shares, hp_lost is the median per room)\n")
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
