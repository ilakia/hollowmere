"""
Study 2 (story mode "Night of the Fire"): the six victim ghosts of the 1987 fire and their fights.

Each victim has a weakness that comes from their story. Fighting them the normal way works, but it is
slow and costly; using the weakness makes the fight short. Nothing here is used by the normal game, the
bots or any Study 1 result.

A victim fight is turn-based like a normal room (game/engine.py): each turn the player acts, Walt helps
(same help modes as in Study 1), then the victim acts. The player sees a "cue" when something special is
about to happen (the lights flicker, the music stops, the camera goes up, the whistle blows).

Actions in a victim room: "attack", "attack:0" / "attack:1" (choose a target, twins only), "defend",
"potion", "rest" (as in the normal game) and two story-mode actions: "shine" (Walt's flashlight) and
"call:<name>" (call the victim by a name).
"""
from . import config as C

VICTIMS = {
    "martha": {"name": "Martha Bell", "role": "ticket seller", "beat": "z1_ticket_booth", "hp": 120, "damage": 8,
               "accuracy": 0.8, "weakness": "shine",
               "fact": "Martha was terrified of the dark and never once turned off the lamp at her ticket booth.",
               "clue_words": ["dark", "lamp", "light"],
               "hint2": "Martha always went quiet when the light was on her. You've got my flashlight, kid.",
               "hint3": 'Shine the flashlight on her, kid! Press L! The light freezes her.',
               "question": ('What was Martha Bell afraid of?', 'The dark', ['Fire', 'Crowds']),
               "scripted": "That's Martha Bell. Sold tickets here for thirty years. Hated the dark, that woman. "
                           "Never once turned off the lamp at her booth."},
    "benny": {"name": "Benny Ortiz", "role": "carousel operator", "beat": "z1_carousel", "hp": 60, "damage": 7,
              "accuracy": 0.8, "weakness": "quiet_attack",
              "fact": "Benny kept the carousel turning all day; the only time he stood still was when the music box ran down.",
              "clue_words": ["music", "still", "stop"],
              "hint2": 'Watch the music box, kid. Hold on while it plays. When it runs down, Benny stands still.',
              "hint3": 'Defend while the music plays, then strike the moment it stops! Not before!',
              "question": ('When did Benny Ortiz stand still?', 'When the music box ran down', ['When it rained', 'When the lights flickered']),
              "scripted": "Benny Ortiz ran this carousel. Never let it stop, not for a second. Only time Benny "
                          "stood still was when the music box ran down."},
    "rosa": {"name": "Rosa Lindqvist", "role": "park photographer", "beat": "z1_photo_booth", "hp": 90, "damage": 6,
             "accuracy": 0.8, "weakness": "shine_lens",
             "fact": "Rosa, the park photographer, used to say a camera is blind to everything but light: point a lamp into the lens when she lifts it and she cannot see a thing.",
             "clue_words": ["lens", "lamp", "light"],
             "hint2": 'Her camera, kid. When she lifts it, give that lens some light.',
             "hint3": 'When she lifts the camera, press L and shine into the lens! Her own flash blinds her.',
             "question": ("What could blind Rosa's camera?", 'A light shone into the lens', ['A loud noise', 'Calling her name']),
             "scripted": "Rosa took everybody's picture. Always said a camera's blind to everything but light. "
                         "Kids used to shine a torch into her lens when she lifted it. Drove her crazy."},
    "henry": {"name": "Henry Pike", "role": "Clown Alley barker", "beat": "z2_clown_alley", "hp": 140, "damage": 6,
              "accuracy": 0.75, "weakness": "call_name", "true_name": "The Great Henry",
              "name_choices": ["Henry Pike", "The Great Henry", "Hank the Barker"],
              "fact": "Henry, the barker of Clown Alley, only calmed down when people called him by his stage name, The Great Henry.",
              "clue_words": ["great henry", "stage name"],
              "hint2": 'He wants to hear his name, kid. Not the one on his paycheck. The one on the posters.',
              "hint3": 'Call him "The Great Henry"! Press N! Calms him right down. And do it again when he gets loud.',
              "question": ('What calmed Henry Pike down?', 'His stage name, The Great Henry', ['A song from the carousel', 'Complete silence']),
              "scripted": "That's Henry Pike, the barker. Loud as a fire bell. Only way to calm him down was to "
                          "call him by his stage name: The Great Henry."},
    "twins": {"name": "Lily Ward", "role": "Hall of Mirrors attendant", "beat": "z2_mirrors", "hp": 45, "damage": 4,
              "accuracy": 0.8, "weakness": "real_target",
              "fact": "Lily, who ran the Hall of Mirrors, never took off her mother's red ribbon; her reflections never had it.",
              "clue_words": ["ribbon", "red"],
              "hint2": 'One of them is real, kid. Look at what the reflections never wear.',
              "hint3": 'Hit the Lily with the red ribbon! Hitting the reflection only heals her.',
              "question": ('How could you tell the real Lily from her reflections?', 'Her red ribbon', ['Her shadow', 'Her voice']),
              "scripted": "Lily Ward ran the Hall of Mirrors. Sweet girl. Never took off her mother's red ribbon. "
                          "Funny thing: her reflections never had it."},
    "ned": {"name": "Ned Carver", "role": "ghost train engineer", "beat": "z3_ghost_train", "hp": 80, "damage": 6,
            "accuracy": 0.75, "weakness": "attack_whistle",
            "fact": "Ned, the ghost train engineer, rode the train every lap; the only moment anyone could reach him was when it came past with its whistle blowing.",
            "clue_words": ["whistle", "came past", "reach"],
            "hint2": "You can't reach Ned while the train is away, kid. Wait for the whistle.",
            "hint3": 'Attack when the whistle blows and the train comes past! Any other time you barely touch him.',
            "question": ('When could you reach Ned Carver?', 'When the train came past, whistle blowing', ['When the train stopped at the station', 'When the lights went out']),
            "scripted": "Old Ned Carver never got off that train. Every lap, all night. Only time you could "
                        "reach him was when it came past, whistle blowing."},
}

