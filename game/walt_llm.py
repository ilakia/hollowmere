"""
LLM Walt (Study 2): the prompt for the companion version of the llm_risk director from Study 1.

Before every room of a story night, LLM Walt quietly chooses the difficulty of the room and how he
helps. Exactly as llm_risk in Study 1, every allowed option is first scored by the band model
(game/risk.py) for THIS player, and the model picks one of the best options. New in Study 2: he also
says one short sentence to the player, in character, which is spoken aloud in the game.

The model answers with the NUMBER of an option (easier to check than free text) plus the sentence.
Anything invalid falls back to scripted Walt's choice and is logged as decision_source = "fallback".
"""
from . import config as C
from .llm import round_to

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

Answer ONLY with JSON: {"option": <number of the option>, "say": "...", "reason": "..."}
- say: ONE short sentence (at most 20 words) that you say to the player before the room, in your voice:
  gruff, warm, a bit old-fashioned, calls the player "kid". Say how you will help (or that you stay back).
  Never mention difficulty, numbers, percentages or the options.
- reason: one short sentence for the researchers: why this option."""

FINALE_NOTE = ("This is the FINALE: the player fights YOU at the gate, so you do not help (help_mode none). "
               "The best ending is a close fight the player can win, so choose by the numbers.")
SAY_MAX_WORDS = 22


def walt_prompt(night, room_index, rooms, hp, max_hp, potions, skill_estimate, last_band, victim, options,
                is_finale, memory=""):
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
    lines.append("Options (predicted for this player):")
    for number, o in enumerate(options, start=1):
        lines.append(f"{number}. difficulty={o['difficulty']}, help_mode={o['help_mode']}: "
                     f"in band {round_to(o['in_band'] * 100, 5):.0f}%, too easy {round_to(o['too_easy'] * 100, 5):.0f}%, "
                     f"too hard {round_to(o['too_hard'] * 100, 5):.0f}%")
    return "\n".join(lines)


def check_answer(answer, options):
    """Validate the model's answer.
    Inputs: the parsed JSON (dict, {} if it failed) and the options it could choose from
    Output: (chosen option dict or None, the sentence to say or None, the reason text)"""
    option = None
    number = answer.get("option")
    if isinstance(number, str) and number.strip().isdigit():
        number = int(number.strip())
    if isinstance(number, int) and 1 <= number <= len(options):
        option = options[number - 1]
    say = answer.get("say")
    if not isinstance(say, str) or not say.strip():
        say = None
    else:
        say = say.strip()
        too_long = len(say.split()) > SAY_MAX_WORDS
        leaks = any(ch.isdigit() for ch in say) or "%" in say or "difficult" in say.lower()
        if too_long or leaks:
            say = None                   # the sentence breaks the rules: Walt says his scripted line instead
    reason = answer.get("reason") if isinstance(answer.get("reason"), str) else ""
    return option, say, reason


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
Answer ONLY with JSON: {"level": 1|2|3, "say": "...", "reason": "..."}
- say: what you say now, ONE or TWO short sentences (at most 25 words), gruff and warm, call the player "kid".
  If you stay at level 1, say something encouraging WITHOUT new information.
- reason: one short sentence for the researchers."""

STORY_SYSTEM_PROMPT = """You are Walt, an old park mechanic who died in the 1987 fire at Hollowmere Park.
A ghost appears: someone you knew and who died in the fire. Tell the player who they were, in your own words,
in TWO or THREE short sentences (at most 45 words), gruff and warm, like an old man remembering a friend.
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
