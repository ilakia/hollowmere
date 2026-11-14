# Study 2: Does an AI companion help players? (design, as built)

Study 1 (done, frozen) asked **who should control difficulty** (rule, bandit, LLM, predictor) and was
answered with bots. Study 2 takes three of those directors, turns each into a **companion** (Walt) and
tests them with **real players**:

> **Does an LLM-driven companion (that adjusts difficulty, decides how much to reveal, remembers the player
> and talks to them) keep players in the right difficulty band, help them discover hidden mechanics and
> make the game more enjoyable than a scripted or a silent companion?**

**Outcome (14 Nov 2026):** the playtest with friends did not take place before the deadline. Study 2 was
finished with the bot test on the playtest nights (main evidence) and the developer's own 16 nights (a
single-player case, not evidence for H1-H5). Results and limits: **REPORT.md** (`python analyze_final.py`).
The playtest design below stays ready for a later study with real players.

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

Per activity (one per night in the playtest: Flashlight Search, Lake Crossing, Bucket Brigade): start and end
difficulty and help, successes, mistakes, pressure (share of the fail budget used), the activity band, how
often Walt stepped in (and what he said). After each night also: **"Which part did you enjoy most?"** (the
fights / the ghosts' stories and tricks / the challenge / the story).

Pilot changes (before the first playtest player, 12-13 Nov): the Lake Crossing became a dodging game (steer
between three lanes), and Night C's Smoke Escape was replaced by the Bucket Brigade (same engine rules as in
the bot runs and the activity band model). Each activity starts with 3 practice steps that are not counted.
If an LLM decision is not ready 2 s after the walk, scripted Walt's rule decides that room (logged as "timeout").
When Walt changes the difficulty in the middle of an activity (the checkpoints after 1/3 and 2/3), the change is
now visible in the game itself, without any text: it glides in over about a second (lake: the fog rolls back or
in and the boat slows down or speeds up; flashlight: the light grows or shrinks; bucket: the other fires calm
down or flare up). The engine rules and the checkpoints are unchanged (bot results identical).
LLM Walt v3 (13-14 Nov, section 6c): safety net for clearly worse choices, a second try for his own sentence,
and a shorter list of options when he steps in. Text in the window (strike rating, keepsake found) was moved
so it no longer covers Walt.

## 5b. Hypotheses and analysis plan (fixed on 11 Nov 2026, BEFORE any playtest data)

