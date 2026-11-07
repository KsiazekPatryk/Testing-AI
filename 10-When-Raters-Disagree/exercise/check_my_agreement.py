"""
check_my_agreement.py: the exercise from the post.

"Take 20 examples rated by two people (or by a human and an LLM judge) and compute two things:
   - the raw agreement rate,
   - Cohen's kappa (a spreadsheet and the formula from this post are enough).
 Then read every disagreement and write one word next to each: 'rubric', 'policy',
 'preference' or 'error'. That split will tell you more than the number itself."

Run:  python exercise/check_my_agreement.py
      python exercise/check_my_agreement.py path/to/your_pairs.csv

The CSV needs the columns rater_a, rater_b and reason (and optionally id, question, note).
Any labels work: acceptable/risky, pass/fail, 0-10. Leave 'reason' empty where the raters agree.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from agreement import cohen_kappa, describe, load_csv  # noqa: E402

DEFAULT_FILE = HERE / "my_pairs.csv"
REASONS = {
    "rubric": "the rubric does not separate the dimensions: fix the rubric, add anchor examples",
    "policy": "the policy does not answer the question: clarify the policy",
    "preference": "both answers are acceptable, the raters value different things: a product design signal",
    "error": "one rater missed something: retrain, or recalibrate the judge; check if it is a blocker",
}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    rows = load_csv(path)
    a = [r["rater_a"].strip() for r in rows]
    b = [r["rater_b"].strip() for r in rows]
    res = cohen_kappa(a, b)
    n = len(rows)
    agree = sum(x == y for x, y in zip(a, b))

    print("=" * 78 + f"\n{path.name}: {n} examples\n" + "=" * 78)
    labels = sorted(set(a) | set(b))
    width = max(len(x) for x in labels) + 2
    print(" " * (width + 2) + "".join(f"{'B ' + l:>{width + 2}}" for l in labels))
    for la in labels:
        print(f"  {'A ' + la:{width}}" + "".join(
            f"{sum(x == la and y == lb for x, y in zip(a, b)):>{width + 2}}" for lb in labels))
    print(f"\n  raw agreement:     {agree} / {n} = {res['observed']:.0%}")
    print(f"  chance agreement:  {res['chance']:.2f}")
    print(f"  Cohen's kappa:     ({res['observed']:.2f} - {res['chance']:.2f}) / (1 - {res['chance']:.2f}) "
          f"= {res['kappa']:.2f}  ({describe(res['kappa'])})")
    if n < 20:
        print(f"  Note: {n} examples is a small sample; treat the numbers as a rough signal.")

    print("\n" + "=" * 78 + f"\nTHE {n - agree} DISAGREEMENTS, ONE WORD EACH\n" + "=" * 78)
    tags = Counter()
    untagged = []
    for r, x, y in zip(rows, a, b):
        if x == y:
            continue
        reason = (r.get("reason") or "").strip().lower()
        if reason not in REASONS:
            untagged.append(r)
            reason = "?"
        tags[reason] += 1
        q = r.get("question") or r.get("id", "")
        note = f"   ({r['note']})" if r.get("note") else ""
        print(f"  [{reason:10}] {q}: A {x}, B {y}{note}")

    print("\n  The split:")
    for reason, action in REASONS.items():
        if tags[reason]:
            print(f"    {reason:10} {tags[reason]:>2}   {action}")
    if untagged:
        print(f"    {'?':10} {len(untagged):>2}   not tagged yet: write rubric, policy, preference or error")
    harmful = tags["rubric"] + tags["policy"] + tags["error"]
    print(f"\n  harmful (rubric, policy, error): {harmful} of {n - agree}. Fix the measurement.")
    print(f"  healthy (preference):            {tags['preference']} of {n - agree}. Use them to design the product.")
    print("  This split says more than the kappa on its own.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
