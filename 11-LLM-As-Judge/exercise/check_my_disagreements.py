"""
check_my_disagreements.py: the exercise from the post.

"Find ten cases where a human and the LLM judge (or two raters) gave different scores.
 Do not average them. Put each case into one of five categories:
   ambiguous rubric, missing context, legitimate preference difference, judge error,
   rater expertise gap.
 If most cases land in the first category, the problem is the definition of quality,
 not the model and not the judge."

Run:  python exercise/check_my_disagreements.py
      python exercise/check_my_disagreements.py path/to/your_cases.csv

The CSV needs: human_score, judge_score, category (and optionally id, case, note).
Categories: ambiguous_rubric, missing_context, preference, judge_error, expertise_gap.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_FILE = HERE / "my_disagreements.csv"
CATEGORIES = {
    "ambiguous_rubric": "rewrite the rubric: anchors, dimensions, what 'complete' and 'correct' mean",
    "missing_context": "give the judge what the human saw: the customer's message, the policy, the order",
    "preference": "both are acceptable: settle the preference in the rubric, or design for both groups",
    "judge_error": "fix the judge: examples in the prompt, blocker checks, a segment correction",
    "expertise_gap": "route this kind of case to someone with the expertise, and re-label it",
}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    h = [float(r["human_score"]) for r in rows]
    j = [float(r["judge_score"]) for r in rows]

    print("=" * 78 + f"\n{path.name}: {n} disagreements\n" + "=" * 78)
    print(f"  The tempting summary: human mean {sum(h) / n:.1f}, judge mean {sum(j) / n:.1f}.")
    print("  Do not average them: the gaps go in both directions, and each one has a different cause.\n")
    tags = Counter()
    for r, x, y in zip(rows, h, j):
        cat = (r.get("category") or "").strip().lower()
        if cat not in CATEGORIES:
            cat = "?"
        tags[cat] += 1
        label = r.get("case") or r.get("id", "")
        print(f"  [{cat:16}] human {x:>4.0f}  judge {y:>4.0f}  {label}")

    print("\n  The split:")
    for cat, action in CATEGORIES.items():
        if tags[cat]:
            print(f"    {cat:16} {tags[cat]:>2}   {action}")
    if tags["?"]:
        print(f"    {'?':16} {tags['?']:>2}   not categorized yet: pick one of the five")

    top, count = max(((c, tags[c]) for c in CATEGORIES), key=lambda t: t[1])
    print()
    if tags["ambiguous_rubric"] > n / 2:
        print(f"  Most cases ({tags['ambiguous_rubric']} of {n}) are an ambiguous rubric.")
        print("  The problem is the definition of quality, not the model and not the judge.")
        print("  Fix the rubric first; calibrating a judge against an unclear definition only scales the confusion.")
    else:
        print(f"  The largest group is {top} ({count} of {n}): start there.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
