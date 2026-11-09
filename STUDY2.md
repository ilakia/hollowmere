# Study 2: Does an AI companion help players? (design, as built)

Study 1 (done, frozen) asked **who should control difficulty** (rule, bandit, LLM, predictor) and was
answered with bots. Study 2 takes three of those directors, turns each into a **companion** (Walt) and
tests them with **real players**:

> **Does an LLM-driven companion (that adjusts difficulty, decides how much to reveal, remembers the player
> and talks to them) keep players in the right difficulty band, help them discover hidden mechanics and
> make the game more enjoyable than a scripted or a silent companion?**

Study 2 runs in a **separate story mode** ("Night of the Fire"). The normal game, the engine rules used by
the bots and every Study 1 result stay exactly as they are (sanity check unchanged).

## 1. The story mode in one paragraph

In 1987 a fire killed several people at Hollowmere Park. Their ghosts still haunt the attractions where
they worked. Each **victim ghost** has a name, a story and **one weakness** that comes from that story.
Fighting a victim the normal way works, but it is long and painful; using the weakness makes the fight
short. Walt knew every one of them, so what he tells about them contains the **clue**. The normal ghosts
(wisps, animatronics, wraiths) appear in the other rooms; the finale is always Walt.

## 2. Six victim ghosts (2 per night)

| Night | Victim | Who they were | Weakness (how to beat them fast) | Clue (life story) | Tell on screen |
|---|---|---|---|---|---|
| A | **Martha Bell** | Ticket seller | **Shine** the flashlight (L): frozen for 2 turns, double damage | "Hated the dark... never once turned off the lamp at her booth." | Lights flicker |
| A | **Ned Carver** | Ghost-train engineer | **Attack while the train passes** (whistle): double damage; otherwise a third of the damage | "Only time you could reach him was when it came past, whistle blowing." | Whistle, train rushes past |
| B | **Rosa Lindqvist** | Photographer | **Shine into her lens** when she lifts the camera: her own flash blinds her. Otherwise her flash blinds you | "A camera's blind to everything but light." | Camera goes up |
| B | **Lily Ward** (and reflection) | Hall of Mirrors attendant | **Attack the real Lily** (red ribbon); hitting the reflection heals her until the mirror cracks | "Never took off her mother's red ribbon. Her reflections never had it." | Two Lilys |
| C | **Benny Ortiz** | Carousel operator | **Defend while the music plays, strike when it stops** (every 2nd turn): a double hit; attacking the spinning ride throws you off | "Only time Benny stood still was when the music box ran down." | Carousel waltz plays / goes silent, music box with countdown |
| C | **Henry Pike** | Clown Alley barker | **Call his stage name** (N, 3 choices): "The Great Henry" calms him for 3 turns (no attacks, double damage), then he shouts again | "Only way to calm him down was his stage name: The Great Henry." | "WHO AM I?!" |

Balance check (`python story_check.py`, bots): using the weakness saves turns and HP for every victim
(e.g. Martha 11.8 -> 8.7 turns, 56% -> 0% HP lost; Henry 14.9 -> 9.5 turns; Benny 12.8 -> 5.8 turns after
the pilot, where the music box "took forever": it now runs down every 2nd turn instead of every 3rd). For Ned and the twins naive
players hit the weakness **by chance** (87% / 52% of naive bots), so for them how often it is used matters
more than whether it was used once.

## 3. Three nights = three chapters (fixed order A -> B -> C)

| Night | Chapter | What is new in this night |
|---|---|---|
| A | **The First Night** | Walt seems human. Silent signs in the park (photo wall, mirrors, wax museum, workshop). At the gate he reveals he is a ghost and shows the signs the player walked past |
| B | **You Came Back** | Walt is a ghost all night and cannot remember the fire. **Five keepsakes** glint along the walks (press E). At the gate Walt fights **with** the player against **the Smoke** of the fire; once the gate is open he remembers what the found keepsakes show. Measure: keepsakes found |
| C | **The Fire** | The park burns more with every room. Before the gate: the fire of June 1987, **one scene per keepsake found in Night B** (missed ones stay burnt-out frames) and the truth. Then Walt and the player fight **the Blaze** together; true ending |

