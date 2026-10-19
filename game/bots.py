"""
Simulated players. Each profile is a RANGE of settings, not one fixed setting:
every bot samples its own values, so we get thousands of slightly different
players instead of 4 identical clones. This reduces simulator bias.

Settings:
  accuracy      chance to hit when attacking
  dodge         chance to avoid an enemy hit that would have landed
  defend_skill  chance to defend when an enemy is visibly winding up
  potion_at     drinks a potion when HP falls below this share of max HP
  quit_after    quits after this many deaths in a row (None = never quits)

The bots model players. They are NOT real players, and the write-up must say so.
"""
from .config import HINT_DEFEND_BOOST

PROFILES = {
    "beginner": {"accuracy": (0.45, 0.60), "dodge": (0.00, 0.08),
                 "defend_skill": (0.05, 0.25), "potion_at": (0.15, 0.25), "quit_after": None},
    "average":  {"accuracy": (0.60, 0.75), "dodge": (0.08, 0.15),
                 "defend_skill": (0.40, 0.60), "potion_at": (0.25, 0.35), "quit_after": None},
    "expert":   {"accuracy": (0.80, 0.92), "dodge": (0.15, 0.25),
                 "defend_skill": (0.80, 0.95), "potion_at": (0.35, 0.45), "quit_after": None},
    # an average-ish player with low patience
    "rage_quitter": {"accuracy": (0.50, 0.70), "dodge": (0.05, 0.12),
                     "defend_skill": (0.20, 0.50), "potion_at": (0.20, 0.30), "quit_after": 2},
}


class Bot:
    def __init__(self, profile, rng):
        p = PROFILES[profile]
        self.profile = profile
        self.accuracy = rng.uniform(*p["accuracy"])
        self.dodge = rng.uniform(*p["dodge"])
        self.defend_skill = rng.uniform(*p["defend_skill"])
        self.potion_at = rng.uniform(*p["potion_at"])
        self.quit_after = p["quit_after"]

    def params(self):
        """Hidden true skill. Logged for analysis only, NEVER use as a model feature."""
        return {"true_accuracy": round(self.accuracy, 4), "true_dodge": round(self.dodge, 4),
                "true_defend_skill": round(self.defend_skill, 4),
                "true_potion_at": round(self.potion_at, 4)}

    def choose_action(self, view, rng):
        if view["potions"] > 0 and view["hp"] / view["max_hp"] < self.potion_at:
            return "potion"
        if view["wind_up"]:
            p = self.defend_skill
            if view["warning"]:  # the companion's hint helps weak players notice the wind-up
                p = p + (1 - p) * HINT_DEFEND_BOOST
            if rng.random() < p:
                return "defend"
        return "attack"

    def end_of_room(self, room_index):
        """Called after every room. The learning curve is added in step 2."""
        pass

    def wants_to_quit(self, consecutive_deaths):
        return self.quit_after is not None and consecutive_deaths >= self.quit_after
