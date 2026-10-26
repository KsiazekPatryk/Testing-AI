"""
compare_versions.py: is version B really better than A?

Run:  python compare_versions.py

The dashboard says A passes 82% and B 84%. Looks like a win. But each number has a
margin of about ±3 points, so A lies somewhere between 79% and 85%, and B between
81% and 87%. B might be better. It might also be practically the same.

When the same test cases run through both versions, compute the difference (B minus A)
for each case and build the interval around those differences. A paired comparison
like this removes a lot of noise.

  whole interval above zero  -> strong evidence of an improvement
  interval crosses zero      -> the data does not settle which version is better
"""

from __future__ import annotations

import sys
from pathlib import Path

from stats import load_jsonl, paired_difference_ci, proportion_ci

HERE = Path(__file__).parent
CANDIDATES = {
    "b_prompt_tweak": "B1: prompt tweak",
    "b_retrieval_fix": "B2: retrieval fix",
}


def main() -> None:
    rows = load_jsonl(HERE / "data" / "version_pairs.jsonl")
    n = len(rows)
    a = [r["a"] for r in rows]
    pa, alo, ahi = proportion_ci(sum(a), n)
    print(f"Same {n} test cases through every version (1 = pass, 0 = fail).\n")

    for key, label in CANDIDATES.items():
        b = [r[key] for r in rows]
        pb, blo, bhi = proportion_ci(sum(b), n)
        print("=" * 78)
        print(f"A vs {label}")
        print("=" * 78)
        print("What the dashboard shows, each version on its own:")
        print(f"  A  {pa:.0%}  (95% CI {alo:.0%}–{ahi:.0%})")
        print(f"  B  {pb:.0%}  (95% CI {blo:.0%}–{bhi:.0%})")
        overlap = blo <= ahi
        print(f"  The intervals {'overlap' if overlap else 'do not overlap'}." +
              (" That alone does not settle it." if overlap else ""))

        better = sum(1 for x, y in zip(a, b) if y > x)
        worse = sum(1 for x, y in zip(a, b) if y < x)
        d, lo, hi = paired_difference_ci(a, b)
        print("\nPaired, case by case (B minus A):")
        print(f"  B fixed {better} cases that A failed, and broke {worse} cases that A passed.")
        print(f"  difference {d:+.1%}, 95% CI {lo:+.1%} to {hi:+.1%}")
        if lo > 0:
            print("  -> The whole interval is above zero: strong evidence that B is better.\n")
        elif hi < 0:
            print("  -> The whole interval is below zero: B is worse.\n")
        else:
            print("  -> The interval crosses zero: the data does not settle which version is better.")
            print("     A \"maybe better\" change still carries rollout risk: results shift, a page")
            print("     users relied on may drop, the product feels less predictable. A small gain")
            print("     whose interval touches zero may not be worth that risk or the rollout cost.\n")

    print("\"About\", \"approximately\" and \"based on this sample\" do not weaken a report.")
    print("They make it more credible.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
