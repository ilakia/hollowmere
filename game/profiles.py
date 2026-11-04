"""
Part 3 of LLM Walt: he remembers the player across nights.

After every story night a short profile of the player (by player ID, a nickname, never a real name) is
updated in data/player_profiles.json:
  nights played, last skill estimate, which victims they met and how (weakness found? at which hint
  level?), deaths, how they like to fight (attack / defend share), Night B keepsakes found.
Only LLM Walt uses it: the profile is turned into a few plain sentences that go into his prompts, so he can
greet the player like he remembers them and judge how much help they need. Silent and scripted Walt have
no memory (that is part of the comparison). data/ is not in git, so profiles are never committed.
"""
import json
from pathlib import Path

from .victims import VICTIMS

PROFILE_PATH = Path("data/player_profiles.json")


def load_profiles(path=PROFILE_PATH):
    """Output: dict player_id -> profile (empty if the file does not exist yet)."""
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(player_id, path=PROFILE_PATH):
    """Output: this player's profile dict, or None for a new player (or no ID)."""
    if not player_id:
        return None
    return load_profiles(path).get(player_id)


def update_profile(player_id, rows, skill_estimate, keepsakes=None, path=PROFILE_PATH):
    """Add one finished night to the player's profile and save the file.
    Inputs: player ID, the night's room rows, Walt's skill estimate at the end of the night, and the
            keepsakes found (Night B, list of names) if any."""
    if not player_id:
        return
    profiles = load_profiles(path)
    p = profiles.get(player_id, {"nights": [], "victims": {}, "deaths": 0, "attacks": 0, "defends": 0,
                                 "keepsakes": []})
    p["nights"].append(rows[0]["night"])
    p["last_outcome"] = rows[-1]["run_outcome"]
    p["skill_estimate"] = round(skill_estimate, 3)
    for r in rows:
        p["deaths"] += int(r["deaths"])
        p["defends"] += int(r["defends"])
        p["attacks"] += int(r["hits"]) + int(r["misses"])
        if r.get("victim"):
            p["victims"][r["victim"]] = {"found": bool(r["weakness_used"]),
                                         "turn_found": r.get("turn_first_used"),
                                         "hint_level_at_use": r.get("hint_level_at_use"),
                                         "hint_level_max": r.get("hint_level_max", 0)}
    if keepsakes:
        p["keepsakes"] = sorted(set(p["keepsakes"]) | set(keepsakes))
    profiles[player_id] = p
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profiles, indent=1), encoding="utf-8")


def memory_text(profile):
    """The profile as a few plain sentences for LLM Walt's prompts. Output: text, or "" for a new player."""
    if not profile or not profile.get("nights"):
        return ""
    lines = [f"You remember this player: they have been through {len(profile['nights'])} night(s) with you "
             f"(last night they {'escaped' if profile.get('last_outcome') == 'escaped' else 'did not escape'})."]
    total = profile["attacks"] + profile["defends"]
    if total:
        style = "charges straight in" if profile["attacks"] / total > 0.75 else "plays carefully and defends a lot"
        lines.append(f"Their style: {style}. They died {profile['deaths']} time(s) so far.")
    for victim_id, v in profile["victims"].items():
        name = VICTIMS[victim_id]["name"]
        if v["found"]:
            how = "on their own" if not v.get("hint_level_at_use") or v["hint_level_at_use"] <= 1 else \
                  f"after your level {v['hint_level_at_use']} hint"
            lines.append(f"They figured out {name}'s weakness {how}.")
        else:
            lines.append(f"They never figured out {name}'s weakness.")
    if profile.get("keepsakes"):
        lines.append(f"They found these keepsakes of yours: {', '.join(profile['keepsakes'])}.")
    return " ".join(lines)
