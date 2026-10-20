"""
LinUCB contextual bandit (Li et al., 2010), used by BanditController in controllers.py.

Each "arm" is one director choice: a (difficulty, Walt mode) pair.
For every arm the bandit keeps a small straight-line model:
    expected reward = theta . context
and picks the arm with the highest  expected reward + exploration bonus.
The bonus is large for arms it has little experience with in this kind of situation,
so they still get tried; it shrinks as evidence grows ("optimism under uncertainty").

Reward (decided before building, see README): 1 if the room ends in band, else 0,
exactly the measure every director is graded on.
"""
import numpy as np

from . import config as C

DIFFICULTY_ORDER = ["easy", "normal", "hard"]
# 12 arms for normal rooms; in the finale Walt is the enemy, so only difficulty can be chosen (3 arms)
ARMS = [(difficulty, help_mode) for difficulty in DIFFICULTY_ORDER for help_mode in C.HELP_MODES]
FINALE_ARMS = [(difficulty, C.FINALE_HELP_MODE) for difficulty in DIFFICULTY_ORDER]
CONTEXT_NAMES = ["bias", "skill_estimate", "hp_share", "potions_share", "progress", "died_last_room"]


def make_context(state, skill_estimate, died_last_room):
    """The situation the bandit sees before a room, as numbers of similar size (about 0 to 1).
    Inputs:  state = the game state given to every director, skill_estimate, died_last_room (bool)
    Output:  numpy vector in the order of CONTEXT_NAMES"""
    return np.array([
        1.0,                                                   # bias: lets each arm have a base value
        skill_estimate,
        state["hp"] / state["max_hp"],
        state["potions"] / C.POTIONS_PER_RUN,
        state["room_index"] / (C.ROOMS_PER_RUN - 1),
        1.0 if died_last_room else 0.0,
    ])


class LinUCB:
    def __init__(self, arms, n_features, alpha):
        """Inputs: arms = list of (difficulty, help_mode), n_features = context length,
        alpha = exploration strength (0 = never explore, just use the best estimate)."""
        self.arms = arms
        self.alpha = alpha
        self.A_inv = [np.eye(n_features) for _ in arms]   # inverse of (identity + sum of x x^T)
        self.b = [np.zeros(n_features) for _ in arms]     # sum of reward * x
        self.theta = [np.zeros(n_features) for _ in arms]  # learned weights = A_inv @ b
        self.pulls = [0 for _ in arms]

    def choose(self, x, rng, explore=True):
        """Pick an arm for context x. Output: arm index. Ties are broken at random with rng."""
        scores = []
        for i in range(len(self.arms)):
            score = self.theta[i] @ x
            if explore:
                score += self.alpha * np.sqrt(x @ self.A_inv[i] @ x)
            scores.append(score)
        best = max(scores)
        candidates = [i for i, s in enumerate(scores) if s >= best - 1e-12]
        return rng.choice(candidates)

    def update(self, i, x, reward):
        """Learn from one room: arm i was played in context x and earned reward (0 or 1)."""
        # Sherman-Morrison formula: updates the inverse directly instead of re-inverting a matrix
        A_inv_x = self.A_inv[i] @ x
        self.A_inv[i] = self.A_inv[i] - np.outer(A_inv_x, A_inv_x) / (1.0 + x @ A_inv_x)
        self.b[i] = self.b[i] + reward * x
        self.theta[i] = self.A_inv[i] @ self.b[i]
        self.pulls[i] += 1

    def save(self, path):
        np.savez(path, A_inv=np.array(self.A_inv), b=np.array(self.b),
                 pulls=np.array(self.pulls), alpha=self.alpha)

    def load(self, path):
        data = np.load(path)
        self.A_inv = list(data["A_inv"])
        self.b = list(data["b"])
        self.pulls = list(data["pulls"])
        self.alpha = float(data["alpha"])
        self.theta = [self.A_inv[i] @ self.b[i] for i in range(len(self.arms))]
