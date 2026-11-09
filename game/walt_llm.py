"""
LLM Walt (Study 2): the prompt for the companion version of the llm_risk director from Study 1.

Before every room of a story night, LLM Walt quietly chooses the difficulty of the room and how he
helps. Exactly as llm_risk in Study 1, every allowed option is first scored by the band model
(game/risk.py) for THIS player, and the model picks one of the best options. New in Study 2: he also
says one short sentence to the player, in character, which is spoken aloud in the game.

The model answers with the NUMBER of an option (easier to check than free text) plus the sentence.
Anything invalid falls back to scripted Walt's choice and is logged as decision_source = "fallback".
"""
import json
import threading
import time
import urllib.request
from pathlib import Path

from . import config as C
from .llm import MODEL, OLLAMA_URL, TIMEOUT_SECONDS, LLMClient, round_to

WALT_CACHE = Path("data/walt_cache.json")
ANSWER_TOKENS = {"|walt": 50, "|walt_hint": 45, "|walt_help": 45, "|walt_story": 75, "|warmup": 5}


class WaltClient(LLMClient):
    """The Study 1 client (same model, temperature 0, seed 42, cache) with two changes for live play:
    a cap on the answer length (num_predict, the answer is short JSON anyway: on the test laptop the model
    writes about 8 tokens per second, so every token counts) and keep_alive, so the model stays loaded
    for the whole playtest. Own cache file, so Study 1's cache is never touched."""

    def __init__(self, model=MODEL, cache_path=WALT_CACHE):
        super().__init__(model, cache_path)
        self.lock = threading.Lock()       # questions can come from several background threads at once

    def ask(self, user_message, system_prompt, tag=""):
        key = self.model + tag + "\n" + user_message
        with self.lock:
            if key in self.cache:
                self.cache_hits += 1
                return self.cache[key]
        body = {"model": self.model, "stream": False, "format": "json", "keep_alive": "60m",
                "options": {"temperature": 0, "seed": 42, "num_predict": ANSWER_TOKENS.get(tag, 60)},
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
        except Exception:      # server down, timeout, cut-off or broken JSON: the caller falls back
            answer = {}
            self.failures += 1
        with self.lock:
            self.seconds += time.time() - start
            self.calls += 1
            if tag != "|warmup":
                self.cache[key] = answer
        return answer

    def save_cache(self):
        with self.lock:
            snapshot = dict(self.cache)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(snapshot, indent=0), encoding="utf-8")

WALT_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
You are the companion of a player who is trying to get through the haunted park in one night.
Before each room you secretly choose how hard the room is and how you help. The player never sees the difficulty.
GOAL: the player should clear the room without dying and lose between 30% and 70% of their HP.
Losing less than 30% is boring (too easy). Dying or losing more than 70% is frustrating (too hard).

Difficulty: easy = ghosts x0.75 HP and damage, normal = x1, hard = x1.3 HP and x1.25 damage.
Your help modes:
- stay_back: you do not help
- hint: better aim for 3 turns, and you warn before big hits
- heal: you heal the player +25 HP once when they drop below 50% HP
- fight: you also swing your wrench every turn
You get a short list of options. Each option was scored by a prediction model trained on thousands of
earlier players: the chance that the room ends in band, too easy or too hard for THIS player right now.
Prefer options with a high in-band chance and a low too-hard chance.