Written down before the playtest so the results cannot shape the questions. Each player plays the three
nights (A, B, C) with the three Walt versions in one of 6 rotated orders; every comparison is **within the
same player** (LLM Walt vs the player's own nights with the other versions).

**Main measure for difficulty:** per night, the share of the **adjustable rooms** that ended in band: the 3
normal fights and the activity (4 rooms where Walt chose the difficulty; victims and finale excluded:
victims depend on finding the trick, the finale is a boss).

| | Hypothesis (direction) | Measure | Based on |
|---|---|---|---|
| H1 | LLM Walt keeps more adjustable rooms in band than silent Walt | in-band share per night | Study 1 and the bot pre-check (fights: LLM 50%, silent 39%) |
| H2 | With LLM Walt the night feels closer to "just right" than with silent Walt | distance of "How hard was this night?" from 3 (smaller = better) | the band idea, from the player's side |
| H3 | With scripted and with LLM Walt, players find more victim weaknesses than with silent Walt | share of the 2 victims whose weakness was used | hint ladder bot check (scripted 90%, silent 24%) |
| H4 | LLM Walt feels more like a real companion than scripted and than silent Walt | rating 1-5 | the research question |
| H5 | Nights with LLM Walt are more fun than with silent Walt | rating 1-5 | the research question |

**Tests:** for each hypothesis the per-player difference (e.g. LLM minus silent); an exact one-sided sign
test (how many players are better with LLM Walt than without, ties dropped); the p-values of H1-H5 (six
comparisons: H3 and H4 have two each) are corrected with Holm's method. Reported for every comparison: the
mean difference with a bootstrap 95% interval (seed 42), and how many players were better / worse / equal.
With 9-18 players only large effects can be shown; small or unclear results are reported as such, not as
"no effect".

**Exploratory (no hypothesis, reported descriptively):** LLM vs scripted Walt on H1-H3; the activities
on their own (bots: LLM Walt did not follow the numbers well there); hint level at discovery; "Walt, help!"
presses; comprehension; which part was most fun; LLM waiting times, fallbacks and dropped sentences;
keepsakes found (Night B).

**Who is counted:** playtest IDs only (not PILOT*, GUEST or the developer's own ID). A player who stops
early counts for the nights they finished; within-player tests use the pairs that exist.
**When the playtest ends:** at 18 players or on 24 Nov, whichever comes first (changed 14 Nov: see the amendment below).
**Known limits:** fixed night order (night and position cannot be separated); LLM Walt differs from the
others in several ways at once (difficulty numbers, talking, memory), so the comparison is of companions as
a whole; bots and the activity settings come from the same simulator (the playtest is the real test).

### Amendment (14 Nov 2026, still BEFORE any playtest data): 4-5 players

Reason: only 4-5 players can be recruited, not 9-18. Nothing has been played yet, so this change cannot be
driven by results. The hypotheses H1-H5 and their measures stay the same; what changes is how they are
judged.
- **Why the sign tests are dropped as the decision rule:** with 5 players, even 5 of 5 players better gives
  p = 1/32 = 0.031; after Holm's correction for 6 comparisons that is at best 0.19. No result could ever be
  "significant", so the tests would only look like evidence.
- **Main quantitative evidence = the bot test** (section 6c, fixed test plan, fresh seeds, about 180
  adjustable rooms per version). It answers H1 (rooms in band) and H3 (weaknesses found) for simulated
  players.
- **The playtest = a small user study** that checks whether the bot pattern also shows with real players,
  and is the only source for H2, H4 and H5 (felt difficulty, companion feeling, fun). Reported for each
  hypothesis: every player's value per Walt version (a table and a dot plot, one line per player), the
  number of players better / worse / equal with LLM Walt, and the mean difference. No p-values are claimed
  as confirmation; the sign-test p-values may be shown with the note that they cannot reach 0.05 after
  correction. H1 is also shown per room, pooled over players (about 5 players x 4 adjustable rooms = 20
  rooms per version), as a description, not a test.
- **What counts as "supports":** the playtest is read as *consistent* with a hypothesis when most players
  (at least 4 of 5, or 3 of 4) are better with LLM Walt and the mean difference points the same way;
  otherwise as *not shown*. Both are reported in the same way.
- **The open answers become central:** after the last night each player is asked two short open questions
  (what Walt did that helped or annoyed; which night felt best and why), noted word for word.
- **Orders:** player IDs P01, P02, ... in order. P01-P03 get orders 1-3, which form a Latin square (each
  Walt version once on each night), so with 3 players night and version are already balanced; P04-P05 add
  orders 4-5. The imbalance with 4-5 players is reported.
- **When the playtest ends:** when 5 players have finished, or on 24 Nov, whichever comes first.

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

### 6c. LLM Walt v3 and the final bot test (13-14 Nov, before the first playtest player)

Three changes, made because the pilot showed he often sounded like scripted Walt (46% of sentences dropped)
and the bots showed weak activity results:
- **Safety net:** if his choice has a predicted in-band chance more than 10 points below the best option,
  the best option is played (logged `llm_corrected`). He still chooses and still says his own sentence.
  At step-ins the same rule uses the distance of the expected end from 50%.
- **Second sentence try:** if his sentence fails the checks, he is asked once more with a short prompt that
  names the chosen help; only if that also fails is the fixed line used.
- **Step-in shortlist:** at a step-in he only sees options whose expected end is within 5 points of the
  best one (at most 3).

Test plan (fixed before running): development seeds 600000 (old vs new), tuning seeds 610000 (check the
step-in shortlist), then one **final run on fresh seeds 620000** with all four versions, reported as it
came out. Bots: 3 bot types x naive / listen / smart x 2 nights x Nights A, B, C (with activities).
Run in one-night batches with the charger connected (the laptop shut down on battery again).

Development seeds (600000): own sentence 53% (old) -> 87% (new); activities in band 19% -> 26%; normal
fights 69% -> 67%. The step-ins made activities too easy, hence the shortlist.

**Final test, fresh seeds 620000** (about 180 adjustable rooms per version, about 105 activities):

| Walt | Adjustable rooms in band (H1 measure) | Normal fights | Activities | Night A / B / C |
|---|---|---|---|---|
| silent | 40% | 45% | 34% | 36 / 40 / 43% |
| scripted | 41% | 42% | 40% | 39 / 40 / 43% |
| **LLM v3** | **53%** | 60% | **46%** | 52 / 62 / 44% |
| predictor only (ablation) | 50% | 61% | 38% | 49 / 52 / 49% |

LLM Walt v3: own sentence in 90% of rooms, 23% of decisions corrected by the safety net, 0 fallbacks,
0 timeouts, 3.6 s of model time per room (hidden while the player walks).
Reading: LLM Walt is ahead of silent and scripted Walt in both fights and activities, and level with the
predictor (ahead in the activities, equal in the fights); Night C is his weakest night (44%). With about
180 rooms per version, differences under about 10 points are within chance. These are bots from the same
simulator; the playtest is the real test. Victim rooms are judged by discovery, not by the band.
Data: `data/llm_batches_v3/` (development), `data/llm_batches_v4/` (tuning), `data/llm_batches_v5/` (final).
Note: these runs used the bot-only night plan with two activities per night (`--activities`,
NIGHTS_WITH_ACTIVITIES), not the playtest nights (one activity, three fights per night, `game/victims.py`).

**Night C fix (14 Nov).** Night C was the weakest night for every version because of one room: the Ticket
Booth (2 weak wisps) was too easy even on "hard" (expected HP lost 4 / 13 / 18% on easy / normal / hard;
in the final test 81% of these rooms ended too easy). It was replaced by the Helter Skelter (`z2_barrel`,
4 wisps, expected 17 / 46 / 57%, an existing room with Night C artwork), so every Walt can adjust it.
Checked on the **playtest Night C** with fresh seeds 630000 (about 70 adjustable rooms per version):

| Walt | Night C before (Ticket Booth) | Night C after (Helter Skelter) | Fights after | Bucket after |
|---|---|---|---|---|
| silent | 47% | 65% | 74% | 39% |
| scripted | 46% | 67% | 76% | 39% |
| LLM v3 | not run | 67% | 75% | 41% |
| predictor only | 53% | 67% | 76% | 39% |

The room itself went from 6% in band to 72%. On this night all versions are now level (65-67%): the fix
makes Night C fairer and better to play for everyone; it does not give LLM Walt an advantage there.
LLM Walt here: own sentence 87%, 0 timeouts, 6.0 s model time per room (in the window the walk hides about
the first seconds; anything not ready 2 s after the walk is decided by the scripted rule and logged).
Data: `data/llm_batches_v6/`.

**All three playtest nights (14 Nov, seeds 630000, the night plan players will actually play, with the new
Night C; about 215 adjustable rooms per version):**

| Walt | Adjustable rooms in band | Normal fights | Activities | Night A / B / C | Too easy / too hard |
|---|---|---|---|---|---|
| silent | 63% | 71% | 39% | 54 / 69 / 65% | 25 / 12% |
| scripted | 60% | 65% | 43% | 42 / 71 / 67% | 31 / 9% |
| **LLM v3** | **66%** | 74% | 42% | 61 / 71 / 67% | 23 / 11% |
| predictor only | 73% | 81% | 50% | 79 / 74 / 67% | 15 / 12% |

LLM Walt v3: own sentence 84%, 18% corrected by the safety net, 3 fallbacks, 0 timeouts, 4.6 s per room.
Reading: on the playtest nights LLM Walt is slightly ahead of silent (+3 points) and scripted (+6), which is
within chance at this size, and behind the predictor alone (-7), mostly on Night A. There, in the Tilted
Room, both choose "hard", but LLM Walt often adds healing or hints (the predictor stays back), so 12 of 18
of these rooms ended too easy. The larger lead in the two-activity bot plan (53% vs 40-41%) does not carry
over to the playtest nights. For the write-up: bots support "LLM Walt is at least as good as the simple
versions at keeping rooms in band"; they do not support a large advantage on the playtest nights.

**Last changes and final check (14 Nov, fresh seeds 640000, playtest nights).** Two changes from the
diagnosis above: (1) Night A's Tilted Room (expected 11 / 24 / 32% HP lost) was replaced by the Laughing
Stage (wraith + wisp, 19 / 37 / 55%, an existing room with its own artwork), the same reason as the Night C
fix; (2) before a room or activity LLM Walt only sees options at most 5 points below the best (at most 6 for
rooms, 3 for activities), the rule that already fixed his step-ins (`ROOM_CLOSE`, `close_options`).
About 215 adjustable rooms per version:

| Walt | Adjustable rooms in band | Normal fights | Activities | Night A / B / C | Too easy / too hard |
|---|---|---|---|---|---|
| silent | 53% | 64% | 19% | 43 / 54 / 61% | 31 / 16% |
| scripted | 57% | 64% | 39% | 44 / 56 / 72% | 33 / 10% |
| **LLM v3 (final)** | **62%** | 74% | 25% | 60 / 57 / 68% | 25 / 14% |
| predictor only | 67% | 75% | 43% | 64 / 71 / 67% | 19 / 14% |

LLM Walt: own sentence 88%, 0% corrected (the shorter list leaves no clearly worse option), 3 fallbacks,
0 timeouts, 5.0 s model time per room. The new Laughing Stage room is in band 70% (non-LLM versions).
Reading: LLM Walt is ahead of silent (+9 points) and scripted Walt (+5) and 5 points behind the predictor
alone. In the **fights** he now equals the predictor (74% vs 75%); his weak spot is the **activities**
(25%, only about 54 activities, so this number is uncertain; the lake in Night B was 17%). These are the
settings the playtest uses; nothing is changed after this check. Data: `data/llm_batches_v7/`.

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
