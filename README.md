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
- Dying restarts the room with 60 HP. The 3rd death ends the run. Between rooms you regain 60 HP.
- Walt's modes (not in the finale): `stay_back` (nothing), `hint` (+15% aim for 3 turns and warns about wind-ups), `heal` (+25 HP once when you drop below 50%), `fight` (small damage every turn).
- Difficulty tiers: `easy` (×0.75 enemy HP and damage), `normal`, `hard` (×1.3 HP, ×1.25 damage).

**Target band (frozen 19 Oct):** a room is *in band* if it was cleared without dying and the player lost 30 to 70% of all the HP they had in that room: the HP at the start plus any HP healed during the room (potions, Walt's heal), i.e. `damage_taken / (hp_start + hp_healed)`. Below 30% is *too easy*, a death or above 70% is *too hard*. This rule is fixed before any controller is built, so no controller can be "graded in its favour". It was changed once, on 19 Oct, before any director existed (see design decisions).

## Design decisions so far (X instead of Y because Z)

- **Own game instead of the NetHack dataset**, because recorded NetHack games cannot contain my director's decisions, so controllers would have to be tested in simulation either way, and NetHack would cost weeks of learning and data parsing.
- **Turn-based instead of real-time**, because bots and logging stay simple and every result can be reproduced from its seed.
- **Hint = small stat boost + warnings instead of text tips**, because bots cannot read text, so a text hint would have no measurable effect.
- **Bot settings sampled from ranges instead of 4 fixed bots**, to reduce simulator bias (thousands of slightly different players).
- **Same seed = same bot and same dice rolls for every controller**, so controllers are compared on identical players (paired comparison).
- **`true_*` columns are hidden skill**, logged only for analysis. They must never be used as model features.
- **Band measured against start HP + HP healed instead of start HP alone**, because the old rule counted healing as extra difficulty: healing lets the player survive longer and take more total damage, so `heal` mode looked harmful (beginner too-hard share 31% vs 27% for `stay_back`, although it halved deaths), and 1,112 of 17,212 rooms cleared without dying scored above 100%. A director learning from that number would wrongly learn "healing is bad". Net HP loss (start − end) was rejected because potions could hide a hard fight and the ratio could go below 0.
- **No extra "guard" help mode (Walt fights only when the player's HP is low) instead of a 5th mode**, because `fight` already works as a rescue (beginner deaths per room 0.21 with `stay_back` vs 0.04 with `fight`, random director, 500 runs per bot type), the main balance problem is rooms being *too easy*, not too hard, and an automatic in-room rescue would do part of the director's job for it, which blurs the comparison between directors. A 5th mode would also grow the bandit's choices from 12 to 15. Walt can still be *shown* stepping in during `fight`/`heal` in the pygame panel.

## Current balance (fixed director, 500 runs per bot type, 19 Oct, after balancing)

| Bot | Escaped | Too easy | In band | Too hard | Finale close win |
|---|---|---|---|---|---|
| beginner | 53% | 19% | 53% | 28% | 21% |
| average | 98% | 33% | 61% | 6% | 71% |
| expert | 100% | 51% | 49% | 0% | 91% |

Balancing changes (19 Oct): wisp HP 14 → 20, rest heal 40 → 60, Walt's lantern blast 22 → 18 (reasons in `game/config.py` and the problem log). Every bot type now has rooms on both sides of the band, so an adaptive director has room to improve. Experts are still too easy in half the rooms on `normal`, which a director can fix by choosing `hard`.
