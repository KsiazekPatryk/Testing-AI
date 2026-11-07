"""
krippendorff_alpha.py: when there are more than two reviewers and the data is messy.

Run:  python krippendorff_alpha.py

  alpha = 1 - observed disagreement / expected disagreement

Alpha handles:
  - more than two reviewers
  - missing ratings (not every reviewer rated every item)
  - ordered scales (0-10), where 7 vs 8 is a smaller disagreement than 2 vs 9

The post's example first, counted pair by pair. Then 0-10 scores with gaps.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

from agreement import krippendorff_alpha, load_jsonl

HERE = Path(__file__).parent
S, R = "safe", "risky"
EXAMPLE = [[S, S, S], [S, S, S], [R, R, R], [S, S, R], [S, R, R]]


def post_example() -> None:
    print("=" * 78 + "\nTHE POST'S EXAMPLE: 3 REVIEWERS, 5 OUTPUTS, SAFE OR RISKY\n" + "=" * 78)
    pairs = disagree = 0
    for i, u in enumerate(EXAMPLE, 1):
        d = sum(x != y for x, y in combinations(u, 2))
        pairs += 3
        disagree += d
        print(f"  output {i}: {', '.join(u):20} reviewer pairs that disagree: {d} of 3")
    values = [v for u in EXAMPLE for v in u]
    s, r = values.count(S), values.count(R)
    res = krippendorff_alpha(EXAMPLE)
    print(f"\n  observed disagreement: {disagree} of {pairs} pairs = {res['observed']:.2f}")
    print(f"  expected, if all {len(values)} labels ({s} safe, {r} risky) were paired at random:")
    print(f"    {s} x {r} mixed pairs / ({len(values)} x {len(values) - 1} / 2) pairs = {res['expected']:.2f}")
    print(f"  alpha = 1 - {res['observed']:.2f} / {res['expected']:.2f} = {res['alpha']:.2f}")
    print("\n  Better than random, too weak to treat these labels as a stable release signal.")
    print("  The next step is not to worship the number: look at outputs 4 and 5.")
    print("  Were they ambiguous? Was the policy unclear? Or did one reviewer see a problem the others missed?")


def ordinal_scale() -> None:
    print("\n" + "=" * 78 + "\nA 0-10 SCALE: 7 vs 8 IS NOT 2 vs 9\n" + "=" * 78)
    close = [[7, 8, 7], [8, 7, 8], [3, 2, 3], [9, 8, 9], [5, 6, 5], [2, 3, 2]]
    far = [[7, 2, 7], [8, 9, 1], [3, 9, 3], [9, 8, 9], [5, 6, 5], [2, 3, 2]]
    for name, data in (("small misses (7 vs 8)", close), ("big misses (2 vs 9)", far)):
        nom = krippendorff_alpha(data, "nominal")["alpha"]
        ordi = krippendorff_alpha(data, "ordinal")["alpha"]
        itv = krippendorff_alpha(data, "interval")["alpha"]
        print(f"  {name:22} nominal {nom:5.2f}   ordinal {ordi:5.2f}   interval {itv:5.2f}")
    print("  Nominal alpha treats every mismatch the same, so 7 vs 8 counts as a full disagreement.")
    print("  The ordinal and interval versions weigh the distance.")


def real_scores() -> None:
    rows = load_jsonl(HERE / "data" / "reviews.jsonl")
    print("\n" + "=" * 78 + "\n100 ANSWERS, 3 REVIEWERS, 0-10 SCORES, SOME RATINGS MISSING\n" + "=" * 78)
    for g in ("v1", "v2"):
        sub = [r for r in rows if r["guideline"] == g]
        units = [list(r["scores"].values()) for r in sub]
        missing = sum(v is None for u in units for v in u)
        labels = krippendorff_alpha([list(r["labels"].values()) for r in sub], "nominal")["alpha"]
        ordi = krippendorff_alpha(units, "ordinal")["alpha"]
        print(f"  guideline {g}: {missing} missing ratings; alpha on labels {labels:.2f}, on 0-10 scores (ordinal) {ordi:.2f}")
    print("  No need to throw away items with a missing rating: alpha uses every pair that exists.")


def main() -> None:
    post_example()
    ordinal_scale()
    real_scores()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