# Three nights, each with its own two victims (so a player meets each victim only once) and one activity
# (game/activities.py) in place of one normal fight: the playtest version. The bot-only plan with two
# activities per night is NIGHTS_WITH_ACTIVITIES in game/activities.py.
NIGHTS = {
    "A": ["z1_cotton_candy", "martha", "z2_tilted_room", "act_flashlight", "z3_log_flume", "ned", "finale_gate"],
    "B": ["z1_ring_toss", "rosa", "act_lake", "twins", "z3_tunnel_boats", "z3_haunted_manor", "finale_gate"],
    "C": ["benny", "z2_barrel", "henry", "act_bucket", "z3_tunnel_boats", "z3_log_flume", "finale_gate"],
}
# Night C changes before the playtest: the bucket replaced the smoke escape (pilot), and the Helter Skelter
# (z2_barrel, 4 ghosts) replaced the Ticket Booth (2 weak wisps). In the Ticket Booth players lose only
# 4 / 13 / 18% HP on easy / normal / hard (expected_hp_lost.csv), so no Walt could put it in the 30-70% band;
# the Helter Skelter expects 17 / 46 / 57%, so every Walt can adjust it.

STUNNED_TURNS = 2           # Martha / Rosa after the flashlight: no attacks, take double damage
BLIND_TURNS = 2             # after Rosa's flash: the player's attacks miss
RIDE_RECOIL = 5             # attacking Benny's spinning carousel throws you off
BENNY_MUSIC_TURNS = 2       # the music box runs down every 2nd turn (every 3rd made the fight drag on)
NED_FAR_FACTOR = 1 / 3      # hitting Ned while the train is away: a third of the damage
WRONG_NAME_RAGE = 2         # turns Henry hits 50% harder after a wrong name
HENRY_CALM_TURNS = 3        # the right name calms Henry for 3 turns (no attacks, double damage), then he shouts again
MIRROR_HEAL = 10            # hitting Lily's reflection heals Lily ...
MIRROR_CRACK_HITS = 3       # ... until the mirror cracks after 3 hits and the reflection is gone


def cue_for(victim_id, turn):
    """What the player can see this turn (the 'tell'). turn starts at 1 in each attempt."""
    if victim_id == "benny" and turn % BENNY_MUSIC_TURNS == 0:
        return "music_stopped"          # the only turns Benny stands still
    if victim_id == "rosa" and turn % 3 == 2:
        return "camera_up"              # she flashes at the end of this turn
    if victim_id == "ned" and turn % 3 == 1:
        return "whistle"                # the train (with Ned on it) passes this turn
    if victim_id == "martha" and turn % 4 == 2:
        return "lights_flicker"         # flavour only: she grows when the lights flicker
    return None