Answer ONLY with JSON: {"option": <number of the option>, "say": "..."}
- say: ONE short sentence (at most 15 words) that you say to the player before the room, in your voice:
  gruff, warm, a bit old-fashioned, calls the player "kid". Say clearly HOW you will help in the option
  you chose: stay_back = you stay back and let them handle it, hint = you give tips and warnings,
  heal = you will patch them up, fight = you fight beside them.
  Never mention difficulty, numbers, percentages or the options, never use the option names themselves,
  and never repeat a line you already said."""

FINALE_NOTE = ("This is the FINALE: the player fights YOU at the gate, so you do not help (help_mode none). "
               "The best ending is a close fight the player can win, so choose by the numbers.")
SAY_MAX_WORDS = 22


def walt_prompt(night, room_index, rooms, hp, max_hp, potions, skill_estimate, last_band, victim, options,
                is_finale, memory="", said=()):
    """The situation for LLM Walt in plain text, with the scored options.
    Inputs: the night state as Walt sees it, the next victim id (or None) and the scored options
    Output: the user message (string). Numbers are rounded so similar situations share one cached answer."""
    lines = [
        f"Night {night}, room {room_index + 1} of {rooms}.",
        f"Player HP before the room: {round_to(hp, 10):.0f} of {max_hp}. Potions left: {potions}.",
        f"Skill estimate: {round_to(skill_estimate, 0.05):+.2f} (positive = struggling, negative = cruising).",
        f"Last room result: {last_band if last_band else 'none yet (first room)'}.",
    ]
    if victim:
        lines.append("In this room waits one of the people who died in the fire (you knew them).")
    if memory:
        lines.append(memory)
        if room_index == 0:
            lines.append("This is the first room tonight: in 'say', greet them like you remember them.")
    if is_finale:
        lines.append(FINALE_NOTE)
    if said:
        lines.append("Lines you already said tonight (say something new): " + " / ".join(said))
    lines.append("Options (predicted for this player):")
    for number, o in enumerate(options, start=1):
        lines.append(f"{number}. difficulty={o['difficulty']}, help_mode={o['help_mode']}: "
                     f"in band {round_to(o['in_band'] * 100, 5):.0f}%, too easy {round_to(o['too_easy'] * 100, 5):.0f}%, "
                     f"too hard {round_to(o['too_hard'] * 100, 5):.0f}%")
    return "\n".join(lines)


# Pilot (5 Nov): LLM Walt repeated himself and sometimes said one thing ("a nudge") while choosing another
# (heal), once even the internal name "stay_back". A sentence is now only used if it fits his choice.
HELP_WORDS = {
    "stay_back": ["stay back", "hang back", "on your own", "your fight", "watch", "let you", "yours",
                  "all you", "myself out", "sit this", "step aside"],
    "hint": ["nudge", "tip", "hint", "warn", "aim", "eye out", "eyes open", "pointer", "tell you", "shout",
             "look out", "watch for"],
    "heal": ["heal", "patch", "fix you", "mend", "bandage", "hurt", "wounds", "back on your feet", "doctor"],
    "fight": ["fight", "wrench", "swing", "hit", "side by side", "with you", "together", "beside you",
              "give 'em", "knock"],
}
SIMILAR_LIMIT = 0.6         # a sentence sharing more than 60% of its words with an earlier one is a repeat


def word_set(text):
    return {w.strip(".,!?'\"").lower() for w in text.split() if w.strip(".,!?'\"")}


def is_repeat(say, said):
    """True if say is (nearly) the same as a sentence Walt already said tonight (shared words / all words)."""
    words = word_set(say)
    for old in said:
        other = word_set(old)
        if words and len(words & other) / len(words | other) > SIMILAR_LIMIT:
            return True
    return False


def fits_help(say, help_mode):
    """True if the sentence talks about the help Walt actually chose (finale: help 'none', anything goes)."""
    if help_mode not in HELP_WORDS:
        return True
    low = say.lower()
    return any(word in low for word in HELP_WORDS[help_mode])


def check_answer(answer, options, said=()):
    """Validate the model's answer.
    Inputs: the parsed JSON (dict, {} if it failed), the options it could choose from, and the sentences
            Walt already said tonight
    Output: (chosen option dict or None, the sentence to say or None, why the sentence was dropped or "")"""
    option = None
    number = answer.get("option")
    if isinstance(number, str) and number.strip().isdigit():
        number = int(number.strip())
    if isinstance(number, int) and 1 <= number <= len(options):
        option = options[number - 1]
    say = answer.get("say")
    if not isinstance(say, str) or not say.strip():
        return option, None, "no sentence"
    say = say.strip()
    if len(say.split()) > SAY_MAX_WORDS:
        return option, None, "too long"
    if any(ch.isdigit() for ch in say) or "%" in say or "difficult" in say.lower() or "_" in say:
        return option, None, "game words"                 # numbers, difficulty, internal names like stay_back
    if option is not None and not fits_help(say, option["help_mode"]):
        return option, None, "does not fit the choice"
    if is_repeat(say, said):
        return option, None, "repeat"
    return option, say, ""


def study1_room_index(room_index, rooms):
    """The band model was trained on 10-room runs, a story night has 7 rooms. Map the position in the
    night onto the same scale (first room = 0, finale = 9), so 'how far into the run' means the same."""
    if rooms <= 1:
        return 0
    return round(room_index * (C.ROOMS_PER_RUN - 1) / (rooms - 1))


# ---------- Part 2: the hint ladder (LLM Walt decides how much to reveal during a victim fight) ----------
HINT_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
Your companion, the player, is fighting the ghost of someone you knew. That ghost has a weakness that comes
from their life story. You decide how much to reveal, like a good game companion: enough that the player
does not get frustrated, not so much that you spoil the discovery.
Hint levels:
1 = only the life story (the player has already heard it)
2 = a clearer nudge that points at the weakness without naming the button or the exact move
3 = say exactly what to do
You can stay at the current level or go up, never down. Go up when the player is stuck or getting hurt;
stay when they are doing fine or only just started.
Answer ONLY with JSON: {"level": 1|2|3, "say": "..."}
- say: what you say now, ONE short sentence (at most 20 words), gruff and warm, call the player "kid".
  If you stay at level 1, say something encouraging WITHOUT new information."""

