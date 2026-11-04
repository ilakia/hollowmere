"""
The three nights as three chapters of one story (played in the order A -> B -> C).

  Night A, "The First Night":  Walt seems human. Hidden signs in the park; at the gate he reveals he is a
                               ghost and shows the signs the player walked past (clue flashback).
  Night B, "You Came Back":    Walt is a ghost all night, and he cannot remember the night of the fire.
                               Five burnt keepsakes lie along the walks (press E when one glints). At the
                               gate he remembers what the found keepsakes show.
  Night C, "The Fire":         The park burns a little more with every room. Before the gate the fire of
                               June 1987 is shown, one scene per keepsake found in Night B (the missed ones
                               stay burnt-out frames). The truth, the last fight and the true ending.

Only text and settings live here; the window (window/story_window.py) draws it. The fights, the victims
and every measure are the same in all three nights.
"""

# Night B: the keepsakes. "room" = the walk TO this room of the night (0-based) is where it lies.
# "memory" = what Walt remembers in Night B; "fire" = its scene of the fire in Night C (beat = the place).
KEEPSAKES = [
    {"id": "workshop_key", "name": "Walt's workshop key", "room": 0, "beat": "z3_workshop",
     "memory": "My workshop key. I locked up early that night. Why can't I remember why?",
     "fire": "My workshop. The old radio was still on. The wires sparked, and that's where it started."},
    {"id": "ticket_roll", "name": "a scorched ticket roll", "room": 1, "beat": "z1_ticket_booth",
     "memory": "Martha's tickets. She was counting the night's money when the lights went out.",
     "fire": "Nine fifteen. Martha's lamp went out, and the smoke came through the dark."},
    {"id": "photo", "name": "a photo with burnt edges", "room": 2, "beat": "z1_photo_booth",
     "memory": "Rosa took this one that afternoon. The whole staff. The last picture of all of us.",
     "fire": "Rosa ran back for her camera. I shouted at her to leave it. She didn't listen."},
    {"id": "pocket_watch", "name": "a melted pocket watch", "room": 4, "beat": "z1_carousel",
     "memory": "My pocket watch. Stopped at nine twenty-two. Why that minute?",
     "fire": "Nine twenty-two. Benny wouldn't leave his carousel. The music box was still playing."},
    {"id": "newspaper", "name": "a newspaper scrap", "room": 5, "beat": "z3_ghost_train",
     "memory": "'Mechanic went back in.' That's what it says. Went back in... for who?",
     "fire": "I got the gate open. Then I heard Ned's whistle in the smoke, and I went back in."},
]
KEEPSAKE_BY_ID = {k["id"]: k for k in KEEPSAKES}

NIGHT_STORY = {
    "A": {
        "title": "The First Night",
        "walt_is_ghost": False,
        "intro": None,                           # the normal "Midnight" card
        "gate_line": "The gate is just ahead. Nearly out, kid.",
        "reveal_line": "I never left this park, kid. Neither will you.",
        "flashback": "clues",
        "finale_start": "Now you know, kid. Let's finish this.",
        "farewell": "Not bad, kid. Not bad at all. Go on. Don't look back.",
        "fire": False,
    },
    "B": {
        "title": "You Came Back",
        "walt_is_ghost": True,
        "intro": ("The second night",
                  ["You wake up inside Hollowmere Park again. The gates are locked again.",
                   "A green light comes through the fog. 'You came back, kid. So now you know what I am.'",
                   "'Funny thing. I can't remember the night of the fire. If you find any of my things, pick "
                   "them up.'  (Press E when something glints on the way.)"]),
        "intro_line": "You came back, kid. So now you know what I am.",
        "gate_line": "The gate again. It won't open for me, kid. It never has.",
        "reveal_line": "Beat me, and the park has to let you go.",
        "flashback": "keepsakes",
        "flashback_intro": "Let me see what you found, kid.",
        "flashback_none": "You found nothing of mine. Maybe it's better I don't remember.",
        "flashback_end": "There's something I never told you, kid. About the fire.",
        "finale_start": "Come on then, kid. One more time.",
        "farewell": "Come back tomorrow night, kid. I want to remember the rest.",
        "fire": False,
    },
    "C": {
        "title": "The Fire",
        "walt_is_ghost": True,
        "intro": ("June 1987",
                  ["The third night. The air smells of smoke.",
                   "The park is burning, the way it burned in 1987. Every attraction a little more.",
                   "'Tonight I remember everything, kid. Stay close.'"]),
        "intro_line": "Tonight I remember everything, kid. Stay close.",
        "gate_line": "The gate. This is where it ended, kid.",
        "reveal_line": "One last fight, kid. Then we can all go.",
        "flashback": "fire",
        "flashback_intro": "June 1987. Here's what really happened.",
        "flashback_missing": "A memory you never found.",
        "flashback_end": ("It wasn't anyone's fault, kid. Just an old radio. I got the gate open, "
                          "then I went back in for them."),
        "finale_start": "Let's finish it. For all of us.",
        "farewell": "Thank you, kid. We can all go home now.",
        "fire": True,
    },
}
FIRE_GLOW_PER_ROOM = 14       # Night C: the orange glow over the park grows by this much (alpha) per room


def keepsake_for_room(night, room_index):
    """The keepsake lying on the walk to this room (Night B only), or None."""
    if night != "B":
        return None
    for k in KEEPSAKES:
        if k["room"] == room_index:
            return k
    return None


def all_lines():
    """Every fixed line Walt says in the chapters (so the voice files can be prepared at the start).
    Output: (normal lines, ghost lines)."""
    normal, ghost = [], []
    for story in NIGHT_STORY.values():
        if story.get("intro_line"):
            normal.append(story["intro_line"])
        normal.append(story["gate_line"])
        for key in ("reveal_line", "flashback_intro", "flashback_none", "flashback_end", "finale_start",
                    "farewell", "flashback_missing"):
            if story.get(key):
                ghost.append(story[key])
    normal += [k["memory"] for k in KEEPSAKES]
    ghost += [k["fire"] for k in KEEPSAKES]
    return normal, ghost
