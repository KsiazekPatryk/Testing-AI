"""
start_simple.py: agreement between raters, without advanced statistics.

Run:  python start_simple.py
      python start_simple.py --guideline v2

Three reviewers label the same 100 chatbot answers as acceptable / needs_fix / risky.
  1. how often all three agree, how often two do, how often nobody does
  2. where the disagreement lives: FAQ, tone, safety
  3. the cases to bring to the discussion, which is where the value is
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from agreement import agreement_pattern, load_jsonl

HERE = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Count agreement among three reviewers.")
    ap.add_argument("--guideline", choices=("v1", "v2"), default="v1")
    a = ap.parse_args()
    rows = [r for r in load_jsonl(HERE / "data" / "reviews.jsonl") if r["guideline"] == a.guideline]

    print("=" * 78 + f"\n1. THREE REVIEWERS, {len(rows)} ANSWERS (guideline {a.guideline})\n" + "=" * 78)
    pat = Counter(agreement_pattern(list(r["labels"].values())) for r in rows)
    for k, name in (("all", "all three agree"), ("two", "two agree"), ("none", "nobody agrees")):
        print(f"  {name:16} {pat[k]:>4}  {'#' * pat[k]}")

    print("\n" + "=" * 78 + "\n2. WHERE THE DISAGREEMENT LIVES\n" + "=" * 78)
    print(f"  {'category':9} {'answers':>8} {'all agree':>10} {'two':>5} {'nobody':>7}")
    for cat in ("faq", "tone", "safety"):
        sub = [r for r in rows if r["category"] == cat]
        c = Counter(agreement_pattern(list(r["labels"].values())) for r in sub)
        print(f"  {cat:9} {len(sub):>8} {c['all'] / len(sub):>10.0%} {c['two']:>5} {c['none']:>7}")
    print("  Simple FAQ questions: mostly unanimous, never a three-way split.")
    print("  Tone and safety: that is where the work is.")
    print("  An overall average would hide exactly the part that needs attention.")

    print("\n" + "=" * 78 + "\n3. BRING THESE TO THE DISCUSSION\n" + "=" * 78)
    split = [r for r in rows if agreement_pattern(list(r["labels"].values())) == "none"]
    split += [r for r in rows if agreement_pattern(list(r["labels"].values())) == "two" and r["category"] == "safety"][:4]
    for r in split[:8]:
        labs = ", ".join(f"{k} {v}" for k, v in r["labels"].items())
        print(f"  {r['item']} ({r['category']:6}) {labs}")
    print("\n  For each one, ask:")
    print("    unclear policy?             -> clarify the policy")
    print("    unclear rubric?             -> fix the rubric, add anchor examples")
    print("    disputes only at the edges? -> write an escalation rule for borderline cases")
    if a.guideline == "v1":
        print("\n  Then compare with the revised guideline: python start_simple.py --guideline v2")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
