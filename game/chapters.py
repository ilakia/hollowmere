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
        "travel_lines": ["This way, kid.", "Stay close.", "Don't touch anything that moves.", "Almost there.",
                         "These rides were something, back then.", "Hear that? Keep walking."],
        "reveal_line": "I never left this park, kid. Neither will you.",
        "flashback": "clues",
        "finale_enemy": "walt",                  # Night A: the player fights Walt himself
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
        "gate_line": "The gate again. Something's holding it shut, kid. Smells like smoke.",
        "reveal_line": "The smoke from that night! It never left. Together, kid!",
        "travel_lines": ["Keep your eyes on the ground, kid. My things must be somewhere.",
                         "I walked this path every night for thirty years. Can't remember the last one.",
                         "Rosa used to stand right there with her camera.",
                         "Something shiny back there? No... keep looking.",
                         "The boats... I fixed their motors the week before.",
                         "Almost at the gate. Let's see if it lets us through this time."],
        "flashback": "keepsakes",
        "finale_enemy": "smoke",                 # Night B: Walt fights WITH the player against the smoke
        "flashback_intro": "Let me see what you found, kid.",
        "flashback_none": "You found nothing of mine. Maybe it's better I don't remember.",
        "flashback_end": "There's something I never told you, kid. About the fire.",
        "finale_start": "Hit it while I keep it busy, kid!",
        "farewell": "The gate's open. Come back tomorrow night, kid. I want to remember the rest.",
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
        "gate_line": "The gate. This is where it ended, kid. The fire's still here.",
        "reveal_line": "That's the fire that took us. One last fight, kid. For all of us.",
        "travel_lines": ["Smell that? Same as that night. Stay low, kid.",
                         "Benny's music box was the last thing I heard before the roof came down.",
                         "Henry kept shouting for people to get out. Loudest man in the park.",
                         "The fire jumped from roof to roof, right along here.",
                         "The boats burned on the water. Strangest thing I ever saw.",
                         "Nearly at the gate. I know what's waiting there now."],
        "flashback": "fire",
        "finale_enemy": "blaze",                 # Night C: together against the fire itself
        "flashback_intro": "June 1987. Here's what really happened.",
        "flashback_missing": "A memory you never found.",
        "flashback_end": ("It wasn't anyone's fault, kid. Just an old radio. I got the gate open, "
                          "then I went back in for them."),
        "finale_start": "Now, kid! Put it out for good!",
        "farewell": "Thank you, kid. We can all go home now.",
        "fire": True,
    },
}
# New places for Night B and C. Each new room keeps the FIGHT of the room it replaces (same ghosts, same
# threat, same beat id in the data), so difficulty tables, the band rule and the bot checks stay valid;
# only the place, its name, its short story and its look (window/pieces_lake.py, pieces_1987.py) change.
NIGHT_ZONE = {"B": 5, "C": 6}           # window/scenery_nights.py: 5 = the Lakeside, 6 = June 1987
ROOM_SKINS = {
    "B": {
        "z1_ring_toss": ("bumper_cars", "Bumper Cars",
                         ("The dodgems still spark under the roof.", "Nobody has paid for a ride in forty years.")),
        "z1_photo_booth": ("photo_pier", "Rosa's Photo Pier",
                           ("At the end of the pier, Rosa's camera still stands on its tripod.",
                            "Her last photos hang on the line, curling in the damp.")),
        "z2_tilted_room": ("swan_boats", "The Swan Boats",
                           ("White swans bob on the black water.", "One of them has lost its head.")),
        "z2_mirrors": ("mirror_maze", "Lily's Mirror Maze",
                       ("Glass walls by the lake. Lily ran this maze.", "Your reflection walks with you. Walt's does not.")),
        "z3_tunnel_boats": ("bandstand", "The Bandstand",
                            ("The band played here every summer evening.", "The music stands are empty. The music is not.")),
        "z3_haunted_manor": ("wild_mouse", "Wild Mouse Coaster",
                             ("A little mouse car is stuck at the top of the hill.", "It rattles when you look away.")),
        "finale_gate": ("lake_gate", "The Lake Gate",
                        ("The old staff gate by the water.", "Smoke pours through the bars.")),
    },
    "C": {
        "z1_carousel": ("carousel_1987", "Benny's Carousel, 1987",
                        ("The bulbs are bright, the paint is new.", "And the canopy is on fire.")),
        "z1_ticket_booth": ("main_street", "Main Street",
                            ("SUMMER '87. Arcades, candy and popcorn.", "The roofs are starting to burn.")),
        "z2_clown_alley": ("henry_stage", "The Great Henry's Stage",
                           ("Henry's posters on every wall.", "His voice still booms over the crackling.")),
        "z2_barrel": ("helter_skelter", "Helter Skelter",
                      ("The slide spirals round the tower.", "Smoke pours out of the top window.")),
        "z3_tunnel_boats": ("food_court", "The Food Court",
                            ("Burgers, ice cream, picnic tables.", "The kitchen is already burning.")),
        "z3_log_flume": ("workshop_1987", "Walt's Workshop",
                         ("W. Hale - Repairs. June 1987.", "The old radio on the bench is throwing sparks.")),
        "finale_gate": ("main_gate_1987", "The Main Gate",
                        ("The way out, that night.", "Flames run along the arch.")),
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
        normal += story["travel_lines"]
        (ghost if story["finale_enemy"] == "walt" else normal).append(story["reveal_line"])
        (ghost if story["finale_enemy"] == "walt" else normal).append(story["finale_start"])
        for key in ("flashback_intro", "flashback_none", "flashback_end",
                    "farewell", "flashback_missing"):
            if story.get(key):
                ghost.append(story[key])
    normal += [k["memory"] for k in KEEPSAKES]
    ghost += [k["fire"] for k in KEEPSAKES]
    return normal, ghost
