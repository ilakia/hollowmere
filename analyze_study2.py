"""
Study 2 analysis: silent vs scripted vs LLM Walt, with the playtest data, following the analysis plan in
STUDY2.md (section 5b, fixed before the playtest).

Reads data/story_runs.csv (one row per room) and data/story_answers.csv (one row per night: ratings,
comprehension, "enjoyed most"). Only playtest players are counted (not PILOT*, GUEST or EXCLUDED_IDS).

Prints:
  1. per Walt version: adjustable rooms in band (3 normal fights + the activity), normal fights and the
     activity on their own, victim weaknesses found, ratings, "how hard" distance from just right
  2. the hypotheses H1-H5: per-player differences, exact one-sided sign tests, Holm-corrected p-values,
     mean differences with bootstrap 95% intervals (seed 42)
  3. exploratory: LLM vs scripted, the activities, hint level at discovery, help presses, comprehension,
     what was most fun, LLM waiting times and fallbacks
Tables are saved to figures/study2_*.csv.

Example:  python analyze_study2.py
"""
import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

RUNS = Path("data/story_runs.csv")
ANSWERS = Path("data/story_answers.csv")
OUT = Path("figures")
SEED = 42
EXCLUDED_IDS = {"GUEST", "VARSHINI"}          # the developer's own test nights
VERSIONS = ["silent", "scripted", "llm"]


def is_playtester(player_id):
    player_id = str(player_id)
    return player_id not in EXCLUDED_IDS and not player_id.upper().startswith("PILOT")


def sign_test_one_sided(differences):
    """Exact one-sided sign test for 'more positive than negative differences' (ties dropped).
    Output: (number positive, number negative, number equal, p-value)."""
    positive = sum(1 for d in differences if d > 0)
    negative = sum(1 for d in differences if d < 0)
    equal = len(differences) - positive - negative
    n = positive + negative
    if n == 0:
        return positive, negative, equal, 1.0
    p = sum(math.comb(n, i) for i in range(positive, n + 1)) / 2 ** n
    return positive, negative, equal, p


