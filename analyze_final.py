"""
Final analysis of Study 2 (bots + the developer's own play nights), as used in REPORT.md.

Why this script: the real playtest with friends did not take place before the deadline, so the study is
finished with (1) the bot test on the playtest nights and (2) the 16 nights the developer played herself
while building and piloting the game. Part 2 is a single-player case study, not evidence for the hypotheses.

Inputs (all in data/, which is not in git; each folder was made with story_brains_check.py):
  data/llm_batches_v7/   final bot test: playtest nights, final settings, seeds 640000-640001
  data/llm_batches_v3/   development test (old vs new LLM Walt), two-activity bot plan, seeds 600000
  data/llm_batches_v5/   first final test, two-activity bot plan, seeds 620000
  data/llm_batches_v6/   playtest nights before the last two changes, seeds 630000
  data/story_runs.csv, data/story_answers.csv   the developer's own nights (IDs VARSHINI, PILOT1-7)
Outputs: tables figures/final_*.csv, figures figures/final_*.png, and a printed summary.

Example:  python analyze_final.py
"""
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                          # draw to files only (no window needed)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("figures")
SEED = 42
BOOTSTRAP_REPEATS = 2000                       # enough for stable 95% intervals; more only costs time
VERSIONS = ["silent", "scripted", "llm", "predictor"]
LABELS = {"silent": "Silent Walt", "scripted": "Scripted Walt", "llm": "LLM Walt", "predictor": "Predictor only"}
COLORS = {"silent": "#9e9e9e", "scripted": "#4a7fb5", "llm": "#d9822b", "predictor": "#5a9e6f"}
NIGHT_KEY = ["seed", "bot_type", "player", "night"]   # one bot night: same key = same bot, same luck
OWN_IDS = ("VARSHINI", "PILOT")                # the developer's own nights


def load_folder(folder):
    """All bot CSVs in one folder, with a 'kind' column (fight / activity / victim / finale).
    Input: folder path. Output: one DataFrame (one row per room)."""
    parts = []
    for path in sorted(glob.glob(str(folder) + "/*.csv")):
        if "oldC" in path:                     # the before-fix Night C check is not part of a test
            continue
        part = pd.read_csv(path)
        if "llm_old" in path:
            part["companion"] = "llm_old"
        parts.append(part)
    rooms = pd.concat(parts, ignore_index=True)
    return add_kind(rooms)


def add_kind(rooms):
    """Label every room as fight, activity, victim or finale. Input/output: DataFrame."""
    rooms["kind"] = "fight"
    rooms.loc[rooms["victim"].notna(), "kind"] = "victim"
    rooms.loc[rooms["activity"].notna(), "kind"] = "activity"
    rooms.loc[rooms["is_finale"].astype(bool), "kind"] = "finale"
    return rooms


def adjustable(rooms):
    """Only the rooms where Walt chooses the difficulty and the band is the right measure (H1):
    normal fights and activities. Input/output: DataFrame."""
    return rooms[rooms["kind"].isin(["fight", "activity"])]


def bootstrap_mean(night_values, rng):
    """95% interval of a mean, resampling whole nights (rooms of one night are not independent).
    Input: one value per night. Output: (low, high)."""
    values = np.array(night_values, dtype=float)
    means = []
    for _ in range(BOOTSTRAP_REPEATS):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(sample.mean())
    return np.percentile(means, 2.5), np.percentile(means, 97.5)


def version_table(rooms, rng):
    """Per Walt version: share of adjustable rooms in band (with a 95% interval over nights), normal fights,
    activities, too easy / too hard, and weaknesses found by the 'listen' bots (H3).
    Input: bot rooms. Output: DataFrame, one row per version."""
    adj = adjustable(rooms)
    rows = []
    for version in VERSIONS:
        mine = adj[adj["companion"] == version]
        if mine.empty:
            continue
        per_night = mine.groupby(NIGHT_KEY)["in_band"].mean()      # one value per bot night
        low, high = bootstrap_mean(per_night, rng)
        victims = rooms[(rooms["companion"] == version) & (rooms["kind"] == "victim") & (rooms["player"] == "listen")]
        rows.append({"version": version,
                     "adjustable_in_band": mine["in_band"].mean(),
                     "ci_low": low, "ci_high": high,
                     "fights_in_band": mine[mine["kind"] == "fight"]["in_band"].mean(),
                     "activities_in_band": mine[mine["kind"] == "activity"]["in_band"].mean(),
                     "too_easy": (mine["band"] == "too_easy").mean(),
                     "too_hard": (mine["band"] == "too_hard").mean(),
                     "weakness_found_listen": victims["weakness_used"].astype(float).mean(),
                     "rooms": len(mine), "nights": len(per_night)})
    return pd.DataFrame(rows).set_index("version")


