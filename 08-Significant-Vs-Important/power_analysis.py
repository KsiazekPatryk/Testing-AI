"""
power_analysis.py: is your flashlight strong enough?

Run:  python power_analysis.py
      python power_analysis.py --cases 40 --effect 0.3 --sd 1.2
      python power_analysis.py --rate-from 0.10 --rate-to 0.05

A small evaluation cannot see every small difference. "No significant difference" from a
small sample often means "the sample could not have seen it", not "the systems are the same".

The script shows (95% confidence, 80% power, two-sided):
  1. what an evaluation of 30, 40, 100... cases can actually detect
  2. how many cases per version you need to see a drop in failure rate (10% -> 5%, 1% -> 0.5%)
  3. the coding agent: 6 vs 4 security problems in 60 tasks
  4. a simulation: run the same small evaluation 2,000 times and count how often it "sees" a real effect
"""

from __future__ import annotations

import argparse
import random
import sys

from stats_tools import (fisher_exact, n_paired_means, n_per_group_proportions, p_str, power_paired_means,
                         power_proportions, smallest_detectable_paired, two_proportions)


def header(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def what_can_it_see(sd: float, effect: float, cases: int) -> None:
    header(f"1. WHAT CAN AN EVALUATION OF N PAIRED CASES SEE? (sd of differences = {sd})")
    print(f"  {'cases':>6}  {'smallest effect seen 80% of the time':>38}  {'chance to see +' + str(effect):>18}")
    for n in sorted({30, 40, 60, 100, 200, 500, 1000, cases}):
        mark = "  <- yours" if n == cases else ""
        print(f"  {n:>6}  {smallest_detectable_paired(sd, n):>34.2f} pts  "
              f"{power_paired_means(effect, sd, n):>17.0%}{mark}")
    need = n_paired_means(effect, sd)
    print(f"\n  To see +{effect} with 80% power you need about {need} paired cases.")
    print(f"  An honest sentence for {cases} cases:")
    print(f"    \"With {cases} cases this evaluation only detects changes of about "
          f"{smallest_detectable_paired(sd, cases):.1f} points or more.")
    print(f"     It is too weak for the +{effect} improvement you are asking about.\"")
    print(f"  And +0.1? You would need about {n_paired_means(0.1, sd):,} cases.")


def failure_rates(p_from: float, p_to: float) -> None:
    header("2. HOW MANY CASES PER VERSION TO SEE A DROP IN FAILURES?")
    print(f"  {'from':>6} {'to':>6}  {'cases per version':>18}")
    pairs = [(0.10, 0.05), (0.06, 0.02), (0.05, 0.025), (0.01, 0.005)]
    if (p_from, p_to) not in pairs:
        pairs.append((p_from, p_to))
    for a, b in pairs:
        print(f"  {a:>6.1%} {b:>6.1%}  {n_per_group_proportions(a, b):>18,}")
    print("  Rare events need a lot of data, or targeted tests that go looking for them.")
    print("  (Approximate: 95% confidence, 80% power, continuity correction included.)")
    p6 = power_proportions(0.06, 0.02, 100)
    print(f"\n  The policy-failure example from two_significances.py (6% -> 2%, 100 per version)")
    print(f"  had a {p6:.0%} chance of reaching significance even if the drop is real.")


def coding_agent() -> None:
    header("3. THE CODING AGENT: 6 vs 4 SECURITY PROBLEMS IN 60 TASKS")
    res = two_proportions(6, 60, 4, 60)
    p = fisher_exact(6, 54, 4, 56)
    print(f"  old 6/60 = {res['p1']:.0%}, new 4/60 = {res['p2']:.1%}. Looks better.")
    print(f"  Fisher's exact {p_str(p)}; the interval for the difference runs from "
          f"{res['ci_low'] * 100:+.1f} to {res['ci_high'] * 100:+.1f} points.")
    print(f"  Power of 60 tasks to tell 10% from 6.7%: {power_proportions(0.10, 4 / 60, 60):.0%}.")
    print(f"  To see it reliably: about {n_per_group_proportions(0.10, 4 / 60):,} tasks per version.")
    print("  This result should trigger more sampling, not a celebration.")


def simulate(sd: float, effect: float, cases: int, rounds: int = 2000, seed: int = 1) -> None:
    header(f"4. SIMULATION: A REAL +{effect} EFFECT, EVALUATED {rounds:,} TIMES ON {cases} CASES")
    rng = random.Random(seed)
    z = 1.959964
    seen = 0
    for _ in range(rounds):
        d = [rng.gauss(effect, sd) for _ in range(cases)]
        m = sum(d) / cases
        s = (sum((x - m) ** 2 for x in d) / (cases - 1)) ** 0.5
        seen += abs(m) / (s / cases ** 0.5) > z
    print(f"  The effect is real in every one of these worlds. The evaluation 'saw' it in {seen / rounds:.0%} of them.")
    print(f"  In the other {1 - seen / rounds:.0%}, the report would say 'no significant difference'.")
    print("\n  The report should not ask 'did p fall below 0.05?' but:")
    print("  'was the evaluation big enough to notice a win that matters to us?'")


def main() -> None:
    ap = argparse.ArgumentParser(description="Power analysis: is the sample big enough for the decision?")
    ap.add_argument("--cases", type=int, default=40, help="cases in your evaluation (default 40)")
    ap.add_argument("--effect", type=float, default=0.3, help="minimum meaningful effect in points (default 0.3)")
    ap.add_argument("--sd", type=float, default=1.2, help="sd of the per-case differences (default 1.2)")
    ap.add_argument("--rate-from", type=float, default=0.10)
    ap.add_argument("--rate-to", type=float, default=0.05)
    a = ap.parse_args()
    what_can_it_see(a.sd, a.effect, a.cases)
    failure_rates(a.rate_from, a.rate_to)
    coding_agent()
    simulate(a.sd, a.effect, a.cases)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
