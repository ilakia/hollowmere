"""
Study 2 playtest mode: which night and which Walt a player gets.

- The nights are chapters of one story, so every player plays them in the same order: A, then B, then C.
- The three Walt versions are rotated over the three nights. All 6 possible orders are used in turn, so
  every version is played equally often as the 1st, 2nd and 3rd night (and comes after each other
  version equally often). With 6, 12 or 18 players the design is fully balanced.
- The order comes from the number in the player ID (P01 -> order 1, P02 -> order 2, ... P07 -> order 1).
  IDs without a number get a fixed order from a fingerprint of the ID, so the same ID always gets the
  same order.
- Which night is next is read from data/story_runs.csv: the number of story nights this ID has already
  saved (a lost night counts too: every player plays each night once).
- The player never sees which Walt version is playing.
"""
import hashlib
import re
from pathlib import Path

import pandas as pd

NIGHT_ORDER = ["A", "B", "C"]
COMPANION_ORDERS = [
    ["silent", "scripted", "llm"],
    ["scripted", "llm", "silent"],
    ["llm", "silent", "scripted"],
    ["silent", "llm", "scripted"],
    ["scripted", "silent", "llm"],
    ["llm", "scripted", "silent"],
]
STORY_RUNS = Path("data/story_runs.csv")


def order_index(player_id):
    """Output: which of the 6 companion orders this player gets (0-5)."""
    digits = re.findall(r"\d+", player_id or "")
    if digits:
        return (int(digits[-1]) - 1) % len(COMPANION_ORDERS)
    fingerprint = int(hashlib.md5((player_id or "").encode("utf-8")).hexdigest(), 16)
    return fingerprint % len(COMPANION_ORDERS)


def nights_played(player_id, path=STORY_RUNS):
    """Output: how many story nights this player ID has saved so far."""
    path = Path(path)
    if not player_id or not path.exists():
        return 0
    table = pd.read_csv(path, usecols=lambda c: c in ("player_id", "run_id"))
    if "player_id" not in table.columns:
        return 0
    mine = table[table["player_id"].astype(str) == player_id]
    return mine["run_id"].nunique()


def next_assignment(player_id, path=STORY_RUNS):
    """Output: (night, companion) for this player's next night, or (None, None) when all three are done."""
    played = nights_played(player_id, path)
    if played >= len(NIGHT_ORDER):
        return None, None
    companion = COMPANION_ORDERS[order_index(player_id)][played]
    return NIGHT_ORDER[played], companion