def paired_differences(rooms, rng):
    """LLM Walt minus each other version, night by night on the SAME bot nights (same seed, bot type,
    player type and night), so luck cancels out. Output: DataFrame with the mean difference, a 95% interval
    and how many nights LLM Walt was better / worse / equal."""
    adj = adjustable(rooms)
    per_night = adj.groupby(["companion"] + NIGHT_KEY)["in_band"].mean().unstack("companion")
    rows = []
    for other in ["silent", "scripted", "predictor"]:
        both = per_night[["llm", other]].dropna()
        diff = both["llm"] - both[other]
        low, high = bootstrap_mean(diff, rng)
        rows.append({"comparison": f"LLM - {other}", "mean_difference": diff.mean(), "ci_low": low,
                     "ci_high": high, "llm_better": int((diff > 0).sum()), "llm_worse": int((diff < 0).sum()),
                     "equal": int((diff == 0).sum()), "nights": len(diff)})
    return pd.DataFrame(rows).set_index("comparison")


def stage_table():
    """How LLM Walt developed over the four bot tests (adjustable rooms in band per version).
    Output: DataFrame, one row per test stage."""
    stages = [("1 development (2-activity plan, old LLM)", "data/llm_batches_v3", "llm_old"),
              ("2 development (2-activity plan, new LLM)", "data/llm_batches_v3", "llm"),
              ("3 first final (2-activity plan)", "data/llm_batches_v5", "llm"),
              ("4 playtest nights, before room fixes", "data/llm_batches_v6", "llm"),
              ("5 playtest nights, final", "data/llm_batches_v7", "llm")]
    rows = []
    for name, folder, llm_name in stages:
        if not Path(folder).exists():
            continue
        rooms = load_folder(folder)                # in v3, the old version's files are labelled "llm_old"
        adj = adjustable(rooms)
        row = {"stage": name}
        for version in ["silent", "scripted", "predictor"]:
            row[version] = adj[adj["companion"] == version]["in_band"].mean()
        row["llm"] = adj[adj["companion"] == llm_name]["in_band"].mean()
        rows.append(row)
    return pd.DataFrame(rows).set_index("stage")


def own_nights():
    """The developer's own nights: one row per night with the Walt version, adjustable rooms in band and
    the answers given after the night. Output: (nights table, room rows)."""
    runs = pd.read_csv("data/story_runs.csv")
    runs = runs[runs["player_id"].astype(str).str.upper().str.startswith(OWN_IDS)].copy()
    runs["walt"] = runs["controller"].astype(str).str.replace("story-", "", regex=False)
    runs = add_kind(runs)
    rows = []
    for run_id, night in runs.groupby("run_id"):
        adj = adjustable(night)
        rows.append({"run_id": run_id, "player_id": night["player_id"].iloc[0], "night": night["night"].iloc[0],
                     "walt": night["walt"].iloc[0], "adjustable_in_band": adj["in_band"].mean(),
                     "adjustable_rooms": len(adj), "outcome": night["run_outcome"].iloc[0]})
    nights = pd.DataFrame(rows)
    answers_path = Path("data/story_answers.csv")
    if answers_path.exists():
        answers = pd.read_csv(answers_path)
        keep = ["run_id", "fun", "walt_helped", "walt_companion", "difficulty_felt", "enjoyed_most"]
        nights = nights.merge(answers[keep], on="run_id", how="left")
    return nights, runs


