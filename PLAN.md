# Plan (deadline: files ready by 1 Dec 2026, official 4 Dec)

| Week | Dates | Work | Done when |
|---|---|---|---|
| 1 | 18 to 25 Oct | Game core v0.1 (done 18 Oct). Read every file. Play 3 runs yourself. Final balance check, then **freeze** config, band rule and telemetry columns. Confirm exposé acceptance, book presentation slot. | `sanity_check.py` passes, config frozen |
| 2 | 26 Oct to 1 Nov | Skill estimator (moving average of recent rooms). Rule-based director. Training data from the `random` director. Failure predictor with gradient boosting. | Rule director beats fixed on in-band share |
| 3 | 2 to 8 Nov | Contextual bandit (LinUCB): write and justify the reward first. Small LSTM predictor vs gradient boosting. | Bandit learning curve plotted |
| 4 | 9 to 15 Nov | LLM director (Ollama, ~3B model): JSON output, validation, cache, timing. Ablation: free text vs valid-beats-only. (SECOM presentation 11 Nov.) | LLM runs 200+ games without crashing |
| 5 | 16 to 22 Nov | Full experiments: all directors × all bots, held-out bot type, ±20% sensitivity check. Pygame demo panel. Playtest with 5 to 10 friends. | Results tables and figures final |
| 6 | 23 Nov to 1 Dec | 3-page documentation, slides, rehearse the 15 minutes, buffer. | Submitted 1 Dec |

**If time runs short, cut in this order:** LSTM, human playtest, pygame panel (demo in terminal instead). Write down why each cut was made, since it counts as a learning.
