"""
Failure predictor: before a room is played, how likely is it that the player fails it?
"Fail" = the room ends up too_hard (a death, or more than 70% of the available HP lost).

Inputs are only what a director can see BEFORE the room (never the hidden true_* skill):
  the player's situation (HP, potions, deaths so far, skill estimate, last room)
  and the director's planned choice (room threat, difficulty, Walt mode, expected HP loss).

Training data: the RANDOM director's runs in data/sim_runs.csv (seeds 0-999), because its
choices do not depend on the player. Testing: new seeds the model has never seen, once with
the random director and once with the rule director (a different style of choices).

Example:  python failure_predictor.py
"""
import argparse

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from game import config as C
from game.controllers import THREAT_ORDER
from game.skill import SkillEstimator, load_expected_table
from game.story import Story
from simulate import simulate

SEED = 42
DIFFICULTY_ORDER = ["easy", "normal", "hard"]
FEATURES = ["room_index", "hp_share", "potions_left", "deaths_so_far", "skill_estimate",
            "last_hp_lost", "died_last_room", "threat", "difficulty_level",
            "help_stay_back", "help_hint", "help_heal", "help_fight", "expected_hp_lost"]


def build_features(df):
    """Turn room rows into one feature row per room, using only information from BEFORE the room.
    Input:  df = room rows from simulate() or data/sim_runs.csv
    Output: (X, y) = feature table and label (1 = room failed, 0 = not failed)"""
    table = load_expected_table()
    threat_of = {b["id"]: b["threat"] for b in Story().beats}
    df = df.sort_values(["run_id", "room_index"])
    rows = []
    for _, run in df.groupby("run_id", sort=False):
        estimator = SkillEstimator(table)
        potions_left = C.POTIONS_PER_RUN
        deaths_so_far = 0
        last_hp_lost = 0.0
        died_last_room = 0
        for room in run.to_dict("records"):
            key = (room["beat_id"], room["difficulty"], room["help_mode"])
            rows.append({
                "room_index": room["room_index"],
                "hp_share": room["hp_start"] / C.PLAYER_MAX_HP,
                "potions_left": potions_left,
                "deaths_so_far": deaths_so_far,
                "skill_estimate": estimator.estimate,       # estimate BEFORE this room
                "last_hp_lost": last_hp_lost,
                "died_last_room": died_last_room,
                "threat": THREAT_ORDER.index(threat_of[room["beat_id"]]),
                "difficulty_level": DIFFICULTY_ORDER.index(room["difficulty"]),
                "help_stay_back": int(room["help_mode"] == "stay_back"),
                "help_hint": int(room["help_mode"] == "hint"),
                "help_heal": int(room["help_mode"] == "heal"),
                "help_fight": int(room["help_mode"] == "fight"),
                "expected_hp_lost": table.get(key, estimator.fallback),
                "failed": int(room["band"] == "too_hard"),
            })
            # only now, after the room, update what the director knows
            estimator.update(room)
            potions_left -= room["potions_used"]
            deaths_so_far += room["deaths"]
            last_hp_lost = room["hp_lost_ratio"]
            died_last_room = int(room["deaths"] > 0)
    out = pd.DataFrame(rows)
    return out[FEATURES], out["failed"]


def evaluate(name, model, X, y):
    """Print how well a model ranks and calibrates failure risk on one test set.
    Output: dict with AUC (1.0 = perfect ranking, 0.5 = coin flip) and Brier score (lower = better)"""
    p = model.predict_proba(X)[:, 1]
    return {"model": name, "AUC": round(roc_auc_score(y, p), 3),
            "Brier": round(brier_score_loss(y, p), 4),
            "mean_predicted": round(p.mean(), 3), "actual_fail_rate": round(y.mean(), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sim_runs.csv")
    ap.add_argument("--test-games", type=int, default=500)
    ap.add_argument("--test-seed-start", type=int, default=200000)
    args = ap.parse_args()

    # training data: random director only, seeds 0-999
    train = pd.read_csv(args.data)
    train = train[train["controller"] == "random"]
    X_train, y_train = build_features(train)

    # test data: new seeds, generated now, never seen in training or tuning
    profiles = ["beginner", "rage_quitter", "average", "expert"]
    test = simulate(["random", "rule"], profiles, args.test_games, args.test_seed_start)
    tests = {}
    for ctrl in ["random", "rule"]:
        tests[ctrl] = build_features(test[test["controller"] == ctrl])

    print(f"Training rooms: {len(y_train)} (fail rate {y_train.mean():.3f}), "
          f"test seeds {args.test_seed_start}-{args.test_seed_start + args.test_games - 1}\n")

    # model 1: only the expected-HP-loss table (what the rule director already knows)
    simple = LogisticRegression(max_iter=1000)
    simple.fit(X_train[["expected_hp_lost"]], y_train)
    # model 2: logistic regression on all features (a straight-line model)
    logistic = LogisticRegression(max_iter=1000)
    logistic.fit(X_train, y_train)
    # model 3: gradient boosting (many small decision trees, can learn curves and interactions)
    # library defaults kept: max_iter=100 trees, learning_rate=0.1; random_state fixes the result
    boosting = HistGradientBoostingClassifier(random_state=SEED)
    boosting.fit(X_train, y_train)

    results = []
    for ctrl, (X_test, y_test) in tests.items():
        for name, model, cols in [("expected table only", simple, ["expected_hp_lost"]),
                                  ("logistic regression", logistic, FEATURES),
                                  ("gradient boosting", boosting, FEATURES)]:
            r = evaluate(name, model, X_test[cols], y_test)
            r["test_director"] = ctrl
            results.append(r)
    res = pd.DataFrame(results)[["test_director", "model", "AUC", "Brier",
                                 "mean_predicted", "actual_fail_rate"]]
    print(res.to_string(index=False))
    res.to_csv("data/failure_predictor_results.csv", index=False)

    # which inputs matter: shuffle one feature at a time on the test set and see how much AUC drops
    X_test, y_test = tests["random"]
    imp = permutation_importance(boosting, X_test, y_test, scoring="roc_auc",
                                 n_repeats=5, random_state=SEED)
    importance = pd.Series(imp.importances_mean, index=FEATURES).sort_values(ascending=False)
    print("\nFeature importance (AUC drop when the feature is shuffled, random-director test set):")
    print(importance.round(3).to_string())


if __name__ == "__main__":
    main()
