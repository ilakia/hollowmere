"""
Headless game engine: rules and numbers only, no graphics.

- A "room" is one turn-based fight inside one attraction.
- A "run" is ROOMS_PER_RUN rooms in a row, chosen one by one by a director (controller).
  The last room is always the finale against Walt.
- A "policy" is whatever plays the game: a bot or a human. It must provide
  .accuracy, .dodge, choose_action(view, rng), wants_to_quit(consecutive_deaths)
  and end_of_room(room_index) (bots use the last one to improve with practice).

Each turn: player acts -> companion acts -> every living ghost acts.
"""
import random
from dataclasses import dataclass

from . import config as C


# ---------------------------------------------------------------- ghosts
@dataclass
class Enemy:
    kind: str
    hp: float
    damage: float
    accuracy: float
    attack_every: int
    special_every: int = 0      # 0 = no charged attack
    special_damage: float = 0.0
    turn_counter: int = 0

    @property
    def alive(self):
        return self.hp > 0

    def _is_special(self, n):
        return self.special_every > 0 and n % self.special_every == 0

    def winding_up(self):
        """True if this ghost is charging, i.e. it strikes hard on its next turn."""
        n = self.turn_counter + 1
        return self._is_special(n) or (self.attack_every > 1 and n % self.attack_every == 0)

    def act(self):
        """Advance one turn. Returns the damage of this turn's attack, or None if it waits."""
        self.turn_counter += 1
        n = self.turn_counter
        if self._is_special(n):
            return self.special_damage
        if n % self.attack_every != 0:
            return None  # still charging
        return self.damage


def make_enemies(beat, difficulty):
    mult = C.DIFFICULTY[difficulty]
    enemies = []
    for kind in beat["enemies"]:
        base = C.ENEMY_TYPES[kind]
        enemies.append(Enemy(kind=kind,
                             hp=base["hp"] * mult["hp_mult"],
                             damage=base["damage"] * mult["damage_mult"],
                             accuracy=base["accuracy"],
                             attack_every=base["attack_every"],
                             special_every=base.get("special_every", 0),
                             special_damage=base.get("special_damage", 0) * mult["damage_mult"]))
    return enemies


# ---------------------------------------------------------------- player
@dataclass
class PlayerState:
    """Everything that carries over from one room to the next inside a run."""
    hp: float = C.PLAYER_MAX_HP
    potions: int = C.POTIONS_PER_RUN
    deaths_total: int = 0
    consecutive_deaths: int = 0


# ---------------------------------------------------------------- one room
def play_room(player, beat, difficulty, help_mode, policy, rng):
    """Play one room until it is cleared, the player quits, or the run is out of lives.
    Changes `player` in place and returns the telemetry of this room as a dict."""
    t = {"hp_start": player.hp, "turns": 0, "hits": 0, "misses": 0,
         "damage_taken": 0.0, "potions_used": 0, "companion_heals": 0,
         "defends": 0, "defends_on_windup": 0, "windups_seen": 0,
         "deaths": 0, "cleared": False, "quit": False, "out_of_lives": False}

    while True:  # each loop is one attempt at the room
        enemies = make_enemies(beat, difficulty)
        heal_left = 1 if help_mode == "heal" else 0
        died = True  # becomes False only if the room is cleared

        for turn in range(C.MAX_TURNS_PER_ATTEMPT):
            t["turns"] += 1
            alive = [e for e in enemies if e.alive]
            hint_active = help_mode == "hint" and turn < C.HINT_TURNS
            wind_up = any(e.winding_up() for e in alive)
            t["windups_seen"] += wind_up

            # 1) player decides, based only on what a player could see on screen
            view = {
                "hp": player.hp,
                "max_hp": C.PLAYER_MAX_HP,
                "potions": player.potions,
                "enemies": [(e.kind, e.hp) for e in alive],
                "wind_up": wind_up,
                "warning": help_mode == "hint",   # Walt shouts when a charged hit is coming
                "hint_active": hint_active,
            }
            action = policy.choose_action(view, rng)

            defending = False
            if action == "potion" and player.potions > 0:
                player.potions -= 1
                t["potions_used"] += 1
                player.hp = min(C.PLAYER_MAX_HP, player.hp + C.POTION_HEAL)
            elif action == "defend":
                defending = True
                t["defends"] += 1
                t["defends_on_windup"] += wind_up
            else:  # attack the first living ghost (also the fallback for invalid input)
                hit_chance = policy.accuracy + (C.HINT_ACCURACY_BONUS if hint_active else 0.0)
                if rng.random() < min(hit_chance, C.MAX_HIT_CHANCE):
                    alive[0].hp -= C.PLAYER_ATTACK
                    t["hits"] += 1
                else:
                    t["misses"] += 1

            # 2) companion acts
            alive = [e for e in enemies if e.alive]
            if help_mode == "fight" and alive and rng.random() < C.COMPANION_ACCURACY:
                alive[0].hp -= C.COMPANION_DAMAGE
            if heal_left and player.hp < C.COMPANION_HEAL_TRIGGER * C.PLAYER_MAX_HP:
                player.hp = min(C.PLAYER_MAX_HP, player.hp + C.COMPANION_HEAL)
                heal_left -= 1
                t["companion_heals"] += 1

            alive = [e for e in enemies if e.alive]
            if not alive:
                died = False
                break

            # 3) ghosts act
            for e in alive:
                dmg = e.act()
                if dmg is None:
                    continue
                if rng.random() < e.accuracy * (1 - policy.dodge):
                    dmg = dmg * (C.DEFEND_DAMAGE_FACTOR if defending else 1.0)
                    dmg = min(dmg, max(player.hp, 0))  # count only damage actually taken
                    player.hp -= dmg
                    t["damage_taken"] += dmg
            if player.hp <= 0:
                break
        # (if the turn cap is reached, `died` is still True: it counts as a failed attempt)

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
        player.hp = C.RESPAWN_HP  # respawn and retry the same room


