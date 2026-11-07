"""
why_not_whether.py: raw agreement says "whether". Good measurement says "why".

Run:  python why_not_whether.py

A customer writes: "My child drank spoiled milk from yesterday's delivery. What should I do?"
Three reviewers score the same answer 9, 5 and 2. Each is right about something different:
tone, escalation, medical-sounding advice with no basis in policy.

Round 2 splits the one score into dimensions and names the blockers. The reviewers now agree,
and the answer fails, which a 5.3 average would never have said.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean, pstdev

from agreement import load_json

HERE = Path(__file__).parent


def main() -> None:
    case = load_json(HERE / "data" / "milk_case.json")
    print(f"Message: \"{case['message']}\"\nAnswer:  \"{case['answer']}\"\n")

    r1 = case["round_1"]
    print("=" * 78 + f"\nROUND 1: \"{r1['guideline']}\"\n" + "=" * 78)
    scores = [r["score"] for r in r1["ratings"]]
    for r in r1["ratings"]:
        print(f"  {r['rater']}: {r['score']:>2}   {r['reason']}")
    print(f"\n  mean {mean(scores):.1f}, spread (sd) {pstdev(scores):.1f}")
    print("  The average says 'mediocre'. The spread says the reviewers measured three different things:")
    print("  tone, escalation, and medical advice. This is not noise. It is a rubric that does not")
    print("  separate them, and has no blockers.")

    r2 = case["round_2"]
    print("\n" + "=" * 78 + f"\nROUND 2: \"{r2['guideline']}\"\n" + "=" * 78)
    for dim in r2["dimensions"]:
        vals = [r[dim] for r in r2["ratings"]]
        agree = "all agree" if len(set(vals)) == 1 else "disagree"
        print(f"  {dim:26} {', '.join(vals):30} {agree}")
    blockers = sorted({b for r in r2["ratings"] for b in r["blockers"]})
    print(f"  blockers: {', '.join(blockers)}")
    print("\n  Verdict: FAIL. The tone is good, and that does not matter here.")
    print("  Calibrate the reviewers and decide which errors are blockers BEFORE labels like these")
    print("  go into training data. A 5.3 would have taught a model that this answer is 'okay'.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
