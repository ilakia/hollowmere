"""
Controllers = the "director". Before every room a controller decides:
  beat_id     which story beat (room) comes next, from state["valid_beats"]
  difficulty  "easy" | "normal" | "hard"
  help_mode   "stay_back" | "hint" | "heal" | "fight"

Every controller has the same two methods, so they can be swapped freely:
  decide(state)                 -> decision dict
  observe(state, decision, row) -> learn from what happened (only the bandit will use it)

Built: Fixed (baseline), Random (for collecting unbiased training data), Rule, Bandit, LLM.
"""
from pathlib import Path

import pandas as pd

from . import config as C
from .bandit import ARMS, CONTEXT_NAMES, FINALE_ARMS, LinUCB, make_context
from .llm import (RISK_FINALE_LINE, RISK_SYSTEM_PROMPT, SHORTLIST_SIZE, LLMClient, build_prompt,
                  describe_options)
from .risk import FEATURES, load_band_model, option_features
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


class LLMController(Controller):
    """A local language model (Ollama, game/llm.py) reads a plain-text description of the
    situation and answers with a JSON decision and a one-sentence reason. It gets the same
    information as the other directors (HP, potions, skill estimate, last result, allowed rooms)
    and a short description of the game, but no hand-written rules and no training.
    list_valid_beats = False is the ablation: the model is not told which rooms are allowed."""
    name = "llm"
    client = None             # one LLMClient (with its cache) shared by all runs
    list_valid_beats = True

    def __init__(self, rng=None):
        super().__init__(rng)
        if LLMController.client is None:
            LLMController.client = LLMClient()
        self.skill = SkillEstimator(load_expected_table())
        self.last_band = None

    def decide(self, state):
        prompt = build_prompt(state, self.skill.estimate, self.last_band, LLMController.list_valid_beats)
        answer = LLMController.client.ask(prompt)
        decision = {"beat_id": answer.get("beat_id"), "difficulty": answer.get("difficulty"),
                    "help_mode": answer.get("help_mode")}
        return decision     # engine.validate_decision repairs and flags anything invalid

    def observe(self, state, decision, row):
        self.skill.update(row)
        self.last_band = row["band"]


class LLMRiskController(LLMController):
    """The LLM director with numbers: before asking, every allowed (attraction, difficulty, Walt mode)
    is scored by the band model (game/risk.py, trained on random-director data) for THIS player,
    and the SHORTLIST_SIZE options with the highest in-band chance are listed in the prompt.
    The model still makes the final choice and gives a reason."""
    name = "llm_risk"

    def __init__(self, rng=None):
        super().__init__(rng)
        self.band_model = load_band_model()
        self.table = load_expected_table()
        self.last_hp_lost = 0.0
        self.died_last_room = False

    def score_options(self, state):
        """Output: all allowed options with predicted in_band / too_easy / too_hard shares, best first."""
        if state["is_finale"]:
            help_modes = [C.FINALE_HELP_MODE]
        else:
            help_modes = C.HELP_MODES
        options, rows = [], []
        for beat in state["valid_beats"]:
            for difficulty in C.DIFFICULTY:
                for help_mode in help_modes:
                    expected = self.table.get((beat["id"], difficulty, help_mode), self.skill.fallback)
                    rows.append(option_features(
                        state["room_index"], state["hp"], state["potions"], state["deaths_total"],
                        self.skill.estimate, self.last_hp_lost, self.died_last_room,
                        beat["threat"], difficulty, help_mode, expected))
                    options.append({"beat_id": beat["id"], "difficulty": difficulty, "help_mode": help_mode})
        probabilities = self.band_model.predict_proba(pd.DataFrame(rows, columns=FEATURES))
        classes = list(self.band_model.classes_)
        for option, p in zip(options, probabilities):
            for band in ["in_band", "too_easy", "too_hard"]:
                option[band] = p[classes.index(band)]
        options.sort(key=lambda o: o["in_band"], reverse=True)
        return options

    def decide(self, state):
        shortlist = self.score_options(state)[:SHORTLIST_SIZE]
        prompt = build_prompt(state, self.skill.estimate, self.last_band, finale_line=RISK_FINALE_LINE)
        prompt = prompt + "\n" + describe_options(shortlist)
        answer = LLMController.client.ask(prompt, RISK_SYSTEM_PROMPT, tag="|risk")
        return {"beat_id": answer.get("beat_id"), "difficulty": answer.get("difficulty"),
                "help_mode": answer.get("help_mode")}

    def observe(self, state, decision, row):
        super().observe(state, decision, row)
        self.last_hp_lost = row["hp_lost_ratio"]
        self.died_last_room = row["deaths"] > 0


CONTROLLERS = {c.name: c for c in [FixedController, RandomController, RuleController,
                                   BanditController, LLMController, LLMRiskController]}
