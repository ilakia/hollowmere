"""
Study 2 analysis: silent vs scripted vs LLM Walt, with the playtest data.

Reads data/story_runs.csv (one row per room) and data/story_answers.csv (one row per night: ratings and
comprehension answers), keeps human players only, and prints per Walt version:
  1. Difficulty (Study 1's measure, now with humans): share of NORMAL rooms in band / too hard / too easy,
     plus how hard the night felt (question, 3 = just right)
  2. Discovery (victim fights): weakness found, how fast, how much Walt had to reveal (hint level when it
     was found), "Walt, help!" presses, and whether the player understood the clue (comprehension question)
  3. Experience: fun, "Walt helped", "Walt felt like a real companion" (1-5)
  4. LLM Walt only: model calls and seconds per room, fallbacks
Then the within-player comparison: for every player who played two versions, the difference in fun /
companion rating, with an exact sign test (how many players preferred LLM Walt). With 9-15 players this
is descriptive: small effects cannot be shown, so report the numbers and the direction honestly.

Example:  python analyze_study2.py              (tables are also saved to figures/study2_*.csv)
"""
import math
from pathlib import Path

import pandas as pd

RUNS = Path("data/story_runs.csv")
ANSWERS = Path("data/story_answers.csv")
OUT = Path("figures")
VERSIONS = ["silent", "scripted", "llm"]


def sign_test(differences):
    """Exact two-sided sign test. Input: list of paired differences (ties are dropped).
    Output: (number positive, number negative, p-value)."""
    positive = sum(1 for d in differences if d > 0)
    negative = sum(1 for d in differences if d < 0)
    n = positive + negative
    if n == 0:
        return 0, 0, 1.0
    k = min(positive, negative)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return positive, negative, min(1.0, 2 * tail)


def companion_of(run_id_series, controller_series):
    """The Walt version of a night, from the saved controller name ("story-llm" -> "llm")."""
    return controller_series.astype(str).str.replace("story-", "", regex=False)


def main():
    if not RUNS.exists():
        print(f"{RUNS} does not exist yet: play some story nights first.")
        return
    runs = pd.read_csv(RUNS)
    runs = runs[runs["bot_type"] == "human"].copy()
    runs["walt"] = companion_of(runs["run_id"], runs["controller"])
    if "player_id" in runs:
        runs = runs[runs["player_id"].astype(str) != "GUEST"]
    print(f"Human story nights: {runs['run_id'].nunique()}  ·  players: {runs['player_id'].nunique()}")
    print(runs.groupby("walt")["run_id"].nunique().rename("nights per Walt version").to_string(), "\n")

    # 1) difficulty: normal rooms (not victims, not the finale), same band rule as Study 1
    normal = runs[runs["victim"].isna() & ~runs["is_finale"].astype(bool)].copy()
    normal["too_hard"] = normal["band"] == "too_hard"
    normal["too_easy"] = normal["band"] == "too_easy"
    difficulty = normal.groupby("walt").agg(rooms=("band", "size"), in_band=("in_band", "mean"),
                                            too_hard=("too_hard", "mean"), too_easy=("too_easy", "mean"))

    # 2) discovery: victim fights
    fights = runs[runs["victim"].notna()].copy()
    for column in ("hint_level_at_use", "help_asks", "turn_first_used"):
        if column not in fights:
            fights[column] = float("nan")
    discovery = fights.groupby("walt").agg(fights=("victim", "size"), weakness_found=("weakness_used", "mean"),
                                           turn_found=("turn_first_used", "mean"),
                                           hint_level_at_use=("hint_level_at_use", "mean"),
                                           help_asks=("help_asks", "mean"))

    tables = {"difficulty": difficulty, "discovery": discovery}
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print("1) Difficulty, normal rooms (share in band = Study 1's measure):")
        print(difficulty, "\n")
        print("2) Discovery, victim fights:")
        print(discovery, "\n")

        if ANSWERS.exists():
            answers = pd.read_csv(ANSWERS)
            answers = answers[answers["player_id"].astype(str) != "GUEST"]
            understood = [c for c in answers.columns if c.startswith("understood_")]
            long = answers.melt(id_vars=["companion"], value_vars=understood, value_name="understood").dropna()
            experience = answers.groupby("companion").agg(nights=("fun", "size"), fun=("fun", "mean"),
                                                          walt_helped=("walt_helped", "mean"),
                                                          walt_companion=("walt_companion", "mean"),
                                                          difficulty_felt=("difficulty_felt", "mean"))
            experience["understood_clue"] = long.groupby("companion")["understood"].mean()
            tables["experience"] = experience
            print("3) Experience and understanding (ratings 1-5; difficulty_felt 3 = just right):")
            print(experience, "\n")

            print("Within-player comparison (each player against themself, exact sign test):")
            for rating in ("fun", "walt_companion", "walt_helped"):
                wide = answers.pivot_table(index="player_id", columns="companion", values=rating)
                for other in ("silent", "scripted"):
                    if "llm" in wide and other in wide:
                        diffs = (wide["llm"] - wide[other]).dropna()
                        pos, neg, p = sign_test(list(diffs))
                        print(f"  {rating:15s} LLM vs {other:8s}: {len(diffs)} players, LLM higher {pos}, "
                              f"lower {neg}, mean difference {diffs.mean():+.2f}, sign test p = {p:.3f}")
            print()
        else:
            print(f"3) {ANSWERS} does not exist yet (questions are asked after each story night).\n")

        llm = runs[runs["walt"] == "llm"]
        if len(llm) and "llm_seconds" in llm:
            print("4) LLM Walt: model work per room (seconds include cached answers as 0):")
            print(llm[["llm_calls", "llm_cache_hits", "llm_seconds"]].describe().loc[["mean", "50%", "max"]])
            if "decision_source" in llm:
                print(llm["decision_source"].value_counts(normalize=True).round(2).to_string())
            if "coach_fallbacks" in llm:
                print(f"hint answers that failed the check (fallbacks) per victim fight: "
                      f"{llm['coach_fallbacks'].dropna().mean():.2f}")

    OUT.mkdir(exist_ok=True)
    for name, table in tables.items():
        table.to_csv(OUT / f"study2_{name}.csv")
    print(f"\nTables saved to {OUT}/study2_*.csv")


if __name__ == "__main__":
    main()