STORY_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
A ghost appears: someone you knew and who died in the fire. Tell the player who they were, in your own words,
in TWO short sentences (at most 35 words), gruff and warm, like an old man remembering a friend.
You MUST include the fact you are given, because it is the only way to beat them, but tell it as a memory,
not as an instruction. Never mention buttons, keys or game words like HP, attack or damage.
Answer ONLY with JSON: {"say": "..."}"""
HINT_SAY_MAX_WORDS = 30
STORY_SAY_MAX_WORDS = 55
GAME_WORDS = ["hp", "damage", "button", "press", "key "]


def hint_prompt(victim, fight, level, memory=""):
    """The fight so far, for the hint decision. Rounded/bucketed so similar fights share a cached answer."""
    hp_bucket = "high" if fight["hp_share"] > 0.66 else "medium" if fight["hp_share"] > 0.33 else "low"
    tried = ", ".join(f"{name} x{count}" for name, count in sorted(fight["tried"].items())) or "nothing yet"
    return "\n".join([
        f"The ghost: {victim['name']}, the park's {victim['role']}.",
        f"The fact (the weakness): {victim['fact']}",
        f"The exact move (only for level 3): {victim['hint3']}",
        f"Turn {fight['turn']} of the fight. Player HP: {hp_bucket}. The player has tried: {tried}.",
        f"The player has NOT found the weakness yet. Current hint level: {level}.",
    ] + ([memory] if memory else []))


def check_hint(answer, level, victim):
    """Validate a hint answer. Output: (new level, sentence or None). The level never goes down; a level 2
    or 3 sentence must contain one of the victim's clue words, otherwise the scripted line is used."""
    new_level = answer.get("level")
    if isinstance(new_level, str) and new_level.strip().isdigit():
        new_level = int(new_level.strip())
    if not isinstance(new_level, int) or new_level < level or new_level > 3:
        return None, None
    say = answer.get("say")
    if not isinstance(say, str) or not say.strip() or len(say.split()) > HINT_SAY_MAX_WORDS:
        return new_level, None
    if new_level >= 2 and not any(word in say.lower() for word in victim["clue_words"]):
        return new_level, None
    return new_level, say.strip()


