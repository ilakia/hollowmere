"""
Study 2 activities: six short challenges that replace some of the normal fights (two per night). They give
the three Walts more decisions to make, and the decisions differ from the fights:

  before an activity:  Walt's brain chooses the DIFFICULTY (easy / normal / hard) and HOW he helps
                       (each activity has its own ways to help, plus "stay_back")
  during an activity:  at two checkpoints (after a third and two thirds of the goal) he may STEP IN and
                       change the difficulty and/or his help

In the fights, LLM Walt gets the band model's predictions (Study 1's llm_risk). For activities there is no
prediction model, so here the LLM decides on its own judgement. That makes the comparison interesting:
does the LLM decide better with numbers (fights) or without (activities)?

How an activity works (the same for bots and, later, for the game window):
  - The player makes attempts ("steps"). Each step is a success or a mistake.
  - goal successes win the activity. Each mistake costs HP and uses one unit of the fail budget.
  - When the budget is used up, the activity is lost (extra HP lost, the night goes on; an activity never
    kills: HP stays at least 1).
  - pressure = mistakes counted / budget (0 = flawless, 1 = failed).
  - Band (same idea as the fights' rule): "in band" = won with pressure between 0.30 and 0.70;
    below 0.30 too easy, failed or above 0.70 too hard.

Bots: the chance of a successful step comes from the bot's hidden skill (accuracy and attention, the same
values as in the fights) plus the difficulty and help modifiers. These modifiers are design choices (set
before any test) and are checked with activity_check.py. The game window will later turn the same
difficulty and help settings into real mini-game settings (beam size, speed, timer ...).
"""
from . import config as C

ACTIVITY_LOW, ACTIVITY_HIGH = 0.30, 0.70      # the band for activities (pressure), like the fights' 30-70%
FAILED_PENALTY = 10                           # extra HP lost when the fail budget runs out
MAX_STEPS = 60                                # safety cap
DIFFICULTY_STEPS = ["easy", "normal", "hard"]

# Difficulty: p = change of the success chance per step, damage = HP per mistake (multiplier)
STANDARD_DIFFICULTY = {"easy": {"p": 0.12, "damage": 0.75}, "normal": {"p": 0.0, "damage": 1.0},
                       "hard": {"p": -0.12, "damage": 1.25}}