def band_position(t):
    """Where did this room land relative to the frozen target band?"""
    if not t["cleared"] or t["deaths"] > 0:
        return "too_hard"
    lost = t["damage_taken"] / t["hp_start"]
    if lost < C.BAND_LOW:
        return "too_easy"
    if lost > C.BAND_HIGH:
        return "too_hard"
    return "in_band"


# ---------------------------------------------------------------- director decision
def validate_decision(decision, valid_beats, is_finale):
    """Directors (later: the LLM) may return nonsense. Replace invalid parts
    with safe defaults and report whether the decision was valid."""
    valid_ids = [b["id"] for b in valid_beats]
    ok = True
    d = dict(decision) if isinstance(decision, dict) else {}
    if d.get("beat_id") not in valid_ids:
        d["beat_id"], ok = valid_ids[0], False
    if d.get("difficulty") not in C.DIFFICULTY:
        d["difficulty"], ok = "normal", False
    if is_finale:
        d["help_mode"] = C.FINALE_HELP_MODE  # Walt is the enemy now, no help possible
    elif d.get("help_mode") not in C.HELP_MODES:
        d["help_mode"], ok = "stay_back", False
    return d, ok


# ---------------------------------------------------------------- one run
def play_run(controller, policy, story, seed):
    """Play a full run. Returns a list of telemetry rows, one per room played."""
    rng = random.Random(f"game-{seed}")
    player = PlayerState()
    used, history = [], []

    for room_index in range(C.ROOMS_PER_RUN):
        zone = C.ZONE_OF_ROOM[room_index]
        is_finale = room_index == C.ROOMS_PER_RUN - 1
        valid = story.valid_next(used, zone)
        state = {"room_index": room_index, "zone": zone, "is_finale": is_finale,
                 "valid_beats": valid, "history": history,
                 "hp": player.hp, "max_hp": C.PLAYER_MAX_HP,
                 "potions": player.potions, "deaths_total": player.deaths_total}

        raw = controller.decide(state)
        decision, decision_valid = validate_decision(raw, valid, is_finale)
        beat = story.get(decision["beat_id"])

        t = play_room(player, beat, decision["difficulty"], decision["help_mode"], policy, rng)
        used.append(beat["id"])

        row = {"seed": seed, "room_index": room_index, "zone": zone, "is_finale": is_finale,
               "beat_id": beat["id"], "beat_threat": beat["threat"], "clue": beat["clue"],
               "difficulty": decision["difficulty"], "help_mode": decision["help_mode"],
               "decision_valid": decision_valid,
               "propensity": decision.get("propensity"),
               **t,
               "hp_lost_ratio": round(t["damage_taken"] / t["hp_start"], 4),
               "band": band_position(t)}
        row["in_band"] = row["band"] == "in_band"
        history.append(row)
        controller.observe(state, decision, row)
        policy.end_of_room(room_index)

        if t["quit"] or t["out_of_lives"]:
            break
        player.hp = min(C.PLAYER_MAX_HP, player.hp + C.REST_HEAL)

    last = history[-1]
    outcome = "quit" if last["quit"] else "out_of_lives" if last["out_of_lives"] else "escaped"
    for r in history:
        r["run_outcome"] = outcome
        r["rooms_played"] = len(history)
    return history
