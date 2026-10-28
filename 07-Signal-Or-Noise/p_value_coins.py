"""
p_value_coins.py: a p-value is evidence, not a release permit. Count it with coins.

Run:  python p_value_coins.py
      python p_value_coins.py --wins 15 --losses 5

The same 20 cases go through the old and the new version. The new one wins 15 times,
the old one 5 times (ties are dropped). If the versions are equal, every case is a coin flip.

How often does a fair coin give 15 or more heads in 20 flips? Count it exactly, then
simulate it. Then see what a p-value is NOT, and why 0.049 and 0.051 carry almost the
same information.
"""

from __future__ import annotations

import argparse
import math
import random
import sys

from stats_tests import binomial_tail, fmt_p, sign_test, welch_t


def exact(wins: int, losses: int) -> None:
    n = wins + losses
    favorable = sum(math.comb(n, i) for i in range(wins, n + 1))
    res = sign_test(wins, losses)
    print("=" * 78 + f"\nCOUNT IT: {wins} wins, {losses} losses out of {n}\n" + "=" * 78)
    print(f"  possible sequences of {n} flips:          2^{n} = {2 ** n:,}")
    print(f"  sequences with {wins} or more heads:          {favorable:,}")
    print(f"  p (one-sided, \"is the new one better?\"):  {favorable:,} / {2 ** n:,} = {res['p_one_sided']:.3f}")
    print(f"  p (two-sided, \"is either one different?\"): {res['p_two_sided']:.3f}")
    print("  Which one to report depends on the question you wrote down BEFORE the test.")


def simulate(wins: int, losses: int, rounds: int, seed: int) -> None:
    n = wins + losses
    rng = random.Random(seed)
    hits = sum(sum(rng.random() < 0.5 for _ in range(n)) >= wins for _ in range(rounds))
    print(f"\nSIMULATE IT: {rounds:,} worlds where the versions are truly equal")
    print(f"  in {hits:,} of them the new version won {wins}+ times by pure luck: {hits / rounds:.3f}")
    print("  That is the p-value: how surprising your result would be in a world with no real difference.")


def what_it_is_not(p: float) -> None:
    print("\n" + "=" * 78 + f"\nWHAT p = {p:.2f} DOES NOT MEAN\n" + "=" * 78)
    print(f"  ✗ that there is a {1 - p:.0%} chance the new version is better")
    print("  ✗ that the improvement is important")
    print("  ✗ that the test was well designed")
    print("  ✗ that the system is safe to ship")
    print(f"  ✓ if the versions were truly equal, a result this extreme would happen about {p:.0%} of the time")


def threshold_is_a_convention(seed: int) -> None:
    rng = random.Random(seed)
    print("\n" + "=" * 78 + "\n0.05 IS A CONVENTION, NOT A LAW OF NATURE\n" + "=" * 78)
    # A small, real improvement (+0.3), measured 2,000 times on 60 cases per version.
    ps = []
    for _ in range(2000):
        old = [rng.gauss(7.8, 1.5) for _ in range(60)]
        new = [rng.gauss(8.1, 1.5) for _ in range(60)]
        ps.append(welch_t(old, new)["p"])
    near = [p for p in ps if 0.04 <= p <= 0.06]
    print("  A small, real improvement (+0.3 points), evaluated 2,000 times on 60 cases per version:")
    print(f"  significant (p < 0.05) in {sum(p < 0.05 for p in ps) / len(ps):.0%} of the evaluations, "
          f"not in the rest. Same change, same truth.")
    print(f"  {len(near)} evaluations landed between 0.04 and 0.06: some 'passed', some 'failed',")
    print("  and they carry almost the same information. Evidence changes smoothly; it does not jump")
    print("  from 'failure' to 'truth' at an arbitrary line.")
    under = sum(p < 0.05 for p in ps)
    print(f"\n  So: report the effect size and its interval first, the p-value second.")
    print(f"  And a non-significant result is weak evidence, not proof of no difference: in {len(ps) - under:,}")
    print("  of these evaluations, reading p ≥ 0.05 as 'no effect' would have dismissed a real improvement.")


def main() -> None:
    ap = argparse.ArgumentParser(description="p-values, counted with coins.")
    ap.add_argument("--wins", type=int, default=15)
    ap.add_argument("--losses", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    exact(a.wins, a.losses)
    simulate(a.wins, a.losses, 100_000, a.seed)
    what_it_is_not(sign_test(a.wins, a.losses)["p_one_sided"])
    threshold_is_a_convention(a.seed)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