def play_victim_room(player, victim_id, help_mode, policy, rng, difficulty="normal", coach=None):
    """One fight against a victim ghost. Changes `player` in place, returns the room's telemetry
    (the same keys as engine.play_room plus the Study 2 measures).
    difficulty scales the victim's HP and damage exactly like normal ghosts (config.DIFFICULTY).
    coach (optional, game/story_mode.py) = Walt's hint ladder: before every turn it may raise the hint
    level and give a line, which the player sees as view["walt_line"] / view["hint_level"]."""
    v = dict(VICTIMS[victim_id])
    v["hp"] = v["hp"] * C.DIFFICULTY[difficulty]["hp_mult"]
    v["damage"] = v["damage"] * C.DIFFICULTY[difficulty]["damage_mult"]
    t = {"hp_start": player.hp, "turns": 0, "hits": 0, "misses": 0, "damage_taken": 0.0, "hp_healed": 0.0,
         "potions_used": 0, "companion_heals": 0, "defends": 0, "defends_on_windup": 0, "windups_seen": 0,
         "deaths": 0, "cleared": False, "quit": False, "out_of_lives": False,
         "victim": victim_id, "weakness_used": False, "turn_first_used": None, "shines": 0,
         "calls": 0, "wrong_calls": 0, "reflection_hits": 0, "blinded_turns": 0,
         "hint_level_max": 0, "hint_level_at_use": None, "hint_lines": 0}
    tried = {}                                         # what the player has tried so far (for the coach)

    def used_weakness():
        if not t["weakness_used"]:
            t["weakness_used"] = True
            t["turn_first_used"] = t["turns"]
            t["hint_level_at_use"] = t["hint_level_max"]   # how much Walt had revealed when it was found

    while True:                                        # one loop = one attempt at the room
        hp = {"main": float(v["hp"]), "reflection": float(v["hp"])}
        real_side = rng.randrange(2)                   # twins: which of the two is the real Lily
        stunned, blind, exposed, rage = 0, 0, False, 0
        reflection_left = MIRROR_CRACK_HITS
        last_action = None
        heal_left = 1 if help_mode == "heal" else 0
        cover_left = 1 if help_mode in C.COVER_HELP_MODES else 0
        died = True
        for turn in range(1, C.MAX_TURNS_PER_ATTEMPT + 1):
            t["turns"] += 1
            cue = cue_for(victim_id, turn)
            t["windups_seen"] += cue in ("camera_up", "whistle")
            targets = None
            if victim_id == "twins":
                if reflection_left > 0:
                    targets = ["real" if side == real_side else "reflection" for side in range(2)]
                else:
                    targets = ["real"]                 # the mirror cracked: only Lily is left
            view = {"hp": player.hp, "max_hp": C.PLAYER_MAX_HP, "potions": player.potions,
                    "victim": victim_id, "victim_hp": hp["main"], "victim_max_hp": v["hp"], "cue": cue,
                    "blind": blind > 0, "stunned": stunned > 0, "targets": targets, "help_mode": help_mode,
                    "turn": turn,                      # lets the window show countdowns (Benny's music box)
                    "tried": dict(tried), "weakness_used": t["weakness_used"],   # for "Walt, help!"
                    # cues that look like a charge-up: players' habit (defend) is NOT the weakness here.
                    # warning False: Walt's generic "it's glowing, DEFEND!" would be wrong advice for victims
                    "wind_up": cue in ("camera_up", "whistle"), "warning": False,
                    "enemies": [(victim_id, hp["main"])]}
            if coach is not None:
                level, line = coach.step({"turn": t["turns"], "weakness_used": t["weakness_used"],
                                          "hp_share": player.hp / C.PLAYER_MAX_HP, "tried": dict(tried)})
                view["hint_level"], view["walt_line"] = level, line
                t["hint_level_max"] = max(t["hint_level_max"], level)
                t["hint_lines"] += line is not None
            action = policy.choose_action(view, rng)
            kind = action.split(":")[0]
            tried[kind] = tried.get(kind, 0) + 1
            defending = False
            damage_mult = 2.0 if (stunned > 0 or exposed) else 1.0

            # 1) the player acts
            if action == "potion" and player.potions > 0:
                player.potions -= 1
                t["potions_used"] += 1
                before = player.hp
                player.hp = min(C.PLAYER_MAX_HP, player.hp + C.POTION_HEAL)
                t["hp_healed"] += player.hp - before
            elif action == "defend" or (action == "rest" and not cover_left):
                defending = True
                t["defends"] += 1
                if cue in ("camera_up", "whistle"):
                    t["defends_on_windup"] += 1
            elif action == "rest":                     # same "Walt covers you" rest as the normal game
                cover_left = 0
                defending = True
                before = player.hp
                player.hp = min(C.PLAYER_MAX_HP, player.hp + C.COVER_HEAL)
                t["hp_healed"] += player.hp - before
                hp["main"] -= C.COVER_WALT_DAMAGE
            elif action == "shine":
                t["shines"] += 1
                if victim_id == "martha" or (victim_id == "rosa" and cue == "camera_up"):
                    used_weakness()                    # Martha fears light; Rosa's own lens blinds her
                    stunned = STUNNED_TURNS + 1        # +1: counted down at the end of this turn
            elif action.startswith("call:"):
                t["calls"] += 1
                if victim_id == "henry" and action[5:] == v["true_name"]:
                    used_weakness()
                    if stunned == 0:                   # calling again while he is calm does nothing
                        stunned = HENRY_CALM_TURNS + 1 # +1: counted down at the end of this turn
                else:
                    t["wrong_calls"] += 1
                    rage = WRONG_NAME_RAGE
            else:                                      # attack (also the fallback for anything unknown)
                target = "real"
                if victim_id == "twins":
                    side = int(action.split(":")[1]) if action.startswith("attack:") else 0
                    target = targets[min(side, len(targets) - 1)]
                hit_chance = policy.accuracy + (C.HINT_ACCURACY_BONUS if help_mode == "hint" and turn <= C.HINT_TURNS else 0.0)
                hits = rng.random() < min(hit_chance, C.MAX_HIT_CHANCE)
                if blind > 0:
                    hits = False
                    t["blinded_turns"] += 1
                ride_recoil = False
                if victim_id == "benny":
                    if cue == "music_stopped":
                        if last_action in ("defend", "rest"):
                            used_weakness()            # waited (defended) for the music to stop, then struck
                            damage_mult = 2.0          # caught him standing still: a clean, double hit
                    else:
                        hits = False                   # thrown off the spinning ride
                        ride_recoil = True
                if victim_id == "ned":
                    if cue == "whistle":
                        used_weakness()                # struck while the train came past
                        damage_mult = 2.0
                    else:
                        damage_mult = NED_FAR_FACTOR   # Ned is far away on the train: only a glancing blow
                if hits and target == "reflection":
                    t["reflection_hits"] += 1
                    reflection_left -= 1
                    hp["main"] = min(v["hp"], hp["main"] + MIRROR_HEAL)
                elif hits:
                    if victim_id == "twins" and t["reflection_hits"] == 0:
                        used_weakness()                # went for the real Lily straight away
                    hp["main"] -= C.PLAYER_ATTACK * damage_mult
                    exposed = False
                    t["hits"] += 1
                else:
                    t["misses"] += 1

            # 2) Walt helps (same rules as in the normal game)
            if help_mode == "fight" and hp["main"] > 0 and rng.random() < C.COMPANION_ACCURACY:
                if victim_id != "benny" or cue == "music_stopped":
                    hp["main"] -= C.COMPANION_DAMAGE
            if heal_left and player.hp < C.COMPANION_HEAL_TRIGGER * C.PLAYER_MAX_HP:
                before = player.hp
                player.hp = min(C.PLAYER_MAX_HP, player.hp + C.COMPANION_HEAL)
                t["hp_healed"] += player.hp - before
                heal_left -= 1
                t["companion_heals"] += 1
            if hp["main"] <= 0:
                died = False
                break

            # 3) the victim acts
            incoming = 0.0
            if action.startswith("attack") and victim_id == "benny" and cue != "music_stopped":
                incoming += RIDE_RECOIL                     # thrown off the ride
            if victim_id == "ned" and cue == "whistle":
                pass                                        # Ned rushes past on the train
            elif victim_id == "rosa" and cue == "camera_up":
                if stunned == 0 and not defending:
                    blind = BLIND_TURNS + 1                 # her flash blinds you (defending shields you)
            elif victim_id == "benny" and cue == "music_stopped":
                pass                                        # Benny stands still
            elif stunned > 0:
                pass                                        # Martha frozen in the light
            else:
                attackers = 2 if victim_id == "twins" else 1
                for _ in range(attackers):
                    if rng.random() < v["accuracy"] * (1 - policy.dodge):
                        damage = v["damage"] * (1.5 if rage > 0 else 1.0)
                        incoming += damage * (C.DEFEND_DAMAGE_FACTOR if defending else 1.0)
            incoming = min(incoming, max(player.hp, 0))
            player.hp -= incoming
            t["damage_taken"] += incoming
            stunned = max(0, stunned - 1)
            blind = max(0, blind - 1)
            rage = max(0, rage - 1)
            last_action = action
            if player.hp <= 0:
                break

        if not died:
            t["cleared"] = True
            player.consecutive_deaths = 0
            return t
        t["deaths"] += 1
        player.deaths_total += 1
        player.consecutive_deaths += 1
        if player.deaths_total >= C.MAX_DEATHS_PER_RUN:
            t["out_of_lives"] = True
            return t
        if policy.wants_to_quit(player.consecutive_deaths):
            t["quit"] = True
            return t
        player.hp = C.RESPAWN_HP
