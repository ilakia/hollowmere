"""
Controllers = the "director". Before every room a controller decides:
  beat_id     which story beat (room) comes next, from state["valid_beats"]
  difficulty  "easy" | "normal" | "hard"
  help_mode   "stay_back" | "hint" | "heal" | "fight"

Every controller has the same two methods, so they can be swapped freely:
  decide(state)                 -> decision dict
  observe(state, decision, row) -> learn from what happened (only the bandit will use it)

Built so far: Fixed (baseline) and Random (for collecting unbiased training data).
To come: RuleController, BanditController, LLMController.
"""
from . import config as C


class Controller:
    name = "base"

    def __init__(self, rng=None):
        self.rng = rng

    def decide(self, state):
        raise NotImplementedError

    def observe(self, state, decision, row):
        pass


class FixedController(Controller):
    """Same choice for everyone: normal difficulty, companion gives hints,
    always the first valid beat. This is the baseline every other controller must beat."""
    name = "fixed"

    def decide(self, state):
        return {"beat_id": state["valid_beats"][0]["id"],
                "difficulty": "normal", "help_mode": "hint"}


class RandomController(Controller):
    """Picks everything uniformly at random. Not a serious director: it is used to
    collect training data for the failure predictor that does not depend on any
    controller's habits. The propensity (probability of the choice) is logged, which
    allows correcting for the logging policy later if needed."""
    name = "random"

    def decide(self, state):
        beats = state["valid_beats"]
        diffs = list(C.DIFFICULTY)
        helps = C.HELP_MODES
        return {"beat_id": self.rng.choice(beats)["id"],
                "difficulty": self.rng.choice(diffs),
                "help_mode": self.rng.choice(helps),
                "propensity": round(1 / (len(beats) * len(diffs) * len(helps)), 6)}


CONTROLLERS = {c.name: c for c in [FixedController, RandomController]}