def plot_versions(table, path):
    """Bar chart: adjustable rooms in band per version with 95% intervals."""
    fig, ax = plt.subplots(figsize=(6.5, 4))
    names = list(table.index)
    values = table["adjustable_in_band"] * 100
    errors = [(table["adjustable_in_band"] - table["ci_low"]) * 100, (table["ci_high"] - table["adjustable_in_band"]) * 100]
    ax.bar([LABELS[n] for n in names], values, yerr=errors, capsize=5, color=[COLORS[n] for n in names])
    for i, value in enumerate(values):
        ax.text(i, value / 2, f"{value:.0f}%", ha="center", color="white", fontweight="bold")   # inside the bar
    ax.set_ylabel("Adjustable rooms in band (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Bots on the playtest nights (final settings)\n95% intervals over bot nights")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_by_night(rooms, path):
    """Lines: adjustable rooms in band per night (A, B, C) for each version."""
    adj = adjustable(rooms)
    table = adj.pivot_table(index="night", columns="companion", values="in_band", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for version in VERSIONS:
        if version in table:
            ax.plot(table.index, table[version] * 100, marker="o", label=LABELS[version], color=COLORS[version])
    ax.set_xlabel("Night")
    ax.set_ylabel("Adjustable rooms in band (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.set_title("Per night (bots, final settings)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_stages(stages, path):
    """Lines: how each version scored in each bot test stage (shows what the changes did)."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(stages))
    for version in VERSIONS:
        ax.plot(x, stages[version] * 100, marker="o", label=LABELS[version], color=COLORS[version])
    ax.set_xticks(list(x))
    ax.set_xticklabels([s.split(" ", 1)[0] for s in stages.index])
    ax.set_xlabel("Bot test stage (see REPORT.md)")
    ax.set_ylabel("Adjustable rooms in band (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.set_title("LLM Walt over the bot test stages")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_own(nights, path):
    """Dots: the developer's own nights, rooms in band per night, by Walt version."""
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for i, version in enumerate(["scripted", "llm"]):
        mine = nights[nights["walt"] == version]
        jitter = np.linspace(-0.12, 0.12, len(mine)) if len(mine) > 1 else [0]
        ax.scatter([i + j for j in jitter], mine["adjustable_in_band"] * 100, color=COLORS[version], s=50)
        ax.hlines(mine["adjustable_in_band"].mean() * 100, i - 0.25, i + 0.25, color="black")
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"Scripted Walt ({(nights['walt'] == 'scripted').sum()} nights)",
                        f"LLM Walt ({(nights['walt'] == 'llm').sum()} nights)"])
    ax.set_ylabel("Adjustable rooms in band (%)")
    ax.set_ylim(0, 105)
    ax.set_title("One real player (the developer): own nights\nline = mean; not a test")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    rng = np.random.default_rng(SEED)
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", "{:.2f}".format)

    # 1) the final bot test
    final = load_folder("data/llm_batches_v7")
    versions = version_table(final, rng)
    paired = paired_differences(final, rng)
    by_night = adjustable(final).pivot_table(index="companion", columns="night", values="in_band").reindex(VERSIONS)
    by_bot = adjustable(final).pivot_table(index="companion", columns="bot_type", values="in_band").reindex(VERSIONS)
    llm = final[final["companion"] == "llm"]
    llm_facts = {"own_sentence": llm["walt_say"].notna().mean(),
                 "corrected": (llm["decision_source"] == "llm_corrected").mean(),
                 "fallback": (llm["decision_source"] == "fallback").mean(),
                 "timeout": (llm["decision_source"] == "timeout").mean(),
                 "model_seconds_per_room": llm["llm_seconds"].mean()}
    print("1) FINAL BOT TEST (playtest nights, final settings)")
    print(versions, "\n")
    print("LLM Walt vs the others, paired on the same bot nights:")
    print(paired, "\n")
    print("Per night:\n", by_night, "\n")
    print("Per bot type:\n", by_bot, "\n")
    print("LLM Walt:", {k: round(v, 2) for k, v in llm_facts.items()}, "\n")

    # 2) the test stages
    stages = stage_table()
    print("2) BOT TEST STAGES (adjustable rooms in band)")
    print(stages, "\n")

    # 3) the developer's own nights
    nights, own_rooms = own_nights()
    print("3) OWN NIGHTS (one real player, the developer; not a test)")
    print(nights.drop(columns=["run_id"]).to_string(index=False), "\n")
    own_summary = nights.groupby("walt").agg(nights=("run_id", "size"), adjustable_in_band=("adjustable_in_band", "mean"),
                                             fun=("fun", "mean"), walt_helped=("walt_helped", "mean"),
                                             walt_companion=("walt_companion", "mean"),
                                             difficulty_felt=("difficulty_felt", "mean"))
    print(own_summary, "\n")
    own_llm = own_rooms[own_rooms["walt"] == "llm"]
    print("Own LLM nights: decision sources", own_llm["decision_source"].value_counts().to_dict(),
          "· own sentence", round(own_llm["walt_say"].notna().mean(), 2))
    print("Enjoyed most:", nights["enjoyed_most"].value_counts().to_dict())

    # 4) save tables and figures
    versions.to_csv(OUT / "final_versions.csv")
    paired.to_csv(OUT / "final_paired.csv")
    by_night.to_csv(OUT / "final_by_night.csv")
    by_bot.to_csv(OUT / "final_by_bot_type.csv")
    stages.to_csv(OUT / "final_stages.csv")
    nights.to_csv(OUT / "final_own_nights.csv", index=False)
    own_summary.to_csv(OUT / "final_own_summary.csv")
    plot_versions(versions, OUT / "final_versions.png")
    plot_by_night(final, OUT / "final_by_night.png")
    plot_stages(stages, OUT / "final_stages.png")
    plot_own(nights, OUT / "final_own_nights.png")
    print(f"\nTables and figures saved to {OUT}/final_*")


if __name__ == "__main__":
    main()