Pilot feedback (5 Nov) changed the finales of B and C: fighting Walt again after he became an ally made no
sense. The Smoke and the Blaze have exactly Walt's fight values (same HP, damage and charged attack), so the
finale stays equally hard; the difference is that Walt helps (help chosen by his brain, like any room).
Walt's travel lines in B and C now belong to the story of that night, so the rooms connect.

Each night has 7 rooms: 4 normal rooms, 2 victim rooms, the finale (`game/victims.py`, NIGHTS). The story
text lives in `game/chapters.py`.

**New places for Night B and C** (`game/chapters.py`, ROOM_SKINS; drawn in `window/pieces_lake.py`,
`window/pieces_1987.py`, backgrounds in `window/scenery_nights.py`): Night B plays at **the Lakeside**
(Bumper Cars, Rosa's Photo Pier, Swan Boats, Lily's Mirror Maze, Bandstand, Wild Mouse Coaster, the Lake
Gate), Night C in **June 1987**, the burning park (Benny's Carousel, Main Street, the Great Henry's Stage,
Helter Skelter, Food Court, Walt's Workshop, the Main Gate). Each new room keeps the fight of the room it
replaces (same ghosts, threat and beat id in the data), so the difficulty tables, the band rule and the bot
checks are unchanged; only the place and its look are new.

**Design consequence:** because the nights tell one story, the night order is the same for everyone
(A, B, C). Only the **Walt version is rotated** over the three nights, using all 6 orders
(`game/playtest.py`), so every version is played equally often as 1st, 2nd and 3rd night:

| Player ID | Night A | Night B | Night C |
|---|---|---|---|
| P01, P07, P13 | silent | scripted | LLM |
| P02, P08, P14 | scripted | LLM | silent |
| P03, P09, P15 | LLM | silent | scripted |
| P04, P10, P16 | silent | LLM | scripted |
| P05, P11, P17 | scripted | silent | LLM |
| P06, P12, P18 | LLM | scripted | silent |

Limitation: night (and its victims) is now tied to the position (1st/2nd/3rd night), so "Night C is
harder" and "third night" cannot be separated; the companion comparison stays balanced.

## 4. The three companions

Each version is a **complete companion**. The study compares the three companions as a whole; it does not
claim which single feature made the difference.

| What Walt does | Silent Walt | Scripted Walt | LLM Walt |
|---|---|---|---|
| **Difficulty + help before each room** (hidden from the player) | fixed: always normal + hint (= Study 1 **fixed** director) | rules on the skill estimate (= Study 1 **rule** director) | band-model shortlist, the LLM picks (= Study 1 **llm_risk** director) and says one sentence why/how he helps |
| **Victim life story** (hint level 1, contains the clue) | none ("Careful, kid. Something's here.") | fixed, hand-written | told by the LLM from a fact sheet; must contain a clue word, otherwise the fixed text |
| **Hint ladder during a victim fight** (1 story, 2 nudge, 3 exact move) | none (level 0) | fixed: level 2 at turn 4, level 3 at turn 7 | the LLM decides at turns 3 and 6 whether to reveal more, from what the player tried and how hurt they are |
| **"Walt, help!" button** (H, costs no turn) | "..." | the next fixed hint level | the LLM decides what to say (checked like the hints) |
| **Memory across nights** | none | none | a player profile (style, deaths, which weaknesses were found and with which hint, keepsakes) goes into every prompt; skill estimate carries over; he greets a returning player |
| Voice, fights, victims, chapters | same for all three versions | | |

Safety and fairness rules for LLM Walt (`game/walt_llm.py`):
- Every answer is **JSON** and is **validated**: the room decision must be one of the scored options; the
  sentence must be short and must not mention difficulty or numbers; hints of level 2/3 and the life story
  must contain one of the victim's clue words. Anything invalid falls back to scripted Walt (logged).
- He can only choose among the same difficulty levels and help modes as the other versions.
- All answers are cached (`data/walt_cache.json`, separate from Study 1's cache); calls, cache hits and
  seconds are logged per room. He is shown his last 3 sentences so he does not repeat himself.
- **The game never waits for the model** (pilot feedback: "Walt is thinking" was annoying). Every call runs
  in the background: the room decision while the player walks to the room (the ghosts wait only if it is
  still not ready), the life stories as soon as the night starts, hints and help answers during the fight
  (spoken the moment they arrive; "Let me think, kid..." in the meantime). Bots run every call at once, so
  bot results stay repeatable.
- Cut (to save time and laptop heat): Walt's comments after each room.

## 5. What is measured

Per room (`data/story_runs.csv`): difficulty and help chosen, decision source, Walt's sentence and reason,
turns, HP lost, deaths, band (Study 1 rule), timing score; LLM calls / seconds.
Per victim fight additionally: weakness used, turn first used, **hint level when it was found**, highest
hint level, "Walt, help!" presses, hint fallbacks. Night B: keepsakes found.

After each night (questions in the game, `data/story_answers.csv`):
- **Fun**, **"Did Walt help you?"**, **"Did Walt feel like a real companion?"** (1-5)
- **"How hard was this night?"** (1 far too easy ... 3 just right ... 5 far too hard): the player's own view
  of the difficulty band
- **Comprehension**, one question per victim met (3 answers): separates understanding the clue from using it

Main comparisons (`python analyze_study2.py`), per Walt version: share of normal rooms in band (Study 1's
measure, now with humans), discovery (found, how fast, at which hint level), comprehension, ratings; and
within each player LLM vs scripted / silent with an exact sign test. With 9-18 players this is mainly
descriptive.

## 6. Bot pre-check (`python story_brains_check.py`, done before the playtest)

Bots: Study 1's beginner / average / expert, each as naive (ignores weaknesses), listen (understands a
weakness after Walt's hint with an assumed chance of 25% / 50% / 85% at level 1 / 2 / 3) and smart (knows
all weaknesses).

| Walt | Rooms in band (naive) | Too hard (naive) | Weakness found (listen bots) | Difficulty chosen |
|---|---|---|---|---|
| silent | 60% | 13% | 24% (by chance only) | always normal |
| scripted | 59% | 11% | 90% | 96% normal, 4% easy |
| LLM | 76% | 5% | 100% | 49% hard, 49% normal |

Scripted and silent: 100 nights per night x bot type x player type. **LLM: only 9 nights of Night A**
(the model is slow and the laptop gets hot), so the LLM row is a first sign, not a result; it was run
before the pilot changes (shorter answers, Benny every 2nd turn) and should be repeated.
Findings to keep in mind:
- The rule director never chooses "hard" (by design in Study 1), so scripted Walt can barely adjust for good
  players; LLM Walt does use "hard".
- When the weakness is found, a victim fight becomes short and is often "too easy" by the band rule. This
  is intended (finding the weakness is the reward), so victim fights are judged by **discovery**, and the
  band measure is reported for the **normal rooms**.

### 6b. Activities (bots only so far, 8-10 Nov)

Six activities (`game/activities.py`) replace two normal fights per night (`NIGHTS_WITH_ACTIVITIES`). Before
each one Walt chooses the difficulty and his help; at two checkpoints he may step in. "In band" = won while
using 30-70% of the allowed mistakes. Not yet playable in the game window (bots only).

For LLM Walt an **activity band model** was trained like Study 1's (`activity_predictor.py`, logistic
regression on 5,293 activities played with random settings; well calibrated on unseen test nights:
predicted 26% in band -> real 26%). LLM Walt picks from the 6 best scored options, like llm_risk.

