# Hollowmere (v0.2, theme park version)

Case study for *Emerging Technologies and AI*, HTW Berlin.
**Skill-Adaptive AI Companion and Storyline Director: Rule-Based, Bandit and LLM Control Compared**

You are trapped in Hollowmere Park at night. Walt, an old mechanic, guides you through 9 haunted attractions in 3 zones. Before each attraction, a "director" decides which attraction comes next, how hard it is, and how Walt helps. At the exit gate Walt reveals he is a ghost and fights you. This repo is the game the directors are tested in. Everything runs offline on your own laptop.

## Run it (Mac, Python 3.10+)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python sanity_check.py --games 500          # is the game working and balanced?
python simulate.py --games 1000 --controllers fixed random   # bot data -> data/sim_runs.csv
python play.py                              # play it yourself in the terminal
```

## Files

| File | What it does |
|---|---|
| `game/config.py` | Every number in the game (HP, damage, difficulty, companion, **target band**) |
| `game/story_beats.json` | The 19 attractions in 3 zones + the finale, with `requires` links and clue flags |
| `game/story.py` | Loads the attractions, checks them for mistakes, lists which are valid next |
| `game/engine.py` | The rules: one room (`play_room`), one full run (`play_run`), the band check, decision validation |
| `game/bots.py` | Simulated players: beginner, average, expert, rage_quitter (random settings inside a range) |
| `game/controllers.py` | Directors: `fixed` (baseline) and `random` (for unbiased training data). Rule, bandit and LLM come next |
| `simulate.py` | Bots play many runs, one CSV row per room |
| `sanity_check.py` | Determinism check, skill-ordering check, summary table |
| `play.py` | Human play in the terminal, telemetry saved under an anonymous ID |

## How the game works (numbers still being balanced)

- A run is 10 rooms: 3 attractions per zone, then the finale. Each room is a turn-based fight. Each turn: you act, Walt acts, ghosts act.
- You can **attack**, **defend** (halves damage that turn) or drink a **potion** (3 per run).
- Ghosts: wisp (weak, in groups), possessed animatronic (medium), wraith (glows one turn, then a big hit, so defending at the right time matters). Finale boss: Walt (wrench hits plus a charged lantern blast every 3rd turn).
- Dying restarts the room with 60 HP. The 3rd death ends the run. Between rooms you regain 40 HP.
- Walt's modes (not in the finale): `stay_back` (nothing), `hint` (+15% aim for 3 turns and warns about wind-ups), `heal` (+25 HP once when you drop below 50%), `fight` (small damage every turn).
- Difficulty tiers: `easy` (×0.75 enemy HP and damage), `normal`, `hard` (×1.3 HP, ×1.25 damage).

**Target band (frozen):** a room is *in band* if it was cleared without dying and the player lost 30 to 70% of the HP they entered with. Below 30% is *too easy*, a death or above 70% is *too hard*. This rule is fixed before any controller is built, so no controller can be "graded in its favour".

## Design decisions so far (X instead of Y because Z)

- **Own game instead of the NetHack dataset**, because recorded NetHack games cannot contain my director's decisions, so controllers would have to be tested in simulation either way, and NetHack would cost weeks of learning and data parsing.
- **Turn-based instead of real-time**, because bots and logging stay simple and every result can be reproduced from its seed.
- **Hint = small stat boost + warnings instead of text tips**, because bots cannot read text, so a text hint would have no measurable effect.
- **Bot settings sampled from ranges instead of 4 fixed bots**, to reduce simulator bias (thousands of slightly different players).
- **Same seed = same bot and same dice rolls for every controller**, so controllers are compared on identical players (paired comparison).
- **`true_*` columns are hidden skill**, logged only for analysis. They must never be used as model features.

## Current balance (fixed director, 500 runs per bot type, 19 Oct, NOT tuned yet)

| Bot | Escaped | Too easy | In band | Too hard | Finale close win |
|---|---|---|---|---|---|
| beginner | 43% | 40% | 33% | 27% | 4% |
| average | 95% | 58% | 29% | 13% | 27% |
| expert | 100% | 70% | 25% | 5% | 60% |

Zones 1 and 2 are currently too easy for everyone. Balancing is the next step.
