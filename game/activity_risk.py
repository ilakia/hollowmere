"""
The activity band model: before an activity, how likely is it to end too easy / in band / too hard for
THIS player with a given difficulty and help? The same idea as Study 1's band model for the fights
(game/risk.py), trained the same way (logistic regression on random-choice data, activity_predictor.py).

Features are only what Walt can see BEFORE the activity (never the bot's hidden skill):
  the player's situation: skill estimate, HP share, how much the last room cost
  the option: expected pressure of an average player (game/expected_activity.csv), difficulty level,
              and what the help does (success bonus, forgiven slips, Walt's own successes, longer goal)
"""
from pathlib import Path

import joblib

from . import config as C
from .activities import ACTIVITIES

ACTIVITY_FEATURES = ["skill_estimate", "hp_share", "last_hp_lost", "expected_pressure", "difficulty_level",
                     "help_p", "help_forgive", "help_assist", "help_goal", "help_delayed"]
DIFFICULTY_LEVEL = {"easy": 0, "normal": 1, "hard": 2}
ACTIVITY_MODEL_PATH = Path("data/activity_band_model.joblib")
_model = None


def activity_features(activity_id, difficulty, help_mode, skill_estimate, hp, last_hp_lost, expected_table,
                      fallback):
    """One feature row for one situation and one possible choice. Output: dict with ACTIVITY_FEATURES."""
    help_spec = ACTIVITIES[activity_id]["help"][help_mode]
    return {
        "skill_estimate": skill_estimate,
        "hp_share": hp / C.PLAYER_MAX_HP,
        "last_hp_lost": last_hp_lost,
        "expected_pressure": expected_table.get((activity_id, difficulty, help_mode), fallback),
        "difficulty_level": DIFFICULTY_LEVEL[difficulty],
        "help_p": help_spec.get("p", 0.0),
        "help_forgive": help_spec.get("forgive", 0),
        "help_assist": help_spec.get("assist", 0.0),
        "help_goal": help_spec.get("goal", 0),
        "help_delayed": int(bool(help_spec.get("later") or help_spec.get("after_mistake"))),
    }


def save_activity_model(model, path=ACTIVITY_MODEL_PATH):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_activity_model(path=ACTIVITY_MODEL_PATH):
    """Output: the trained activity band model (read once). Made by activity_predictor.py."""
    global _model
    if _model is None:
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} is missing. Run: python activity_predictor.py")
        _model = joblib.load(path)
    return _model
