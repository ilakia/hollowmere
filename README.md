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
python build_tables.py                      # expected-HP-loss table for the skill estimator
python compare_directors.py --controllers fixed random rule  # rule director vs baselines
python failure_predictor.py                 # failure predictor (trained on random-director data)
python bandit_experiment.py                 # train + test the bandit, draws the learning curve
python play.py --controller rule            # play it yourself in the terminal (fixed, random, rule, bandit)
python play_window.py --controller rule     # play it in a game window (pygame)
python robustness_experiment.py --games 300 # held-out bot type and +/-20% sensitivity check

# LLM directors need Ollama: brew install ollama && brew services start ollama && ollama pull llama3.2:3b
python llm_experiment.py --games 25 --batch 2 --pause 180                     # plain LLM director
python llm_experiment.py --controller llm_risk --games 25 --batch 2 --pause 180   # LLM + predicted risks
```

## Files

| File | What it does |
|---|---|
| `game/config.py` | Every number in the game (HP, damage, difficulty, companion, **target band**) |
| `game/story_beats.json` | The 19 attractions in 3 zones + the finale, with `requires` links and clue flags |
| `game/story.py` | Loads the attractions, checks them for mistakes, lists which are valid next |
| `game/engine.py` | The rules: one room (`play_room`), one full run (`play_run`), the band check, decision validation |
| `game/bots.py` | Simulated players: beginner, average, expert, rage_quitter (random settings inside a range) |
| `game/controllers.py` | Directors: `fixed` (baseline), `random` (unbiased training data), `rule` (if-else on the skill estimate), `bandit` (LinUCB), `llm` (local language model), `llm_risk` (LLM + predicted risk per option), `predictor` (top predicted option, no LLM) |
| `game/llm.py` | LLM prompts, Ollama call (temperature 0, fixed seed), answer cache `data/llm_cache.json` |
| `game/risk.py` | Shared feature description of a situation + option; the band model used by `llm_risk` and `predictor` |
| `game/skill.py` | Skill estimator: weighted moving average of HP lost compared with an average player in the same situation |
| `game/expected_hp_lost.csv` | "Average player" table per attraction × difficulty × Walt mode (made by `build_tables.py`) |
| `game/bandit.py` | LinUCB contextual bandit: 12 arms (difficulty × Walt mode) + 3 finale arms |
| `simulate.py` | Bots play many runs, one CSV row per room |
| `sanity_check.py` | Determinism check, skill-ordering check, summary table |
| `build_tables.py` | Builds `game/expected_hp_lost.csv` from random-director data |
| `compare_directors.py` | Directors on the same bots and dice rolls (paired comparison) |
| `failure_predictor.py` | Predicts room failure before it is played (logistic regression vs gradient boosting) |
| `bandit_experiment.py` | Trains the bandit, chooses its exploration strength, tests it, plots `figures/bandit_learning_curve.png` |
| `llm_experiment.py` | LLM directors vs the others on the same seeds, in batches with cooling pauses |
| `robustness_experiment.py` | Held-out bot type (re-learn without one type, test on it) and +/-20% changes to the game |
| `play.py` | Human play in the terminal, telemetry saved under an anonymous ID |
| `play_window.py` | Human play in a pygame window (same engine and telemetry); `--demo` plays by itself for testing |

**Seeds:** 0–1999 training (tables, tuning, bandit learning), 50000+ validation (bandit exploration strength), 100000–100999 final director test, 200000+ failure-predictor test. Nothing was tuned on test seeds.

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
- **Skill estimate = weighted moving average (α = 0.3) of HP lost compared with an average player in the same room, difficulty and Walt mode, instead of raw HP lost, hit rate or a whole-run average**, because comparing with the same situation doubled how well it predicts the next room (0.20 → 0.42 rank correlation), hit rate would silently fail for humans (aim is fixed in the text version), and a whole-run average cannot follow a player who improves (bots do not learn yet, which flatters long windows).
- **Rule director never uses `hard`**, because hard difficulty + high-threat room + no help overshot in tuning (experts escaped only 79% of runs); normal difficulty with a harder room and Walt staying back worked better.
- **Bandit reward = 1 if the room is in band, else 0, instead of partial credit or an extra penalty for too hard**, because it is exactly the measure every director is graded on, so the reward cannot favour the bandit.
- **Bandit arms = difficulty × Walt mode (12) + difficulty only in the finale (3), room picked by threat to match the difficulty, instead of every room × difficulty × mode (~228)**, because there would be far too little data per arm.
- **Logistic regression kept as the main failure predictor instead of gradient boosting**, because both reach the same AUC (0.93) and the simpler model is easier to explain.
- **LSTM predictor cut** (first item on the cut list): gradient boosting already added nothing over a straight-line model, so a sequence model was very unlikely to change the conclusion, and it would have needed PyTorch.
- **LLM answers made repeatable (temperature 0, fixed seed, cache) instead of sampling**, so every experiment can be re-run with identical results and without new model work.
- **Game window drawn with simple shapes in code instead of downloaded sprites**, so there are no image files or licence questions. Charge-ups are shown by an orange glow, shaking and a "!" for everyone; Walt's "DEFEND!" bubble and the flashing Defend button only appear in `hint` mode, otherwise the window would give every player the hint for free.
- **No extra "guard" help mode (Walt fights only when the player's HP is low) instead of a 5th mode**, because `fight` already works as a rescue (beginner deaths per room 0.21 with `stay_back` vs 0.04 with `fight`, random director, 500 runs per bot type), the main balance problem is rooms being *too easy*, not too hard, and an automatic in-room rescue would do part of the director's job for it, which blurs the comparison between directors. A 5th mode would also grow the bandit's choices from 12 to 15. Walt can still be *shown* stepping in during `fight`/`heal` in the pygame panel.

## Current balance (fixed director, 500 runs per bot type, 19 Oct, after balancing)

| Bot | Escaped | Too easy | In band | Too hard | Finale close win |
|---|---|---|---|---|---|
| beginner | 53% | 19% | 53% | 28% | 21% |
| average | 98% | 33% | 61% | 6% | 71% |
| expert | 100% | 51% | 49% | 0% | 91% |

Balancing changes (19 Oct): wisp HP 14 → 20, rest heal 40 → 60, Walt's lantern blast 22 → 18 (reasons in `game/config.py` and the problem log). Every bot type now has rooms on both sides of the band, so an adaptive director has room to improve. Experts are still too easy in half the rooms on `normal`, which a director can fix by choosing `hard`.

## Results so far (test seeds 100000–100999, 1000 runs per bot type, bots only)

Share of rooms in band:

| Bot | fixed | random | rule | bandit |
|---|---|---|---|---|
| beginner | 53% | 44% | 57% | 72% |
| rage_quitter | 59% | 47% | 66% | 77% |
| average | 61% | 47% | 69% | 77% |
| expert | 49% | 39% | 63% | 77% |
| **all** | **55.6%** | **44.2%** | **64.0%** | **75.7%** |

- Beginners escape 51% (fixed), 80% (rule), 97% (bandit) of runs.
- **About half of the bandit's gain comes from Walt's `heal` mode** (94% of its training choices). A non-adaptive director that always uses normal + heal already reaches 66.9%, more than the rule director. The rest (66.9% → 75.7%) is real adaptation: hard + heal for strong players, normal + heal for the others.
- The bandit learns fast: about 62% in its first 50 training runs, above the rule director after ~100 runs, ~77% by 8,000 runs (`figures/bandit_learning_curve.png`).
- Failure predictor (new seeds): AUC 0.93 on random-director games, 0.84 on rule-director games, well calibrated (predicted 12.0% vs actual 11.8% failures). Expected HP loss of the chosen room is by far the strongest input; the skill estimate is second.

### LLM directors (test seeds 100000–100024, 25 runs per bot type)

The LLM test is smaller because the language model overheats the laptop (decided before any test result was seen). All directors play exactly the same 100 runs.

| Bot | fixed | rule | bandit | llm | llm_risk | predictor |
|---|---|---|---|---|---|---|
| beginner | 48% | 53% | 73% | 37% | 71% | 72% |
| rage_quitter | 56% | 67% | 80% | 38% | 75% | 82% |
| average | 60% | 65% | 75% | 42% | 81% | 82% |
| expert | 53% | 64% | 78% | 42% | 79% | 79% |
| **all** | **54.3%** | **62.2%** | **76.4%** | **39.9%** | **76.5%** | **78.5%** |
| beginners escaping | 52% | 76% | 100% | 8% | 72% | 96% |

- **Plain LLM (`llm`, llama3.2 3B): worst director, below random.** 0% invalid answers and 0 crashes, but it follows story logic instead of the goal: easy rooms early, hard later, always a hard finale ("Walt's final challenge"), never `heal`, and the same choices for every player type.
- **`llm_risk`** (the LLM gets the 6 options with the highest predicted in-band chance, with numbers) ties the bandit (76.5% vs 76.4%). The prompt was developed on training seeds 1500–1524; one fix was needed there (the model chose "hard" in the finale for drama even when the numbers said 90% too hard).
- **`predictor`** (same numbers, always option 1, no LLM) is the best director: 78.5% (also 78.5% on 1000 runs per bot type), beginners escape 96%. So the gain comes from the prediction model, and the LLM's own choices slightly lower the result. This ablation was added after the LLM test.


### Robustness (test seeds 100000+, 300 runs per bot type per condition, no LLM)

**Held-out bot type** (table, band model and bandit re-learned without that type, tested only on it; rule thresholds were tuned on all types):

| Unseen type | fixed | rule | bandit | predictor |
|---|---|---|---|---|
| beginner | 52.8% | 57.3% | 70.7% | 73.5% |
| rage_quitter | 58.5% | 64.5% | 76.6% | 79.7% |
| average | 61.8% | 68.0% | 74.1% | 83.2% |
| expert | 48.5% | 63.3% | 62.4% | 72.7% |

**+/-20% game changes at test time** (directors keep what they learned on the original game; all bot types):

| Condition | fixed | rule | bandit | predictor |
|---|---|---|---|---|
| original | 55.4% | 63.3% | 75.2% | 79.0% |
| ghost damage x0.8 | 48.0% | 57.7% | 71.5% | 75.7% |
| ghost damage x1.2 | 54.2% | 58.5% | 70.9% | 76.1% |
| ghost HP x0.8 | 50.0% | 51.4% | 69.6% | 75.0% |
| ghost HP x1.2 | 54.8% | 62.7% | 76.3% | 80.3% |
| rest heal x0.8 | 55.0% | 63.2% | 74.9% | 78.7% |
| rest heal x1.2 | 55.3% | 63.4% | 75.4% | 78.9% |

- The order predictor > bandit > rule > fixed holds in all 7 game conditions and for 3 of 4 unseen bot types. The one exception: a bandit that never met experts falls to 62.4% on them, slightly below the rule director (63.3%); the predictor stays at 72.7%.
- Weaker ghosts (HP or damage x0.8) hurt every director most, because more rooms become too easy; rest healing hardly matters.

- All results come from simulated bots. The bots model players, they are not real players.
