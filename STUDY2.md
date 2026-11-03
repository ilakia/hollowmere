# Study 2: Does an AI companion help players? (design draft)

Study 1 (done, frozen) asked **who should control difficulty** (rule, bandit, LLM, predictor) and was
answered with bots. Study 2 asks the question behind the "AI companion" in the title:

> **Does an LLM-driven companion (that decides how to help, tells the story, steps in and reacts) help
> players discover hidden mechanics and play better than a scripted or a silent companion, and do players
> enjoy it more?**

Study 2 runs in a **separate story mode** ("Night of the Fire"). The normal game, the engine rules used by
the bots and every Study 1 result stay exactly as they are.

## 1. The story mode in one paragraph

In 1987 a fire killed several people at Hollowmere Park. Their ghosts still haunt the attractions where
they worked. Each **victim ghost** has a name, a story and **one weakness** that comes from that story.
Fighting a victim the normal way works, but it is long and painful; using the weakness ends the fight
quickly. Walt knew every one of them, so the way he talks about them can contain the **clue**. The normal
ghosts (wisps, animatronics, wraiths) still appear in the other rooms; the finale is still Walt.

## 2. Six victim ghosts (2 per night, as built)

| Night | Victim | Who they were | Weakness (how to beat them fast) | Clue Walt can give | Tell on screen |
|---|---|---|---|---|---|
| A | **Martha Bell** | Ticket seller (Ticket Booth) | **Shine** the flashlight (new action, L): frozen for 2 turns, double damage | "Hated the dark... never once turned off the lamp at her booth." | Lights flicker |
| A | **Ned Carver** | Ghost-train engineer (Ghost Train) | **Attack while the train passes** (whistle): double damage; otherwise only glancing blows. The habit (defend on the whistle) gives nothing | "Never got off that train... only time you could reach him was when it came past, whistle blowing." | Whistle, train rushes past |
| B | **Rosa Lindqvist** | Photographer (Photo Booth) | **Shine into her lens** when she lifts the camera: her own flash blinds her (frozen, double damage). Otherwise her flash blinds you | "A camera's blind to everything but light. Kids shone a torch into her lens." | Camera goes up |
| B | **Lily Ward** (and her reflection) | Hall of Mirrors attendant | **Attack the real Lily** (red ribbon); hitting the reflection heals her, until the mirror cracks after 3 hits | "Never took off her mother's red ribbon. Her reflections never had it." | Two Lilys, one with a ribbon |
| C | **Benny Ortiz** | Carousel operator (Carousel) | **Wait (defend) while it spins, strike when the music stops**; attacking the spinning ride throws you off | "Only time Benny stood still was when the music box ran down." | Music stops, horses freeze |
| C | **Henry Pike** | Barker of Clown Alley | **Call his stage name** (new action, N; 3 choices): "The Great Henry" calms him and ends the fight | "Only way to calm him down was to call him by his stage name: The Great Henry." | He shouts "Who am I?!" |

Balance check (`python story_check.py`, bots, 300 fights per bot type): using the weakness saves turns and
HP for every victim (e.g. Martha 11.8 -> 8.8 turns and 56% -> 0% HP lost; Henry 14.7 -> 1 turn). For Ned and
the twins naive players can hit the weakness **by chance** (80% / 51% of naive bots), so for them the
measure is how **often** the weakness is used (share of whistle turns attacked, share of attacks on the
real Lily), not only whether it was used once.

New actions only exist in story mode: **Shine** (L) and **Call name** (N). Everything else (attack, defend,
potion, timing bar, rest) works as now.

## 3. One game = one night

- A night is **7 rooms**: 4 normal rooms (unchanged ghosts), **2 victim rooms**, and the **finale**
  (fixed per night in `game/victims.py`, NIGHTS). Difficulty is always `normal`; only Walt's help differs.
- Each player plays **3 nights** (A, B, C), each with a **different companion version**.
- The order is **rotated** between players (Latin square), so every companion version is played equally
  often as the 1st, 2nd and 3rd game and with every night:

| Player | Game 1 | Game 2 | Game 3 |
|---|---|---|---|
| P01 | Night A, silent | Night B, scripted | Night C, LLM |
| P02 | Night B, scripted | Night C, LLM | Night A, silent |
| P03 | Night C, LLM | Night A, silent | Night B, scripted |
| P04 | Night A, scripted | Night B, LLM | Night C, silent |
| P05 | Night B, LLM | Night C, silent | Night A, scripted |
| P06 | Night C, silent | Night A, scripted | Night B, LLM |
| … | (repeat from P01) | | |

