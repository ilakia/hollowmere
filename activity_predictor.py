"""
Train and test the activity band model (game/activity_risk.py) for LLM Walt's activity decisions.

Data: whole story nights with activities, played by bots (beginner, average, expert) with the RANDOM
data Walt (random difficulty and help, never steps in), so the choices do not depend on the player,
as for Study 1's band model. Every activity row has what Walt knew before it (skill estimate, HP,
last room) and how it ended (the band).

Training seeds 500000-500xxx, test seeds 510000+ (never seen in training).
Models compared on the test nights (log loss, lower is better; accuracy):
  - always the training shares (no information)
  - only the expected pressure of an average player
  - logistic regression on all features (the one saved, like Study 1's band model)
Also a calibration check: predicted vs real share in band.

Example:  python activity_predictor.py --nights 300
"""
import argparse
import random

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss

from game.activity_risk import ACTIVITY_FEATURES, activity_features, save_activity_model
from game.bots import Bot
from game.story_mode import DATA_BRAINS, load_skill_table, play_night
from game.victims import NIGHTS

PROFILES = ("beginner", "average", "expert")


def collect(first_seed, nights):
    """Play random-Walt nights. Output: one row per activity (features + band)."""
    table, fallback = load_skill_table()
    rows = []
    for night in NIGHTS:
        for profile in PROFILES:
            for seed in range(first_seed, first_seed + nights):
                bot = Bot(profile, random.Random(f"bot-{profile}-{seed}"))
                brain = DATA_BRAINS["random"](random.Random(f"random-walt-{night}-{profile}-{seed}"))
                for r in play_night(night, brain, bot, seed, with_activities=True):
                    if not r.get("activity"):
                        continue
                    features = activity_features(r["activity"], r["start_difficulty"], r["start_help"],
                                                 r["skill_before"], r["hp_before"], r["last_hp_lost"], table, fallback)
                    features.update({"band": r["band"], "bot_type": profile, "activity": r["activity"]})
                    rows.append(features)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nights", type=int, default=300, help="training nights per night x bot type")
    args = ap.parse_args()
    train = collect(500000, args.nights)
    test = collect(510000, max(50, args.nights // 3))
    print(f"Activities: {len(train)} for training, {len(test)} for testing")
    print("Band shares in training:", train["band"].value_counts(normalize=True).round(2).to_dict())
    classes = sorted(train["band"].unique())

    shares = train["band"].value_counts(normalize=True).reindex(classes).values
    base = np.tile(shares, (len(test), 1))
    print(f"\nTest log loss  no information        {log_loss(test['band'], base, labels=classes):.3f}")
    simple = LogisticRegression(max_iter=1000).fit(train[["expected_pressure"]], train["band"])
    p_simple = simple.predict_proba(test[["expected_pressure"]])
    print(f"Test log loss  expected pressure only {log_loss(test['band'], p_simple, labels=classes):.3f}  "
          f"accuracy {accuracy_score(test['band'], simple.predict(test[['expected_pressure']])):.2f}")
    model = LogisticRegression(max_iter=2000).fit(train[ACTIVITY_FEATURES], train["band"])
    p_full = model.predict_proba(test[ACTIVITY_FEATURES])
    print(f"Test log loss  all features (saved)   {log_loss(test['band'], p_full, labels=classes):.3f}  "
          f"accuracy {accuracy_score(test['band'], model.predict(test[ACTIVITY_FEATURES])):.2f}")

    test = test.copy()
    test["p_in_band"] = p_full[:, list(model.classes_).index("in_band")]
    test["bucket"] = pd.cut(test["p_in_band"], [0, 0.2, 0.3, 0.4, 0.5, 1.0])
    calibration = test.groupby("bucket", observed=True).agg(predicted=("p_in_band", "mean"),
                                                            real=("band", lambda b: (b == "in_band").mean()),
                                                            activities=("band", "size"))
    with pd.option_context("display.float_format", "{:.2f}".format):
        print("\nCalibration on the test nights (predicted vs real share in band):")
        print(calibration)
        print("\nWeights (in_band vs the rest), largest first:")
        weights = pd.Series(model.coef_[list(model.classes_).index("in_band")], index=ACTIVITY_FEATURES)
        print(weights.reindex(weights.abs().sort_values(ascending=False).index))
    save_activity_model(model)
    print("\nSaved to data/activity_band_model.joblib")


if __name__ == "__main__":
    main()