| Walt version | Activities in band | beginner / average / expert | Normal fights in band | Activities |
|---|---|---|---|---|
| silent | 29% | 28 / 38 / 23% | 39% | ~1,800 |
| scripted (rules) | 41% | 47 / 42 / 33% | 38% | ~1,800 |
| predictor only (no LLM, ablation) | **44%** | 41 / **52** / **39%** | **56%** | ~1,800 |
| LLM Walt without numbers | 17% | | | 18 |
| LLM Walt with numbers | 26% | 38 / 31 / 11% | 50% | 50 |

Findings (bots, small LLM sample):
- With numbers, LLM Walt nearly matches the predictor in the **fights** (50% vs 56%; Study 1: 76.5% vs 78.5%).
- In the **activities** he does not follow the numbers: he never chose "hard" for experts (the predictor
  did in 93% of their activities) and stepped in more often (1.7 per activity), mostly making things
  easier, so 58% ended too easy. Without numbers he chose "easy" for everyone (17% in band).
- About half of his sentences failed the new checks (wrong help named, repeats); then the fixed line is used.
- Laptop: the test laptop shut down twice when the model started (battery "Service Recommended", 53%
  capacity, no charger). The model must only run with the charger connected; 9 small batches with
  cached answers (`data/llm_batches/`) completed.

