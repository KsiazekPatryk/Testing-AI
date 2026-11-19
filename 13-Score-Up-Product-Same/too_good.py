"""
too_good.py: when the score is too beautiful.

Run:  python too_good.py

A team announces 100% on every measurement, reached overnight. That number should worry you before
it delights you.
  1. tuning against the test set: the same queries, fixed one by one until the dashboard is perfect.
     Not a perfect search engine: a system that knows the exam.
  2. reusing one holdout: in classic software, rerunning the same regression suite is normal.
     In model evaluation, optimizing again and again against the same holdout quietly destroys it.
     The evaluation stops measuring generalization and starts measuring exposure.
"""

from __future__ import annotations

import random
import sys

TRUE_QUALITY = 0.78        # the share of queries the search engine really gets right


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def tuned_on_the_test() -> None:
    test = [True] * 39 + [False] * 11                                   # 78% of 50 test queries
    batches = [0, 4, 3, 2, 2]                                           # special cases added each night
    patched = 0
    header("1. TUNING AGAINST THE TEST SET")
    print(f"  {'night':6} {'test set (50 queries)':>22} {'fresh queries':>14}   what the team did")
    for night, add in enumerate(batches):
        patched += add
        test_score = (sum(test) + patched) / len(test)
        # a query-specific fix helps an unseen query only if it is nearly identical: ~1 in 1,000
        fresh = TRUE_QUALITY + patched * 0.001
        did = "baseline" if not add else f"special cases for {add} more failing test queries ({patched} so far)"
        print(f"  {night:<6} {test_score:>22.0%} {fresh:>14.1%}   {did}")
    print("  'Every measurement at 100%' was every measurement on the queries the team kept fixing.")
    print("  Not a perfect search engine: a system that knows the exam.")


def reused_holdout(seed: int = 7, rounds: int = 25, variants: int = 8) -> None:
    rng = random.Random(seed)
    header(f"2. ONE HOLDOUT, REUSED: {rounds} ROUNDS x {variants} PROMPT VARIANTS")
    print("  Every variant is truly equal (78%). Each round, the team keeps the variant that scores best")
    print("  on the same 100-query holdout. A fresh 1,000-query set is checked only at the end.\n")
    holdout = [rng.random() for _ in range(100)]                       # query difficulty
    best = 0.0
    shown = []
    for r in range(1, rounds + 1):
        for _ in range(variants):
            # a variant gets each holdout query right with the same true probability; luck decides which
            score = sum(rng.random() < TRUE_QUALITY for _ in holdout) / len(holdout)
            best = max(best, score)
        if r in (1, 5, 10, 25):
            shown.append((r, best))
    for r, b in shown:
        print(f"  after round {r:>2}: best holdout score {b:.0%}")
    fresh = sum(rng.random() < TRUE_QUALITY for _ in range(1000)) / 1000
    print(f"  the chosen variant on fresh data: {fresh:.0%}")
    print("\n  The holdout score climbed by selection alone. Keep a holdout you look at rarely, refresh it,")
    print("  and confirm any win on data the team has never optimized against.")


def main() -> None:
    tuned_on_the_test()
    reused_holdout()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