- The game picks the night and the companion version **automatically from the player ID**, and hides
  which version is playing.

## 4. The three companions ("companion brains")

Each version is a **complete companion**. The study compares the three companions as a whole (as is
common for companion/agent studies); it does not claim which single feature made a difference.

| What Walt does | Silent Walt | Scripted Walt | LLM Walt |
|---|---|---|---|
| **How he helps in each room** (stay_back / hint / heal / fight) | always `hint` | chosen by **rules** (the Study 1 rule director's logic) | **chosen by the LLM** from the situation (HP, potions, skill estimate, which victim is next, what happened so far), with a one-line reason |
| **Victim backstories** (contain the clue) | none | fixed, hand-written | **told by the LLM** from a fact sheet; the clue fact must be in it (checked, otherwise the scripted line is used) |
| **Stepping in during a fight** (when the player struggles: 3 misses in a row, HP below 40%, or 3 turns without using the weakness) | never | fixed rules: offers the rest / repeats the clue | **the LLM decides** what to do: encourage, re-tell the clue in other words, offer the rest, or step in and fight for a turn |
| **"Walt, help!" button** (H, the player asks for help) | "..." (nothing) | one fixed line per victim | **the LLM answers** from what it knows about this fight (no free typing; one button) |
| **Comments after each room** | none | fixed line per result (too easy / good / too hard) | **the LLM comments** on how this player did, in Walt's voice |
| **Memory of the night** | none | none | **remembers earlier rooms**: a short running summary goes into every prompt ("like with Martha, think about what scared them") |
| Voice | same voice for all three versions | | |

Safety and fairness rules for LLM Walt:
- Every LLM answer is **JSON with fixed fields** (help mode, text, action) and is **validated**; anything
  invalid falls back to the scripted behaviour (logged as `fallback`).
- The weakness **clue fact** must appear in the backstory (keyword check). Scripted and LLM Walt therefore
  give the same information; LLM Walt tells it differently, reacts and decides.
- Walt's help is limited to the same help modes as in Study 1, so LLM Walt cannot make the game easier
  than the other companions can; he can only choose **when** and **how** to help.
- All prompts, answers, response times and fallbacks are logged; answers are cached.

## 5. What is measured (saved to data/story_runs.csv)

Per victim room:
- **weakness_used** (yes/no) and **turn_first_used**: did the player find the weakness, and how fast
- turns to defeat, HP lost, deaths, band (same rule as Study 1)
- Walt's help mode, how often he stepped in (and what he did), how often the player pressed **"Walt, help!"**
- for LLM Walt: every prompt and answer, response time, clue check passed, fallbacks

After each night (short screen in the game):
- **"How fun was it?"** (1–5), **"Did Walt help you?"** (1–5), **"Did Walt feel like a real companion?"** (1–5)
- **Comprehension check**, one question per victim met, e.g. *"What was Martha afraid of?"* (3 choices).
  This separates **understanding** the clue from **using** it in the fight.

Main comparisons (within each player, order rotated): weakness use and speed, comprehension, HP lost and
band, and the three ratings, for silent vs scripted vs LLM Walt.

## 6. Time plan (deadline 1 Dec)

| Week | Work |
|---|---|
| 1 | Victim ghosts: art, weaknesses, new actions, victim rooms in story mode (bot sanity check: normal game unchanged) |
| 2 | The three Walt brains: rule help, scripted lines, LLM help choice, LLM backstories, step-in decisions, "Walt, help!" button, room comments, night memory; playtest mode (rotation, hidden version, questions) |
| 3 | Pilot with 1–2 people, fix, then playtest with 9–15 friends (3 nights each, about 30–40 min per person) |
| 4 | Analysis, documentation (both studies), slides, rehearsal |

**Cut first if late (in this order):** room comments, night memory, "Walt, help!" button, then Night C.
The core that must stay: LLM chooses Walt's help + LLM backstories + LLM step-in decisions.

## 7. Open points

- **Check with the professor** that adding Study 2 to the accepted exposé is fine.
- At least 9 players are needed (3 per rotation row); 12–15 is better.
- The LLM runs live: about 3–4 calls per room (help choice + backstory in one call while walking, up to 2
  step-in decisions, help-button answers), roughly 25 calls per night, about 1 minute of model work per
  game. Walking hides most of the waiting; during a fight Walt shows a short "thinking..." moment. Laptop
  heat must be tested in the pilot (fallback: smaller model `llama3.2:1b`, or fewer calls).
- With all features bundled, the result says "LLM Walt vs scripted Walt as a whole", not which feature
  helped. Per-feature effects can only be explored descriptively (e.g. players who used "Walt, help!").
