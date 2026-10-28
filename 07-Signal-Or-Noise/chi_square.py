"""
chi_square.py: when quality is buckets, not a mean.

Run:  python chi_square.py
      python chi_square.py --old 70 20 10 --new 55 35 10

Many important outcomes are categories: resolved automatically, escalated to a human,
refused. Chi-square asks whether the distribution across categories shifted more than
ordinary noise would explain.

    χ² = Σ (O − E)² / E          O = observed count, E = expected count if nothing changed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from stats_tests import chi_square, fisher_exact, fmt_p

HERE = Path(__file__).parent


def main() -> None:
    data = json.loads((HERE / "data" / "escalation_policy.json").read_text(encoding="utf-8"))
    ap = argparse.ArgumentParser(description="Chi-square test, step by step.")
    ap.add_argument("--old", type=int, nargs="+", default=data["old_policy"])
    ap.add_argument("--new", type=int, nargs="+", default=data["new_policy"])
    a = ap.parse_args()
    cats = data["categories"] if len(a.old) == len(data["categories"]) else [f"category {i + 1}" for i in range(len(a.old))]

    res = chi_square([a.old, a.new])
    exp = res["expected"]
    n_old, n_new = sum(a.old), sum(a.new)
    print(f"Support conversations per returns policy ({n_old} old, {n_new} new):\n")
    print(f"  {'outcome':26} {'old O':>6} {'old E':>7} {'new O':>6} {'new E':>7}   (O − E)² / E")
    print("  " + "─" * 80)
    for j, cat in enumerate(cats):
        parts = [(a.old[j] - exp[0][j]) ** 2 / exp[0][j], (a.new[j] - exp[1][j]) ** 2 / exp[1][j]]
        print(f"  {cat:26} {a.old[j]:>6} {exp[0][j]:>7.1f} {a.new[j]:>6} {exp[1][j]:>7.1f}   "
              f"{parts[0]:.2f} + {parts[1]:.2f}")
    print(f"\n  E = what each policy would get if nothing changed (its share of the combined totals).")
    print(f"  χ² = {res['chi2']:.2f}, degrees of freedom = (2 − 1) × ({len(cats)} − 1) = {res['df']}, "
          f"p = {fmt_p(res['p'])}")

    print("\nReport the raw numbers, not only the p-value:")
    for j, cat in enumerate(cats):
        print(f"  {cat:26} {a.old[j] / n_old:>5.0%} -> {a.new[j] / n_new:>5.0%}")
    if res["p"] < 0.1:
        print(f"\np = {fmt_p(res['p'])} is not a magic yes/no line. It is evidence that the distribution may have")
        print("shifted. The next question is about the product, not the math: if escalations went up,")
        print("is that acceptable, intended, or a sign the new policy pushes work onto people?")

    if min(min(r) for r in exp) < 5:
        print("\n! Some expected counts are below 5: the chi-square approximation is unreliable here.")
        print("  Use Fisher's exact test (2×2) or merge categories.")
    print("\nSmall counts, for comparison: 2 of 20 vs 7 of 20 conversations escalated.")
    print(f"  Fisher's exact test: p = {fmt_p(fisher_exact([[2, 18], [7, 13]]))}")
    print("  A non-significant result on a small sample can still hide a real, serious change.")
    print("\nIf the SAME conversations went through both policies, the outcomes are paired: for")
    print("pass/fail use McNemar's test instead (see choose_test.py).")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