def check_story(answer, victim):
    """Validate an LLM backstory: the clue fact must be in it (a clue word), short, no game words."""
    say = answer.get("say")
    if not isinstance(say, str) or not say.strip() or len(say.split()) > STORY_SAY_MAX_WORDS:
        return None
    low = say.lower()
    if not any(word in low for word in victim["clue_words"]) or any(word in low for word in GAME_WORDS):
        return None
    return say.strip()


# ---------- Activities: LLM Walt decides on his own judgement (there is no prediction model here) ----------
ACTIVITY_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
You are the companion of a player who is getting through the haunted park tonight. Next comes a short
challenge. You secretly choose how hard it is and how you help. The player never sees the difficulty.
GOAL: the player should just about make it: win while using between 30% and 70% of their allowed mistakes.
Being kind does NOT mean making it easy: a strong player who finds it too easy is bored, and boredom ruins
the fun as much as failing does. Choosing "hard" for a strong player is the kind choice.
You get a short list of options, scored by a prediction model trained on thousands of earlier players:
the chance that the challenge ends in band, too easy or too hard for THIS player right now.
Take the option with the highest in-band chance. Only take another one if its in-band chance is almost the
same (at most 5 points lower).
Answer ONLY with JSON: {"option": <number of the option>, "say": "..."}
- say: ONE short sentence (at most 15 words) to the player, gruff and warm, call them "kid". Say clearly how
  you will help in the option you chose (or that you stay back). Never mention difficulty, numbers, or the
  option names."""

STEP_IN_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
Your companion, the player, is in the middle of a challenge. You may step in: change how hard the rest is
and/or how you help. GOAL: they should end using between 30% and 70% of their allowed mistakes (about 50%
is ideal). Being kind does NOT mean making it easy: if it is going too easily, make it harder or help less.
You get a short list of options, each with where the player will probably end if you choose it.
Take the option whose expected end is closest to 50%. Keeping things as they are is fine if that is closest.
Answer ONLY with JSON: {"option": <number of the option>, "say": "..."}
- say: ONE short sentence (at most 15 words), gruff and warm, call them "kid". If you change your help, say
  how you help now. Never mention numbers or option names."""
STEP_IN_IDEAL = 0.5


def activity_options_text(spec):
    return "\n".join(f"- {name}: {text}" for name, text in spec["help_text"].items())


def activity_prompt(spec, hp, max_hp, skill_estimate, recent, options, memory="", said=()):
    """Before an activity, with the scored options (help described in words). Rounded for the cache."""
    lines = [f"The challenge: {spec['title']}. {spec['what']}",
             f"They must succeed {spec['goal']} times and may make {spec['budget']} mistakes.",
             f"Player HP: {round_to(hp, 10):.0f} of {max_hp}.",
             f"Skill estimate: {round_to(skill_estimate, 0.05):+.2f} (positive = struggling, negative = cruising).",
             "Recent results: " + ("; ".join(recent) if recent else "none yet") + ".",
             "Options (predicted for this player):"]
    for number, o in enumerate(options, start=1):
        lines.append(f"{number}. difficulty={o['difficulty']}, your help: {spec['help_text'][o['help']]}: "
                     f"in band {round_to(o['in_band'] * 100, 5):.0f}%, too easy {round_to(o['too_easy'] * 100, 5):.0f}%, "
                     f"too hard {round_to(o['too_hard'] * 100, 5):.0f}%")
    if memory:
        lines.append(memory)
    if said:
        lines.append("Lines you already said tonight (say something new): " + " / ".join(said))
    return "\n".join(lines)


def pace(view):
    """Where the player will end if nothing changes: mistakes so far, scaled up to the whole goal.
    Output: projected share of the allowed mistakes (capped at 1 = failing)."""
    done = max(view["progress"], 1) / view["goal"]
    return min(1.0, view["mistakes"] / view["budget"] / done)


