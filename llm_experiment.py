"""
Test the LLM director against fixed, rule and bandit on the same bots and dice rolls.

The LLM is slow (about 3 s per new situation on an M1), so it plays fewer runs than the
other tests: --games runs per bot type on seeds 100000+, the same seeds the other directors
were tested on (paired comparison on exactly those runs). Answers are cached in
data/llm_cache.json, so a re-run is fast and gives identical results.

--no-list runs the ablation: the model is not told which attractions are allowed.

Examples:
  python llm_experiment.py --games 50                                   # plain LLM, test seeds
  python llm_experiment.py --controller llm_risk --games 25 --seed-start 1500   # develop on training seeds
  python llm_experiment.py --controller llm_risk --games 50             # final test, once
"""
import argparse
import random
import time

import pandas as pd

from game.bots import Bot
from game.controllers import CONTROLLERS, LLMController
from game.engine import play_run
from game.story import Story
from sanity_check import ORDER, summary
from simulate import simulate

TEST_SEED_START = 100000   # the seeds every director was tested on


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=50, help="runs per bot type")
    ap.add_argument("--no-list", action="store_true", help="ablation: do not list the allowed attractions")
    ap.add_argument("--controller", default="llm", choices=["llm", "llm_risk"])
    ap.add_argument("--seed-start", type=int, default=TEST_SEED_START,
                    help="use training seeds (e.g. 1500) while developing a prompt, test seeds only once")
    ap.add_argument("--batch", type=int, default=5, help="seeds per batch before a cooling pause")
    ap.add_argument("--pause", type=int, default=120, help="seconds to pause between batches (laptop cools down)")
    args = ap.parse_args()

    LLMController.list_valid_beats = not args.no_list
    label = args.controller + ("_no_list" if args.no_list else "")
    if args.seed_start != TEST_SEED_START:
        label = label + f"_dev{args.seed_start}"
    SEED_START = args.seed_start
    director = CONTROLLERS[args.controller]
    story = Story()
    rows = []
    calls_at_batch_start = 0
    for seed in range(SEED_START, SEED_START + args.games):
        for profile in ORDER:
            bot = Bot(profile, random.Random(f"bot-{profile}-{seed}"))
            controller = director(rng=random.Random(f"ctrl-{seed}"))
            for row in play_run(controller, bot, story, seed):
                row.update({"run_id": f"{label}-{profile}-{seed}", "controller": label, "bot_type": profile})
                rows.append(row)
        LLMController.client.save_cache()   # save after every seed, so an interruption loses little
        client = LLMController.client
        print(f"seed {seed}: {client.calls} model calls, {client.cache_hits} cache hits, "
              f"{client.failures} failures", flush=True)
        # pause after every batch of seeds, but only if the model actually had to work in this batch
        seeds_done = seed - SEED_START + 1
        if seeds_done % args.batch == 0 and client.calls > calls_at_batch_start:
            print(f"cooling pause {args.pause} s", flush=True)
            time.sleep(args.pause)
        if seeds_done % args.batch == 0:
            calls_at_batch_start = client.calls

    llm = pd.DataFrame(rows)
    llm.to_csv(f"data/{label}_runs.csv", index=False)
    # the other directors on exactly the same seeds; the plain LLM too when testing llm_risk on the
    # test seeds (its answers are cached there, so this costs no extra model work)
    other_directors = ["fixed", "rule", "bandit"]
    if args.controller != "llm" and SEED_START == TEST_SEED_START:
        other_directors.append("llm")
    others = simulate(other_directors, ORDER, args.games, seed_start=SEED_START)
    table = summary(pd.concat([others, llm], ignore_index=True))

    client = LLMController.client
    print(f"\nSeeds {SEED_START}-{SEED_START + args.games - 1}, {args.games} runs per bot type\n")
    with pd.option_context("display.width", 140, "display.float_format", "{:.2f}".format):
        print(table.to_string(index=False))
    overall = pd.concat([others, llm]).groupby("controller")["in_band"].mean()
    print("\nIn band, all bot types together:", {c: round(v, 3) for c, v in overall.items()})
    print(f"\nLLM: {len(llm)} rooms, invalid decisions {1 - llm['decision_valid'].mean():.1%}, "
          f"model calls {client.calls}, cache hits {client.cache_hits}, failures {client.failures}, "
          f"{client.seconds / max(client.calls, 1):.2f} s per call")
    print("LLM choices (normal rooms):")
    normal = llm[~llm["is_finale"]]
    print(pd.crosstab(normal["difficulty"], normal["help_mode"]).to_string())
    table.to_csv(f"data/{label}_comparison.csv", index=False)


if __name__ == "__main__":
    main()
