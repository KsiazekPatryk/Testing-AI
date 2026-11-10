"""
raters_first.py: raters are part of the product. Define the human system first, then automate.

Run:  python raters_first.py

Before a judge is compared with "the humans", check the humans:
  1. how well do two trained reviewers agree with each other, per segment?
  2. where they disagree, is it a preference, an unclear rubric, or a missing expertise?
  3. is the judge at least as close to the trusted reviewer as a second human is?
     Where it is not, do not automate that segment yet.
"""

from __future__ import annotations

import sys
from pathlib import Path

from judge import judge_v2
from metrics import cohen_kappa, load_jsonl, pass_agreement, within

HERE = Path(__file__).parent
SEGMENTS = ("general", "refunds", "privacy", "medical")


def main() -> None:
    rows = load_jsonl(HERE / "data" / "replies.jsonl")
    for r in rows:
        r["v2"] = judge_v2(r["reply"], context=r["question"])[0]

    print("=" * 78 + "\n1. THE HUMAN SYSTEM: TWO TRAINED REVIEWERS, SAME RUBRIC\n" + "=" * 78)
    print(f"  {'segment':9} {'within 1 pt':>12} {'pass/fail kappa':>16}")
    for seg in SEGMENTS + ("all",):
        sub = rows if seg == "all" else [r for r in rows if r["segment"] == seg]
        h, h2 = [r["human"] for r in sub], [r["human_2"] for r in sub]
        k = cohen_kappa([x >= 7 for x in h], [x >= 7 for x in h2])
        print(f"  {seg:9} {within(h, h2):>12.0%} {k:>16.2f}")
    print("  Written down before automating: who the reviewers are, their training, the rubric version,")
    print("  the arbitration rule. That is the reference the judge will be measured against.")

    print("\n" + "=" * 78 + "\n2. WHERE THE HUMANS DISAGREE\n" + "=" * 78)
    split = [r for r in rows if abs(r["human"] - r["human_2"]) >= 2]
    kinds = {}
    for r in split:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"  {len(split)} replies with a gap of 2+ points: " + ", ".join(f"{k} {v}" for k, v in kinds.items()))
    if set(kinds) == {"vague"}:
        print("  All of them are 'vague' replies: one reviewer finds a short answer fine, the other wants a")
        print("  next step. A preference to settle in the rubric before any judge learns from these labels.")
    print("  And check expertise: the medical segment is reviewed by someone who knows medication handling,")
    print("  not by whoever is free.")

    print("\n" + "=" * 78 + "\n3. ONLY THEN: IS THE JUDGE AS CLOSE AS A SECOND HUMAN?\n" + "=" * 78)
    print(f"  {'segment':9} {'2nd human pass/fail':>20} {'judge pass/fail':>16}   verdict")
    for seg in SEGMENTS:
        sub = [r for r in rows if r["segment"] == seg]
        h = [r["human"] for r in sub]
        a2 = pass_agreement(h, [r["human_2"] for r in sub])
        aj = pass_agreement(h, [r["v2"] for r in sub])
        verdict = "judge can scale this" if aj >= a2 - 0.02 else "not yet: calibrate or keep humans"
        if seg == "medical":
            verdict += " (high risk: a human still decides)"
        print(f"  {seg:9} {a2:>20.0%} {aj:>16.0%}   {verdict}")
    print("\n  A judge can scale the review. It should not own the definition of quality,")
    print("  and it should not own the release decision.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
