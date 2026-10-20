"""
Controllers = the "director". Before every room a controller decides:
  beat_id     which story beat (room) comes next, from state["valid_beats"]
  difficulty  "easy" | "normal" | "hard"
  help_mode   "stay_back" | "hint" | "heal" | "fight"

Every controller has the same two methods, so they can be swapped freely:
  decide(state)                 -> decision dict
  observe(state, decision, row) -> learn from what happened (only the bandit will use it)

Built so far: Fixed (baseline), Random (for collecting unbiased training data), Rule, Bandit.
To come: LLMController.
"""
from pathlib import Path

from . import config as C
from .bandit import ARMS, CONTEXT_NAMES, FINALE_ARMS, LinUCB, make_context
from .skill import SkillEstimator, load_expected_table


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


THREAT_ORDER = ["low", "medium", "high", "boss"]


def pick_beat(valid_beats, wanted_threat):
    """Pick the valid attraction whose threat level is closest to the wanted one.
    Inputs:  valid_beats = list of attraction dicts, wanted_threat = "low" | "medium" | "high"
    Output:  one attraction dict (ties: the first one in story order)"""
    wanted = THREAT_ORDER.index(wanted_threat)
    best = valid_beats[0]
    best_distance = 99
    for beat in valid_beats:
        distance = abs(THREAT_ORDER.index(beat["threat"]) - wanted)
        if distance < best_distance:
            best, best_distance = beat, distance
    return best


class RuleController(Controller):
    """Hand-written if-else rules on top of the skill estimate (game/skill.py).
    Struggling player -> easier room, easy difficulty, Walt helps.
    Cruising player   -> harder room, normal difficulty, Walt stays back.
    The thresholds live in config.py."""
    name = "rule"

    def __init__(self, rng=None):
        super().__init__(rng)
        self.skill = SkillEstimator(load_expected_table())
        self.died_last_room = False

    def decide(self, state):
        hp_share = state["hp"] / state["max_hp"]
        estimate = self.skill.estimate

        if self.died_last_room or hp_share < C.RULE_LOW_HP:   # in danger right now: play it safe
            difficulty, help_mode, threat = "easy", "heal", "low"
        elif estimate > C.RULE_STRUGGLING:                       # losing more HP than average
            difficulty, help_mode, threat = "easy", "hint", "low"
        elif estimate < -C.RULE_CRUISING:                        # losing less HP than average
            # normal instead of hard: "hard" on top of a high-threat room without help
            # overshot, experts escaped only 79% of runs in tuning
            difficulty, help_mode, threat = "normal", "stay_back", "high"
        else:                                                    # about average
            difficulty, help_mode, threat = "normal", "hint", "medium"

        beat = pick_beat(state["valid_beats"], threat)
        return {"beat_id": beat["id"], "difficulty": difficulty, "help_mode": help_mode}

    def observe(self, state, decision, row):
        self.skill.update(row)
        self.died_last_room = row["deaths"] > 0


THREAT_FOR_DIFFICULTY = {"easy": "low", "normal": "medium", "hard": "high"}
BANDIT_MODEL_PATH = Path("data/bandit_model.npz")


class BanditController(Controller):
    """LinUCB contextual bandit (game/bandit.py). It is not told any rules: it learns which
    (difficulty, Walt mode) works in which situation from the reward, across many players.
    The room is then picked by threat to match the difficulty (easy -> low, hard -> high).

    The two models are shared by ALL runs (class attributes), so experience carries over
    from player to player. learning = True while training (explore + update after each room);
    False when testing (always the best-known arm, no updates)."""
    name = "bandit"
    model = None
    finale_model = None
    learning = False

    @classmethod
    def reset(cls, alpha):
        n = len(CONTEXT_NAMES)
        cls.model = LinUCB(ARMS, n, alpha)
        cls.finale_model = LinUCB(FINALE_ARMS, n, alpha)

    @classmethod
    def save(cls, path=BANDIT_MODEL_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        cls.model.save(path)
        cls.finale_model.save(Path(path).with_name("bandit_finale_model.npz"))

    @classmethod
    def load(cls, path=BANDIT_MODEL_PATH):
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} is missing. Run: python bandit_experiment.py")
        cls.reset(alpha=0.0)
        cls.model.load(path)
        cls.finale_model.load(Path(path).with_name("bandit_finale_model.npz"))

    def __init__(self, rng=None):
        super().__init__(rng)
        if BanditController.model is None:
            BanditController.load()
        self.skill = SkillEstimator(load_expected_table())
        self.died_last_room = False
        self.last_choice = None

    def decide(self, state):
        x = make_context(state, self.skill.estimate, self.died_last_room)
        model = BanditController.finale_model if state["is_finale"] else BanditController.model
        i = model.choose(x, self.rng, explore=BanditController.learning)
        difficulty, help_mode = model.arms[i]
        beat = pick_beat(state["valid_beats"], THREAT_FOR_DIFFICULTY[difficulty])
        self.last_choice = (model, i, x)
        return {"beat_id": beat["id"], "difficulty": difficulty, "help_mode": help_mode}

    def observe(self, state, decision, row):
        if BanditController.learning:
            model, i, x = self.last_choice
            reward = 1.0 if row["band"] == "in_band" else 0.0
            model.update(i, x, reward)
        self.skill.update(row)
        self.died_last_room = row["deaths"] > 0


CONTROLLERS = {c.name: c for c in [FixedController, RandomController, RuleController, BanditController]}