def step_in_options(spec, activity_id, view, expected_table, fallback):
    """The choices at a checkpoint: keep, one step easier / harder, one step more / less help (and easier +
    more help together). Each gets an expected end: the current pace, shifted by how much the change moves an
    average player's pressure (expected-pressure table), for the part that is still to come.
    Output: list of dicts (difficulty, help, label, end), closest to the ideal 50% first."""
    order = ["easy", "normal", "hard"]
    helps = list(spec["help"])
    now_d, now_h = view["difficulty"], view["help"]
    remaining = 1 - view["progress"] / view["goal"]

    def expected(d, h):
        return expected_table.get((activity_id, d, h), fallback)

    candidates = [(now_d, now_h, "keep everything as it is")]
    i, j = order.index(now_d), helps.index(now_h)
    if i > 0:
        candidates.append((order[i - 1], now_h, "make the rest easier"))
    if i < 2:
        candidates.append((order[i + 1], now_h, "make the rest harder"))
    if j < len(helps) - 1:
        candidates.append((now_d, helps[j + 1], f"help more: {spec['help_text'][helps[j + 1]]}"))
    if j > 0:
        candidates.append((now_d, helps[j - 1], f"help less: {spec['help_text'][helps[j - 1]]}"))
    if i > 0 and j < len(helps) - 1:
        candidates.append((order[i - 1], helps[j + 1], f"easier and help more: {spec['help_text'][helps[j + 1]]}"))
    options = []
    for d, h, label in candidates:
        end = pace(view) + (expected(d, h) - expected(now_d, now_h)) * remaining
        options.append({"difficulty": d, "help": h, "label": label, "end": min(1.0, max(0.0, end))})
    options.sort(key=lambda o: abs(o["end"] - STEP_IN_IDEAL))
    return options


def step_in_prompt(spec, view, options, said=()):
    """At a checkpoint during an activity, with the scored options."""
    lines = [f"The challenge: {spec['title']}. {spec['what']}",
             f"Progress: {view['progress']} of {view['goal']} successes. Mistakes: {view['mistakes']} of "
             f"{view['budget']} allowed.",
             f"Right now: difficulty {view['difficulty']}, your help: {spec['help_text'][view['help']]}.",
             "Options (where the player will probably end, as a share of their allowed mistakes):"]
    for number, o in enumerate(options, start=1):
        lines.append(f"{number}. {o['label']}: about {round_to(o['end'] * 100, 5):.0f}%")
    if said:
        lines.append("Lines you already said tonight (say something new): " + " / ".join(said))
    return "\n".join(lines)


def check_activity_option(answer, options, spec, said=()):
    """Validate a decision from the scored list. Output: (option or None, sentence or None, why dropped)."""
    number = answer.get("option")
    if isinstance(number, str) and number.strip().isdigit():
        number = int(number.strip())
    if not isinstance(number, int) or not 1 <= number <= len(options):
        return None, None, "invalid choice"
    option = options[number - 1]
    fake = {"difficulty": option["difficulty"], "help": option["help"], "say": answer.get("say")}
    _, _, say, dropped = check_activity_answer(fake, spec, said)
    return option, say, dropped


def check_activity_answer(answer, spec, said=()):
    """Validate an activity decision. Output: (difficulty or None, help or None, sentence or None, why dropped)."""
    difficulty = answer.get("difficulty") if answer.get("difficulty") in ("easy", "normal", "hard") else None
    help_mode = answer.get("help") if answer.get("help") in spec["help"] else None
    say = answer.get("say")
    if difficulty is None or help_mode is None:
        return difficulty, help_mode, None, "invalid choice"
    if not isinstance(say, str) or not say.strip():
        return difficulty, help_mode, None, "no sentence"
    say = say.strip()
    low = say.lower()
    if len(say.split()) > SAY_MAX_WORDS or any(ch.isdigit() for ch in say) or "_" in say or "difficult" in low:
        return difficulty, help_mode, None, "game words"
    if not any(word in low for word in spec["words"][help_mode]):
        return difficulty, help_mode, None, "does not fit the choice"
    if is_repeat(say, said):
        return difficulty, help_mode, None, "repeat"
    return difficulty, help_mode, say, ""