def bootstrap_interval(differences, rng, repeats=5000):
    """95% bootstrap interval of the mean difference. Output: (low, high), or (nan, nan) if too few."""
    values = np.array(differences, dtype=float)
    if len(values) < 3:
        return float("nan"), float("nan")
    means = [rng.choice(values, size=len(values), replace=True).mean() for _ in range(repeats)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(p_values):
    """Holm's correction. Input: list of p-values. Output: list of corrected p-values (same order)."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    corrected = [0.0] * len(p_values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        corrected[i] = running
    return corrected


def per_night_table(runs, answers):
    """One row per player and night: the Walt version and every measure of the plan."""
    rows = []
    for run_id, night in runs.groupby("run_id"):
        adjustable = night[night["victim"].isna() & ~night["is_finale"].astype(bool)]
        fights = adjustable[adjustable["activity"].isna()] if "activity" in adjustable else adjustable
        activity = adjustable[adjustable["activity"].notna()] if "activity" in adjustable else adjustable.iloc[0:0]
        victims = night[night["victim"].notna()]
        rows.append({"run_id": run_id, "player_id": str(night["player_id"].iloc[0]), "night": night["night"].iloc[0],
                     "walt": night["walt"].iloc[0], "story_game_number": night["story_game_number"].iloc[0],
                     "adjustable_in_band": adjustable["in_band"].mean(),
                     "fights_in_band": fights["in_band"].mean(),
                     "activity_in_band": activity["in_band"].mean() if len(activity) else np.nan,
                     "weakness_found": victims["weakness_used"].astype(float).mean() if len(victims) else np.nan,
                     "outcome": night["run_outcome"].iloc[0]})
    table = pd.DataFrame(rows)
    if answers is not None and len(answers):
        keep = ["run_id", "fun", "walt_helped", "walt_companion", "difficulty_felt", "enjoyed_most"]
        table = table.merge(answers[[c for c in keep if c in answers.columns]], on="run_id", how="left")
        table["felt_off"] = (table["difficulty_felt"] - 3).abs()       # 0 = just right
    return table


def paired(table, measure, better, worse, lower_is_better=False):
    """Per-player differences between two Walt versions for one measure (better - worse, signed so that
    positive always means 'as the hypothesis expects')."""
    wide = table.pivot_table(index="player_id", columns="walt", values=measure)
    if better not in wide or worse not in wide:
        return []
    diff = (wide[better] - wide[worse]).dropna()
    if lower_is_better:
        diff = -diff
    return list(diff)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--answers", default=str(ANSWERS))
    ap.add_argument("--out", default=str(OUT), help="folder for the tables")
    args = ap.parse_args()
    runs_path, answers_path, out = Path(args.runs), Path(args.answers), Path(args.out)
    if not runs_path.exists():
        print(f"{runs_path} does not exist yet: play some story nights first.")
        return
    runs = pd.read_csv(runs_path)
    runs = runs[(runs["bot_type"] == "human") & runs["player_id"].map(is_playtester)].copy()
    if runs.empty:
        print("No playtest nights yet (pilot and developer IDs are not counted).")
        return
    runs["walt"] = runs["controller"].astype(str).str.replace("story-", "", regex=False)
    if "activity" not in runs:
        runs["activity"] = np.nan
    answers = None
    if answers_path.exists():
        answers = pd.read_csv(answers_path)
        answers = answers[answers["player_id"].map(is_playtester)]
    table = per_night_table(runs, answers)
    rng = np.random.default_rng(SEED)
    print(f"Playtest nights: {len(table)}  ·  players: {table['player_id'].nunique()}")
    print(table.groupby("walt")["run_id"].count().rename("nights per Walt version").to_string(), "\n")

    measures = ["adjustable_in_band", "fights_in_band", "activity_in_band", "weakness_found", "fun",
                "walt_helped", "walt_companion", "felt_off"]
    measures = [m for m in measures if m in table]
    overview = table.groupby("walt")[measures].mean()
    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.float_format", "{:.2f}".format):
        print("1) Per Walt version (means over nights; felt_off: 0 = 'just right'):")
        print(overview, "\n")

        print("2) Hypotheses (within players, one-sided sign tests, Holm-corrected):")
        plan = [("H1", "adjustable_in_band", "llm", "silent", False),
                ("H2", "felt_off", "llm", "silent", True),
                ("H3a", "weakness_found", "scripted", "silent", False),
                ("H3b", "weakness_found", "llm", "silent", False),
                ("H4a", "walt_companion", "llm", "scripted", False),
                ("H4b", "walt_companion", "llm", "silent", False),
                ("H5", "fun", "llm", "silent", False)]
        results = []
        for name, measure, better, worse, lower in plan:
            if measure not in table:
                continue
            diffs = paired(table, measure, better, worse, lower)
            pos, neg, eq, p = sign_test_one_sided(diffs)
            low, high = bootstrap_interval(diffs, rng)
            results.append({"hypothesis": name, "measure": measure, "comparison": f"{better} vs {worse}",
                            "players": len(diffs), "better": pos, "worse": neg, "equal": eq,
                            "mean_difference": np.mean(diffs) if diffs else np.nan,
                            "ci_low": low, "ci_high": high, "p": p})
        hypotheses = pd.DataFrame(results)
        if len(hypotheses):
            hypotheses["p_holm"] = holm(list(hypotheses["p"]))
            print(hypotheses.to_string(index=False), "\n")

        print("3) Exploratory")
        for measure in ("adjustable_in_band", "weakness_found", "walt_companion", "fun"):
            if measure in table:
                diffs = paired(table, measure, "llm", "scripted")
                pos, neg, eq, _ = sign_test_one_sided(diffs)
                print(f"  LLM vs scripted, {measure}: {len(diffs)} players, better {pos}, worse {neg}, equal {eq}, "
                      f"mean difference {np.mean(diffs) if diffs else float('nan'):+.2f}")
        acts = runs[runs["activity"].notna()]
        if len(acts):
            print("\n  Activities per Walt version:")
            print(acts.groupby("walt").agg(activities=("activity", "size"), in_band=("in_band", "mean"),
                                           won=("cleared", "mean"), pressure=("pressure", "mean"),
                                           step_ins=("step_ins", "mean")))
        fights = runs[runs["victim"].notna()]
        if len(fights):
            columns = {c: c for c in ("hint_level_at_use", "help_asks") if c in fights}
            if columns:
                print("\n  Victim fights: hint level when found, 'Walt, help!' presses:")
                print(fights.groupby("walt")[list(columns)].mean())
        if answers is not None and len(answers):
            understood = [c for c in answers.columns if c.startswith("understood_")]
            if understood:
                long = answers.melt(id_vars=["companion"], value_vars=understood, value_name="understood").dropna()
                print("\n  Understood the clue (comprehension question):")
                print(long.groupby("companion")["understood"].mean())
            if "enjoyed_most" in table:
                print("\n  Enjoyed most:")
                print(pd.crosstab(table["walt"], table["enjoyed_most"]))
        llm = runs[runs["walt"] == "llm"]
        if len(llm) and "llm_seconds" in llm:
            print("\n  LLM Walt: model work per room and where decisions came from:")
            print(llm[["llm_calls", "llm_seconds"]].describe().loc[["mean", "50%", "max"]])
            print(llm["decision_source"].value_counts(normalize=True).round(2).to_string())

    out.mkdir(exist_ok=True)
    table.to_csv(out / "study2_nights.csv", index=False)
    overview.to_csv(out / "study2_overview.csv")
    if len(hypotheses):
        hypotheses.to_csv(out / "study2_hypotheses.csv", index=False)
    print(f"\nTables saved to {out}/study2_*.csv")


if __name__ == "__main__":
    main()
