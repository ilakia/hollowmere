"""
Skill estimator: a running guess of how well the player is doing, using only what a
director can see after each room (never the hidden true_* skill columns).

After each room:
  residual = HP lost in this room - HP lost by an average player in the same room,
             difficulty and Walt mode (the "expected" table, built from random-director data)
  estimate = SKILL_EMA_ALPHA * residual + (1 - SKILL_EMA_ALPHA) * old estimate

  estimate > 0: the player loses more HP than average (struggling)
  estimate < 0: the player loses less HP than average (cruising)

Comparing with the same room, difficulty and Walt mode makes the estimate fair: losing 40%
in a hard room is good, losing 40% in an easy room is not.
"""
import csv
from pathlib import Path

from . import config as C

TABLE_PATH = Path(__file__).with_name("expected_hp_lost.csv")
_table_cache = None


def load_expected_table(path=TABLE_PATH):
    """Read the expected-HP-loss table made by build_tables.py.
    Input:  path to the CSV file
    Output: dict {(beat_id, difficulty, help_mode): average hp_lost_ratio}"""
    global _table_cache
    if _table_cache is None:
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} is missing. Run: python build_tables.py")
        table = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["beat_id"], row["difficulty"], row["help_mode"])
                table[key] = float(row["expected_hp_lost"])
        _table_cache = table  # read the file once, not once per run
    return _table_cache


class SkillEstimator:
    """One estimator per run. Starts at 0 (= average player) because room 1 has no history."""

    def __init__(self, table):
        self.table = table
        self.fallback = sum(table.values()) / len(table)  # used if a combination was never seen
        self.estimate = 0.0

    def update(self, row):
        """Add one finished room to the estimate.
        Input:  row = the room's telemetry (needs beat_id, difficulty, help_mode, hp_lost_ratio)
        Output: the new estimate"""
        key = (row["beat_id"], row["difficulty"], row["help_mode"])
        expected = self.table.get(key, self.fallback)
        residual = row["hp_lost_ratio"] - expected
        residual = max(-C.SKILL_RESIDUAL_CAP, min(C.SKILL_RESIDUAL_CAP, residual))
        self.estimate = C.SKILL_EMA_ALPHA * residual + (1 - C.SKILL_EMA_ALPHA) * self.estimate
        return self.estimate