# Help effects (all optional): p = success chance bonus, forgive = mistakes per segment that do not count,
# damage = HP multiplier, assist = chance per step that Walt adds a success himself, goal = extra
# successes needed (slower but safer), after_mistake = the p bonus only starts after a mistake in the
# segment (help "when asked"), later = p bonus only from the second segment on (Walt needs time).
ACTIVITIES = {
    "act_flashlight": {
        "night": "A", "zone": 3, "title": "Flashlight Search", "goal": 6, "budget": 8, "damage": 6,
        "what": "The lights of the dark ride go out. The player moves Walt's flashlight beam to find the "
                "markers that lead to the exit before the darkness meter fills; ghosts grab them in the dark.",
        "help": {"stay_back": {},
                 "point": {"p": 0.15},
                 "hold_light": {"p": 0.07, "forgive": 1}},
        "help_text": {"stay_back": "you stay back", "point": "you point the way to the next marker",
                      "hold_light": "you hold the light steady (a bigger beam, the first slip in each part is forgiven)"},
        "words": {"point": ["point", "show you", "this way", "over there", "left", "right", "guide", "lead you"],
                  "hold_light": ["light", "beam", "lamp", "torch", "hold"]},
    },
    "act_whack": {
        "night": "A", "zone": 1, "title": "Whack-a-Ghost", "goal": 8, "budget": 7, "damage": 4,
        "what": "Little ghosts pop out of holes at the midway game; the player must hit them before they vanish.",
        "help": {"stay_back": {},
                 "call_out": {"p": 0.15},
                 "slow_down": {"p": 0.08, "damage": 0.6}},
        "help_text": {"stay_back": "you stay back", "call_out": "you call out which hole is next",
                      "slow_down": "you hold your lantern up, which slows them down and makes their bites weaker"},
        "words": {"call_out": ["call", "shout", "tell you", "which hole", "next one"],
                  "slow_down": ["slow", "lantern", "light", "hold them"]},
    },
    "act_lake": {
        "night": "B", "zone": 5, "title": "Lake Crossing", "goal": 7, "budget": 7, "damage": 5,
        "what": "The player steers a swan boat between three lanes through fog, dodging wrecks and drowned hands that reach up to grab the boat.",
        "help": {"stay_back": {},
                 "steer": {"forgive": 1},
                 "warn": {"p": 0.12},
                 "row_with_you": {"p": 0.20, "goal": 2}},
        "help_text": {"stay_back": "you stay back", "steer": "you steer (the first slip in each part is forgiven)",
                      "warn": "you shout which lane is clear before things come out of the fog",
                      "row_with_you": "you row too: everything comes slower, much safer, but the crossing takes longer"},
        "words": {"steer": ["steer", "rudder", "course", "keep us"], "warn": ["warn", "watch", "shout", "look out", "tell you"],
                  "row_with_you": ["row", "oar", "paddle", "together", "with you"]},
    },
    "act_mirror": {
        "night": "B", "zone": 5, "title": "Mirror Maze", "goal": 6, "budget": 6, "damage": 5,
        "what": "The player picks doors in Lily's mirror maze; reflections show fake doors (the real ones show "
                "Lily's red ribbon). A wrong door means bumping into glass.",
        "help": {"stay_back": {},
                 "mark_fakes": {"p": 0.25, "later": True},
                 "ribbon_hint": {"p": 0.12}},
        "help_text": {"stay_back": "you stay back", "mark_fakes": "you mark the fake doors (needs a moment: only after the first part)",
                      "ribbon_hint": "you remind them to look for the ribbon"},
        "words": {"mark_fakes": ["mark", "fake", "chalk", "scratch", "wrong door"],
                  "ribbon_hint": ["ribbon", "red", "look for"]},
    },
    "act_smoke": {
        "night": "C", "zone": 6, "title": "Smoke Escape", "goal": 5, "budget": 6, "damage": 7,
        "what": "A burning street with forks. The player chooses left or right before the smoke timer runs out; "
                "the clues are the colour of the smoke and the heat.",
        "help": {"stay_back": {},
                 "shout_way": {"p": 0.20},
                 "when_asked": {"p": 0.22, "after_mistake": True}},
        "help_text": {"stay_back": "you stay back", "shout_way": "you shout the way at every fork",
                      "when_asked": "you only help after they go wrong (when they ask)"},
        "words": {"shout_way": ["shout", "way", "left", "right", "follow", "this way"],
                  "when_asked": ["ask", "call me", "need me", "if you"]},
    },
    "act_bucket": {
        "night": "C", "zone": 6, "title": "Bucket Brigade", "goal": 7, "budget": 7, "damage": 5,
        "what": "The player fills a bucket and throws it at the spreading fires in time.",
        "help": {"stay_back": {},
                 "throw_too": {"assist": 0.35},
                 "point_fire": {"p": 0.12}},
        "help_text": {"stay_back": "you stay back", "throw_too": "you throw buckets too",
                      "point_fire": "you point at the biggest fire"},
        "words": {"throw_too": ["throw", "bucket", "water", "with you", "together", "douse"],
                  "point_fire": ["point", "biggest", "that one", "over there", "fire"]},
    },
}
for _a in ACTIVITIES.values():
    _a["words"]["stay_back"] = ["stay back", "hang back", "on your own", "all yours", "your turn", "let you",
                                "watch"]

NIGHTS_WITH_ACTIVITIES = {
    "A": ["z1_cotton_candy", "martha", "act_flashlight", "z2_tilted_room", "ned", "act_whack", "finale_gate"],
    "B": ["z1_ring_toss", "rosa", "act_lake", "z2_tilted_room", "twins", "act_mirror", "finale_gate"],
    "C": ["benny", "z1_ticket_booth", "henry", "act_smoke", "z3_tunnel_boats", "act_bucket", "finale_gate"],
}
HELP_ORDER = {a: list(spec["help"]) for a, spec in ACTIVITIES.items()}   # stay_back first, strongest last


def bot_skill(policy):
    """A bot's hidden skill for activities: half aim (accuracy), half attention (defend_skill), the same
    values it uses in fights. Output: about 0.33 (beginner), 0.60 (average), 0.87 (expert)."""
    return 0.5 * policy.accuracy + 0.5 * policy.defend_skill


def step_chance(skill, spec, difficulty, help_mode, segment, mistake_in_segment):
    """Chance that one step succeeds. Base 0.30 + 0.60 x skill, then the difficulty and help modifiers."""
    help_spec = spec["help"][help_mode]
    p = 0.30 + 0.60 * skill + STANDARD_DIFFICULTY[difficulty]["p"]
    bonus = help_spec.get("p", 0.0)
    if help_spec.get("after_mistake") and not mistake_in_segment:
        bonus = 0.0
    if help_spec.get("later") and segment == 0:
        bonus = 0.0
    return min(0.95, max(0.05, p + bonus))


