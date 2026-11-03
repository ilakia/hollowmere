"""
Shared pieces for outcome models: the feature list, how one (situation, option) becomes a
feature row, and the saved band model that predicts too_easy / in_band / too_hard.

Used by failure_predictor.py (training and testing) and by the LLM director's risk-informed
prompt (controllers.py), so both describe a room in exactly the same way.
"""
from pathlib import Path

import joblib

from . import config as C

FEATURES = ["room_index", "hp_share", "potions_left", "deaths_so_far", "skill_estimate",
            "last_hp_lost", "died_last_room", "threat", "difficulty_level",
            "help_stay_back", "help_hint", "help_heal", "help_fight", "expected_hp_lost"]
THREAT_ORDER = ["low", "medium", "high", "boss"]
DIFFICULTY_ORDER = ["easy", "normal", "hard"]
BAND_MODEL_PATH = Path("data/band_model.joblib")
_band_model = None


def option_features(room_index, hp, potions_left, deaths_so_far, skill_estimate, last_hp_lost,
                    died_last_room, threat, difficulty, help_mode, expected_hp_lost):
    """One feature row for one situation and one possible director choice.
    Inputs: the situation before the room (as the director sees it) and the option
            (threat of the attraction, difficulty, help_mode, its expected HP loss)
    Output: dict with the keys in FEATURES"""
    return {
        "room_index": room_index,
        "hp_share": hp / C.PLAYER_MAX_HP,
        "potions_left": potions_left,
        "deaths_so_far": deaths_so_far,
        "skill_estimate": skill_estimate,
        "last_hp_lost": last_hp_lost,
        "died_last_room": int(died_last_room),
        "threat": THREAT_ORDER.index(threat),
        "difficulty_level": DIFFICULTY_ORDER.index(difficulty),
        "help_stay_back": int(help_mode == "stay_back"),
        "help_hint": int(help_mode == "hint"),
        "help_heal": int(help_mode == "heal"),
        "help_fight": int(help_mode == "fight"),
        "expected_hp_lost": expected_hp_lost,
    }


def save_band_model(model, path=BAND_MODEL_PATH):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_band_model(path=BAND_MODEL_PATH):
    """Output: the trained band model (read from disk once). Made by failure_predictor.py."""
    global _band_model
    if _band_model is None:
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} is missing. Run: python failure_predictor.py")
        _band_model = joblib.load(path)
    return _band_model
