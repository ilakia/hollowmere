"""
The story is a pool of attractions ("beats", one beat = one room) stored in story_beats.json.
An attraction can only be chosen if it belongs to the current zone, was not visited yet,
and every attraction in its "requires" list was already visited. This keeps the plot
consistent: a director can only pick from valid_next().
"""
import json
from collections import Counter
from pathlib import Path

from . import config as C

DEFAULT_PATH = Path(__file__).with_name("story_beats.json")


class Story:
    def __init__(self, path=DEFAULT_PATH):
        with open(path, encoding="utf-8") as f:
            self.beats = json.load(f)
        self.by_id = {b["id"]: b for b in self.beats}
        self._check()

    def _check(self):
        """Catch mistakes in the JSON early instead of in the middle of an experiment."""
        for b in self.beats:
            for r in b["requires"]:
                assert r in self.by_id, f"{b['id']} requires unknown attraction {r}"
                assert self.by_id[r]["zone"] < b["zone"], f"{b['id']} requires a later attraction {r}"
            for kind in b["enemies"]:
                assert kind in C.ENEMY_TYPES, f"{b['id']} has unknown ghost {kind}"
        # Each zone needs enough attractions without requirements to fill all its rooms,
        # so a director can never get stuck with no valid next room.
        rooms_needed = Counter(C.ZONE_OF_ROOM)
        for zone, needed in rooms_needed.items():
            free = sum(1 for b in self.beats if b["zone"] == zone and not b["requires"])
            assert free >= needed, f"zone {zone} has only {free} free attractions, needs {needed}"

    def get(self, beat_id):
        return self.by_id[beat_id]

    def valid_next(self, used_ids, zone):
        return [b for b in self.beats
                if b["zone"] == zone
                and b["id"] not in used_ids
                and all(r in used_ids for r in b["requires"])]
