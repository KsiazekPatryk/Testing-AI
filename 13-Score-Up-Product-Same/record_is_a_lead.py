"""
record_is_a_lead.py: a record is a lead, not proof.

Run:  python record_is_a_lead.py
      python record_is_a_lead.py --attempts 40

Run a noisy evaluation enough times and variance will eventually hand you a beautiful score.
The system does not get better because of it.

A prompt averages 8.0 and sometimes scores 8.6. The team tweaks the prompt, the temperature, the
judge, reruns, and so on, until a new record appears. Here none of the tweaks changes anything real.
  1. the run log: every attempt, and the record
  2. why the best of many runs is inflated by construction
  3. what disappears when only the best runs are kept
  4. the recipe: all runs, mean, spread, interval, a fresh holdout, a stopping rule set in advance
"""

from __future__ import annotations

import argparse
import random
import sys
from statistics import stdev

from evalkit import ci95, mean

TRUE_MEAN = 8.0
RUN_NOISE = 0.30            # how much one evaluation run of the same prompt moves
TWEAKS = ["reword the system prompt", "temperature 0.7 -> 0.5", "swap two few-shot examples",
          "judge prompt: stricter wording", "temperature 0.5 -> 0.3", "add 'think step by step'",
          "judge model update", "shorter instructions", "reorder the rubric", "temperature 0.3 -> 0.6"]


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def run_log(attempts: int, seed: int):
    rng = random.Random(seed)
    return [(TWEAKS[i % len(TWEAKS)], round(rng.gauss(TRUE_MEAN, RUN_NOISE), 2)) for i in range(attempts)]


def main() -> None:
    ap = argparse.ArgumentParser(description="Why the best run is not the result.")
    ap.add_argument("--attempts", type=int, default=20)
    ap.add_argument("--seed", type=int, default=27)
    a = ap.parse_args()
    log = run_log(a.attempts, a.seed)
    scores = [s for _, s in log]

    header(f"1. THE RUN LOG: {a.attempts} ATTEMPTS, NONE OF THEM A REAL CHANGE")
    best = float("-inf")
    for i, (tweak, s) in enumerate(log, 1):
        rec = s > best
        best = max(best, s)
        print(f"  {i:>3}. {tweak:34} {s:5.2f}{'   <- new record' if rec and i > 1 else ''}")
    print(f"\n  Reported in the stand-up: \"new record, {max(scores):.2f}!\"")

    header("2. THE BEST OF MANY RUNS IS INFLATED BY CONSTRUCTION")
    rng = random.Random(a.seed + 1)
    print(f"  true quality of every attempt: {TRUE_MEAN:.1f}. Expected best score after n attempts:")
    for n in (1, 5, 10, 20, 50):
        sims = [max(rng.gauss(TRUE_MEAN, RUN_NOISE) for _ in range(n)) for _ in range(4000)]
        print(f"    n = {n:>2}: {mean(sims):.2f}")
    print("  The more you try, the higher the record, with nothing improved. It is the multiple")
    print("  comparisons problem in disguise. The same goes for cherry-picked examples: a great answer")
    print("  shows what the system can do, not how often it does it.")

    header("3. KEEP ONLY THE BEST RUNS, AND THE EVIDENCE DISAPPEARS")
    kept = sorted(scores, reverse=True)[:3]
    print(f"  kept in the report: {', '.join(f'{k:.2f}' for k in kept)}   (mean {mean(kept):.2f})")
    print(f"  deleted: {len(scores) - len(kept)} runs. Nobody remembers how many attempts did not repeat the 'win'.")

    header("4. THE RECIPE")
    lo, hi = ci95(scores)
    print(f"  all {len(scores)} runs: mean {mean(scores):.2f}, spread (sd) {stdev(scores):.2f}, "
          f"95% CI {lo:.2f} to {hi:.2f}")
    rng = random.Random(a.seed + 2)
    fresh = [rng.gauss(TRUE_MEAN, RUN_NOISE) for _ in range(5)]
    record_tweak = log[scores.index(max(scores))][0]
    print(f"  the record's setup ('{record_tweak}') re-run 5 times on a fresh holdout: mean {mean(fresh):.2f}")
    print("  stopping rule, written before the first run: at most 10 attempts, and a change counts only")
    print("  if its 5-run mean beats the baseline's by more than the interval width.")
    print("\n  Report all runs, not the record.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
