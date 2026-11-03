"""
Helpers for the LLM director (LLMController in controllers.py): the prompt, the call to the
local Ollama server, and a cache.

- The model runs offline on the laptop through Ollama (http://localhost:11434).
- It must answer in JSON: {"beat_id": ..., "difficulty": ..., "help_mode": ..., "reason": ...}.
  Anything invalid is replaced by safe defaults in engine.validate_decision and logged as
  decision_valid = False.
- temperature 0 and a fixed seed make answers repeatable; the cache (data/llm_cache.json)
  stores every answer by prompt, so re-running an experiment gives identical results and is fast.
- The situation is rounded (HP to 10, skill estimate to 0.05) so similar situations share
  one prompt, which keeps the number of slow model calls down.
"""
import json
import time
import urllib.request
from pathlib import Path

from . import config as C

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"
CACHE_PATH = Path("data/llm_cache.json")
TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = """You are the director of a turn-based horror theme-park game.
Before each room you choose the next attraction, its difficulty and how Walt (the player's companion) helps.
GOAL: the player should clear the room without dying and lose between 30% and 70% of their HP.
Losing less than 30% is boring (too easy). Dying or losing more than 70% is frustrating (too hard).

Difficulty: easy = ghosts x0.75 HP and damage, normal = x1, hard = x1.3 HP and x1.25 damage.
Walt's help modes:
- stay_back: no help
- hint: +15% aim for 3 turns and warns before big hits
- heal: heals the player +25 HP once when they drop below 50% HP
- fight: Walt also attacks every turn (6 damage, hits 70% of the time)
Attraction threat levels: low < medium < high. Ghosts: wisp (weak), animatronic (medium), wraith (big charged hits).
The skill estimate compares the player's HP loss with an average player in the same situation:
positive = struggling (loses more than average), negative = cruising (loses less than average).

Answer ONLY with JSON: {"beat_id": "...", "difficulty": "easy|normal|hard", "help_mode": "stay_back|hint|heal|fight", "reason": "one short sentence"}
beat_id must be one of the listed attractions."""


RISK_SYSTEM_PROMPT = SYSTEM_PROMPT + """

You also get a short list of options. Each option was scored by a prediction model trained on thousands
of earlier players: the chance that the room ends in band, too easy or too hard for THIS player right now.
Use these numbers: prefer options with a high in-band chance and a low too-hard chance.
Your beat_id, difficulty and help_mode must come from ONE of the listed options."""
SHORTLIST_SIZE = 6


def describe_options(options):
    """Turn scored options into prompt lines.
    Input:  list of dicts with beat_id, difficulty, help_mode, in_band, too_easy, too_hard (shares)
    Output: text, one line per option (percentages rounded to 5 so similar situations share a prompt)"""
    lines = ["Options (predicted for this player):"]
    for number, o in enumerate(options, start=1):
        lines.append(f"{number}. beat_id={o['beat_id']}, difficulty={o['difficulty']}, help_mode={o['help_mode']}: "
                     f"in band {round_to(o['in_band'] * 100, 5):.0f}%, too easy {round_to(o['too_easy'] * 100, 5):.0f}%, "
                     f"too hard {round_to(o['too_hard'] * 100, 5):.0f}%")
    return "\n".join(lines)


def round_to(value, step):
    return round(round(value / step) * step, 2)


FINALE_LINE = "This is the FINALE against Walt himself: only the difficulty matters, use help_mode \"stay_back\"."
# risk version (developed on training seeds 1500-1524): the first version let the model pick "hard"
# for the "finale atmosphere" even when the options said 90% too hard, and it contradicted the
# options' help_mode "none"
RISK_FINALE_LINE = ("This is the FINALE against Walt himself. The predictions already include how strong Walt is. "
                    "The best ending is a close fight the player can win, so choose by the numbers, not by drama. "
                    "Use help_mode \"none\".")


def build_prompt(state, skill_estimate, last_band, list_valid_beats=True, finale_line=FINALE_LINE):
    """Describe the situation in plain text.
    Inputs:  state (from the engine), skill_estimate, last_band ("in_band", "too_easy", "too_hard" or None),
             list_valid_beats = False for the ablation where the model gets no list of allowed attractions,
             finale_line = the sentence used in the finale
    Output:  the user message (string)"""
    hp = round_to(state["hp"], 10)
    lines = [
        f"Room {state['room_index'] + 1} of {C.ROOMS_PER_RUN} (zone {state['zone']}).",
        f"Player HP before the room: {hp:.0f} of {state['max_hp']}. Potions left: {state['potions']}.",
        f"Skill estimate: {round_to(skill_estimate, 0.05):+.2f}.",
        f"Last room result: {last_band if last_band else 'none yet (first room)'}.",
    ]
    if state["is_finale"]:
        lines.append(finale_line)
    if list_valid_beats:
        lines.append("Allowed attractions:")
        for beat in state["valid_beats"]:
            ghosts = ", ".join(beat["enemies"])
            lines.append(f"- {beat['id']}: threat {beat['threat']}, ghosts: {ghosts}")
    else:
        lines.append(f"Choose an attraction for zone {state['zone']}.")
    return "\n".join(lines)


class LLMClient:
    """Calls Ollama, with a cache shared by all runs. Counts calls, cache hits, failures and time."""

    def __init__(self, model=MODEL, cache_path=CACHE_PATH):
        self.model = model
        self.cache_path = Path(cache_path)
        self.cache = {}
        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        self.calls = 0
        self.cache_hits = 0
        self.failures = 0
        self.seconds = 0.0

    def ask(self, user_message, system_prompt=SYSTEM_PROMPT, tag=""):
        """Inputs: the situation text, the system prompt, and a tag that keeps the cache entries
        of different prompt versions apart ("" = the original prompt).
        Output: the model's answer parsed as a dict, or {} if it failed or was not valid JSON."""
        key = self.model + tag + "\n" + user_message
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        body = {"model": self.model, "stream": False, "format": "json",
                "options": {"temperature": 0, "seed": 42},
                "messages": [{"role": "system", "content": system_prompt},
                             {"role": "user", "content": user_message}]}
        request = urllib.request.Request(OLLAMA_URL, data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        start = time.time()
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                reply = json.loads(response.read().decode("utf-8"))
            answer = json.loads(reply["message"]["content"])
            if not isinstance(answer, dict):
                answer = {}
        except Exception:      # server down, timeout, or text that is not JSON
            answer = {}
            self.failures += 1
        self.seconds += time.time() - start
        self.calls += 1
        self.cache[key] = answer
        return answer

    def save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=0), encoding="utf-8")