def play_activity(player, activity_id, difficulty, help_mode, policy, rng, coach=None):
    """Play one activity. Changes player.hp in place. coach (optional) = Walt's brain for this activity:
    coach.step_in(view) at each checkpoint may return {"difficulty", "help", "say"} to change his settings.
    The policy answers each step: policy.activity_step(view, rng) -> True/False if it has that method
    (the game window), otherwise the bot model above.
    Output: telemetry dict with the same keys as a fight room plus the activity measures."""
    spec = ACTIVITIES[activity_id]
    goal = spec["goal"] + spec["help"][help_mode].get("goal", 0)
    t = {"hp_start": player.hp, "turns": 0, "hits": 0, "misses": 0, "damage_taken": 0.0, "hp_healed": 0.0,
         "potions_used": 0, "companion_heals": 0, "defends": 0, "defends_on_windup": 0, "windups_seen": 0,
         "deaths": 0, "quit": False, "out_of_lives": False,
         "activity": activity_id, "start_difficulty": difficulty, "start_help": help_mode,
         "step_ins": 0, "step_in_log": "", "forgiven": 0, "walt_assists": 0}
    progress, mistakes, segment, mistake_in_segment, forgiven_in_segment = 0, 0, 0, False, 0
    skill = bot_skill(policy) if not hasattr(policy, "activity_step") else None
    for _ in range(MAX_STEPS):
        t["turns"] += 1
        view = {"activity": activity_id, "difficulty": difficulty, "help": help_mode, "progress": progress,
                "goal": goal, "mistakes": mistakes, "budget": spec["budget"], "segment": segment,
                "hp": player.hp, "max_hp": C.PLAYER_MAX_HP}
        if skill is None:
            success = policy.activity_step(view, rng)
        else:
            success = rng.random() < step_chance(skill, spec, difficulty, help_mode, segment, mistake_in_segment)
        help_spec = spec["help"][help_mode]
        if not success and help_spec.get("assist") and rng.random() < help_spec["assist"]:
            success = True                                     # Walt's bucket lands instead
            t["walt_assists"] += 1
        if success:
            progress += 1
            t["hits"] += 1
        else:
            t["misses"] += 1
            mistake_in_segment = True
            if forgiven_in_segment < help_spec.get("forgive", 0):
                forgiven_in_segment += 1                       # Walt catches this slip
                t["forgiven"] += 1
            else:
                mistakes += 1
                damage = spec["damage"] * STANDARD_DIFFICULTY[difficulty]["damage"] * help_spec.get("damage", 1.0)
                damage = min(damage, player.hp - 1)            # an activity never kills
                player.hp -= damage
                t["damage_taken"] += damage
        if progress >= goal or mistakes >= spec["budget"]:
            break
        late = coach.pending() if coach is not None and hasattr(coach, "pending") else None
        if late:                                               # a background answer (game window) arrived
            old = (difficulty, help_mode)
            difficulty = late["difficulty"] if late.get("difficulty") in STANDARD_DIFFICULTY else difficulty
            help_mode = late["help"] if late.get("help") in spec["help"] else help_mode
            if (difficulty, help_mode) != old:
                t["step_ins"] += 1
                t["step_in_log"] += f"{progress}:{old[0]}/{old[1]}->{difficulty}/{help_mode};"
            if late.get("say") and hasattr(policy, "walt_says"):
                policy.walt_says(late["say"])
        new_segment = min(2, progress * 3 // goal)             # checkpoints after 1/3 and 2/3 of the goal
        if new_segment > segment:
            segment, mistake_in_segment, forgiven_in_segment = new_segment, False, 0
            if coach is not None:
                change = coach.step_in(dict(view, progress=progress, mistakes=mistakes, segment=segment,
                                            hp=player.hp, difficulty=difficulty, help=help_mode))
                if change:
                    old = (difficulty, help_mode)
                    if change.get("difficulty") in STANDARD_DIFFICULTY:
                        difficulty = change["difficulty"]
                    if change.get("help") in spec["help"]:
                        help_mode = change["help"]
                    if (difficulty, help_mode) != old:
                        t["step_ins"] += 1
                        t["step_in_log"] += f"{progress}:{old[0]}/{old[1]}->{difficulty}/{help_mode};"
                    if change.get("say") and hasattr(policy, "walt_says"):
                        policy.walt_says(change["say"])
    won = progress >= goal
    if not won:
        penalty = min(FAILED_PENALTY, player.hp - 1)
        player.hp -= penalty
        t["damage_taken"] += penalty
    pressure = min(1.0, mistakes / spec["budget"])
    t.update({"cleared": won, "progress": progress, "goal": goal, "mistakes": mistakes, "pressure": round(pressure, 4),
              "end_difficulty": difficulty, "end_help": help_mode})
    return t


def activity_band(t):
    """The activity's band: too_easy / in_band / too_hard (see the module text)."""
    if not t["cleared"] or t["pressure"] > ACTIVITY_HIGH:
        return "too_hard"
    if t["pressure"] < ACTIVITY_LOW:
        return "too_easy"
    return "in_band"
