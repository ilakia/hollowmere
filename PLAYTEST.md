# Running the Study 2 playtest

One session = one player, three nights (A, B, C), about 40-45 minutes. The game chooses the night and the
Walt version from the player ID (6 rotated orders, `game/playtest.py`); the player never sees which version
is playing. The hypotheses and the analysis plan are fixed in STUDY2.md (5b) and must not change now.

## Before each session (checklist)

- [ ] **Charger connected and recognised.** In a terminal: `pmset -g batt` must say *AC Power*. The test
      laptop's battery is worn ("Service Recommended", 53%) and the Mac switched off twice when the model
      started on battery.
- [ ] Ollama running: `brew services start ollama`, then `ollama list` shows `llama3.2:3b`.
- [ ] Laptop cool, other apps closed (browser, video).
- [ ] Sound on, headphones ready (Walt speaks).
- [ ] Next free player ID from the ID sheet (P01, P02, ... in order). **Never a real name.**
- [ ] Session log sheet ready (ID, date, start time, problems).

## Consent (read out, the same for everyone)

> "This is a game for my university project. You will play three short nights in a haunted theme park.
> The game saves what you do in the game and your answers to a few questions after each night, under a
> code (for example P07), never your name. Nothing else is recorded. You can stop at any time without
> giving a reason. Is that okay for you?"

Only continue after a clear yes. Write "consent: yes" on the log sheet.

## Starting

```
cd /Users/ilakia/hollowmere
.venv/bin/python play_window.py --playtest
```

On the title screen press **I**, enter the player ID, then **Start**.

## Instructions (read out, the same for everyone, nothing more)

> "You'll play three nights. An old mechanic called Walt goes with you. Play the way you like: the
> controls are shown on screen. I can't help you while you play, but tell me if something breaks.
> After each night there are a few questions; there are no right or wrong answers about the game."

Do **not** explain the ghosts' tricks, the activities, or that Walt behaves differently in different
nights. Answer only technical questions ("the window froze").

## During the session

- Sit where you cannot see the screen closely; don't react to what happens.
- After each night the questions appear; then **"...or maybe not?"** starts the next night.
- Note on the log sheet: crashes, long "Walt is thinking" waits, anything unusual, with the time.
- If the Mac switches off: that night is not saved. Restart, start the game with the same ID; it continues
  with the night that is missing.

## After the third night

- Thank them. **Debrief:** "Walt was a different version in each night: one silent, one with fixed lines,
  one run by a language model. Please don't tell other players before they have played."
- Back up the data (after every session): copy `data/story_runs.csv`, `data/story_answers.csv` and
  `data/player_profiles.json` to a private place (USB stick or private cloud folder). `data/` is not in git.
- Quick check: `.venv/bin/python analyze_study2.py` shows the new player's nights.

## Who to invite and when to stop

- 9-18 players; 12 or 18 balance the 6 orders best. Friends who have not seen the game.
- The playtest ends at 18 players or on 24 Nov (whichever comes first, as fixed in STUDY2.md).
- Pilot sessions use IDs starting with PILOT; they are left out of the analysis automatically.
