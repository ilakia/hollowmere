"""
All game numbers live here. To rebalance the game, change this file only.
Every number is a design choice and should be justified in the write-up.
"""

# ---------- Player ----------
PLAYER_MAX_HP = 100
PLAYER_ATTACK = 15           # damage of one successful hit
POTIONS_PER_RUN = 3          # 3 instead of 2, because a run is now 10 rooms long
POTION_HEAL = 35
REST_HEAL = 40               # HP regained when walking to the next attraction
RESPAWN_HP = 60              # HP after dying (the attraction restarts)
MAX_DEATHS_PER_RUN = 3       # the 3rd death ends the run ("trapped forever")
MAX_TURNS_PER_ATTEMPT = 60   # safety cap, a room can never loop forever
DEFEND_DAMAGE_FACTOR = 0.5   # defending halves incoming damage for that turn
MAX_HIT_CHANCE = 0.95        # nobody hits 100% of the time

# ---------- Run structure ----------
ROOMS_PER_RUN = 10
ZONE_OF_ROOM = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4]   # zone 4 = the finale at the exit gate
ZONE_NAMES = {1: "Entrance & Midway", 2: "The Funhouse", 3: "The Dark Rides", 4: "The Exit Gate"}

# ---------- Ghosts ----------
# attack_every = 2: the ghost glows on one turn and strikes on the next.
# special_every / special_damage: a charged attack every N turns (only Walt has one).
# A good player defends whenever a ghost is charging ("wind-up").
ENEMY_TYPES = {
    "wisp":        {"hp": 14,  "damage": 3,  "accuracy": 0.80, "attack_every": 1},
    "animatronic": {"hp": 32,  "damage": 6,  "accuracy": 0.75, "attack_every": 1},
    "wraith":      {"hp": 50,  "damage": 16, "accuracy": 0.70, "attack_every": 2},
    "walt":        {"hp": 110, "damage": 6,  "accuracy": 0.75, "attack_every": 1,
                    "special_every": 3, "special_damage": 22},
}

# ---------- Difficulty lever (controlled by the director) ----------
DIFFICULTY = {
    "easy":   {"hp_mult": 0.75, "damage_mult": 0.75},
    "normal": {"hp_mult": 1.00, "damage_mult": 1.00},
    "hard":   {"hp_mult": 1.30, "damage_mult": 1.25},
}

# ---------- Companion lever (controlled by the director) ----------
HELP_MODES = ["stay_back", "hint", "heal", "fight"]
FINALE_HELP_MODE = "none"    # in the finale Walt is the enemy, so there is no help
HINT_ACCURACY_BONUS = 0.15   # hint: better aim for the first few turns ...
HINT_TURNS = 3
HINT_DEFEND_BOOST = 0.5      # ... and warns about charge-ups for the whole room
COMPANION_HEAL = 25          # heal: once per attempt, when player HP is low
COMPANION_HEAL_TRIGGER = 0.5 # "low" = below 50% of max HP
COMPANION_DAMAGE = 6         # fight: Walt swings his wrench every turn
COMPANION_ACCURACY = 0.7

# ---------- Target difficulty band (FROZEN, do not tune per controller) ----------
# A room is "in band" if the player cleared it without dying and lost
# between 30% and 70% of the HP they entered with.
# Less than 30% = too easy (boring). Death or more than 70% = too hard.
BAND_LOW = 0.30
BAND_HIGH = 0.70