**LLM Walt v2 for activities (10-11 Nov).** Why v1 did badly (from the cached answers): when the best
option was "hard" (31 times) he never chose a hard option, and his stepping in did not follow his pace
(when it went too easily he made it easier more often than harder). Changes: the instruction now says to
take the highest in-band chance (kindness is not making it easy: strong players get bored), only the 3
best options are shown, and for stepping in he gets options (keep / easier / harder / more or less help)
each with an expected end from the expected-pressure table. The predictor version got the same stepping-in
numbers (always the option closest to 50%): 44% -> **48%** of activities in band (100 nights per type).
LLM v2, Night A only (18 activities, 3 batches): he now gives experts "hard" in 4 of 6 activities (v1: 0 of
6) and steps in less (1.2 vs 1.9 per activity); in band 33%, the same as v1 on Night A (Night A for 100
nights: predictor 42%, scripted 36%, silent 27%). With 18 activities this cannot be told apart from the
other versions; the LLM tests were stopped here (laptop battery). For the write-up: the LLM follows the
numbers in the fights, and after a clearer instruction partly in the activities.

## 7. How to run the playtest

```
.venv/bin/python play_window.py --playtest
```
The player enters their ID (P01, P02, ...) on the title screen; night and Walt version come from the ID and
the nights they already played, and stay hidden. After each night the questions appear. LLM Walt needs
Ollama running (`brew services start ollama`); the model is loaded while the intro cards are read.

## 8. Time plan (deadline 1 Dec)

| Week | Work |
|---|---|
| 1 (done) | Victims, chapters, three Walts, hint ladder, memory, help button, playtest mode, questions, analysis script |
| 2 | Pilot with 1-2 people (laptop heat, LLM waiting time), fixes; optional: new rooms and backgrounds for Night B and C |
| 3 | Playtest with 9-18 friends (3 nights each, about 40 min per person) |
| 4 | Analysis, documentation (both studies), slides, rehearsal |

## 9. Open points

- **Check with the professor** that Study 2 (and the fixed night order) is fine with the accepted exposé.
  Share the design change with the team.
- LLM speed on the test laptop: the model writes about 8 tokens per second (10-13 s per answer during the
  pilot, with the game running). Answers were shortened (no "reason" field, length cap), which roughly
  halves the time, and every call now runs in the background. If it is still too slow: `llama3.2:1b`
  (needs a download, ask first).
- Test IDs: nights already saved under an ID count for playtest mode, so real players need fresh IDs.
