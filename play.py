"""
Play Hollowmere yourself in the terminal (no graphics yet).

  python play.py                     # fixed director
  python play.py --controller random

Your telemetry is saved to data/human_runs.csv under a random anonymous ID,
so the same file format can be used later for the small playtest.

Note: in this text version your aim (accuracy) is fixed and hits are dice rolls.
Your skill shows in WHEN you defend and WHEN you drink potions. The pygame version
(week 5) adds a timing bar so your aim counts too.
"""
import argparse
import random
import uuid
from pathlib import Path

import pandas as pd

from game import config as C
from game.controllers import CONTROLLERS
from game.engine import play_run
from game.story import Story

WALT_LINES = {
    "stay_back": "Walt: 'You've got this. I'll keep watch.'",
    "hint": "Walt: 'Watch the big ones, they glow before they swing. Duck when they glow.'",
    "heal": "Walt: 'You're hurt. Hold still, kid.' (he opens a first-aid kit)",
    "fight": "Walt: 'Stay behind me.' (he pulls out his wrench)",
}


class HumanPolicy:
    accuracy = 0.75
    dodge = 0.10

    def choose_action(self, view, rng):
        enemies = ", ".join(f"{k} ({max(hp, 0):.0f} HP)" for k, hp in view["enemies"])
        print(f"\n  You: {view['hp']:.0f}/{view['max_hp']} HP, potions: {view['potions']}"
              f"   |   Ghosts: {enemies}")
        if view["wind_up"]:
            if view["warning"]:
                print("  Walt: 'It's glowing, DEFEND!'")
            else:
                print("  Something is glowing brighter and brighter...")
        while True:
            choice = input("  [a]ttack  [d]efend  [p]otion > ").strip().lower()
            if choice in ("a", "d", "p"):
                return {"a": "attack", "d": "defend", "p": "potion"}[choice]

    def wants_to_quit(self, consecutive_deaths):
        print("\n  Everything goes dark...")
        return input("  Try this attraction again? [y/n] > ").strip().lower() == "n"

    def end_of_room(self, room_index):
        pass


class NarratingController:
    """Wraps any director so the human sees the story text before each room."""

    def __init__(self, inner, story):
        self.inner, self.story = inner, story
        self.last_mode = None

    def decide(self, state):
        d = self.inner.decide(state)
        beat = self.story.by_id.get(d.get("beat_id"))
        if beat:
            zone = C.ZONE_NAMES[state["zone"]]
            print(f"\n=== Room {state['room_index'] + 1}/{C.ROOMS_PER_RUN} | {zone}: {beat['title']} ===")
            print(beat["text"])
            mode = d.get("help_mode")
            if not state["is_finale"] and mode != self.last_mode:
                print(WALT_LINES.get(mode, ""))   # Walt only speaks when his behaviour changes
                self.last_mode = mode
        return d

    def observe(self, state, decision, row):
        print(f"\n  Result: {'cleared' if row['cleared'] else 'not cleared'}, "
              f"deaths {row['deaths']}, HP lost {row['hp_lost_ratio']:.0%} -> {row['band']}")
        self.inner.observe(state, decision, row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controller", default="fixed", choices=list(CONTROLLERS))
    ap.add_argument("--out", default="data/human_runs.csv")
    args = ap.parse_args()

    story = Story()
    seed = random.randrange(10**6)
    player_id = uuid.uuid4().hex[:6]  # anonymous, not linked to any name
    print("Midnight. You wake up inside Hollowmere Park. The gates are locked.")
    print("An old mechanic with a flashlight finds you. 'Name's Walt. Stick with me, I know the way out.'")

    controller = NarratingController(CONTROLLERS[args.controller](rng=random.Random(seed)), story)
    rows = play_run(controller, HumanPolicy(), story, seed)

    outcome = rows[-1]["run_outcome"]
    if outcome == "escaped":
        print("\nThe gate creaks open. Dawn. Walt fades into the light. 'Not bad. Not bad at all.'")
    elif outcome == "out_of_lives":
        print("\nThe lights go out. Tomorrow, the photo booth prints a new picture: you, with the 1987 staff.")
    else:
        print("\nYou stop walking. The park keeps you.")

    for r in rows:
        r.update({"run_id": f"human-{player_id}-{seed}", "controller": args.controller,
                  "bot_type": "human", "player_id": player_id})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
    print(f"Telemetry saved to {out}")


if __name__ == "__main__":
    main()
