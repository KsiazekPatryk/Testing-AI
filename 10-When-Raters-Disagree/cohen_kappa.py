"""
cohen_kappa.py: how much agreement is left after you subtract chance?

Run:  python cohen_kappa.py
      python cohen_kappa.py --table 50 30 10 10

Two reviewers, A and B, label 100 chatbot answers as acceptable or risky.
The post's example: both acceptable 50, both risky 30, A acceptable / B risky 10, A risky / B acceptable 10.

  kappa = (observed agreement - chance agreement) / (1 - chance agreement)

Then: why kappa is sensitive to how common each label is, and what 0.58 means for low-risk
style checks vs privacy, medicine or finance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agreement import cohen_kappa, describe, kappa_from_table, load_jsonl

HERE = Path(__file__).parent


def by_hand(both_yes: int, both_no: int, a_yes: int, b_yes: int) -> float:
    n = both_yes + both_no + a_yes + b_yes
    res = kappa_from_table(both_yes, both_no, a_yes, b_yes)
    pa = (both_yes + a_yes) / n
    pb = (both_yes + b_yes) / n
    print("=" * 78 + "\nTHE POST'S EXAMPLE, STEP BY STEP\n" + "=" * 78)
    print(f"                      B acceptable   B risky")
    print(f"  A acceptable        {both_yes:>12}   {a_yes:>7}")
    print(f"  A risky             {b_yes:>12}   {both_no:>7}")
    print(f"\n  observed agreement = ({both_yes} + {both_no}) / {n} = {res['observed']:.2f}")
    print(f"  A says 'acceptable' {pa:.0%} of the time, B {pb:.0%}")
    print(f"  chance agreement   = {pa:.2f} x {pb:.2f} + {1 - pa:.2f} x {1 - pb:.2f} = {res['chance']:.2f}")
    print(f"  kappa              = ({res['observed']:.2f} - {res['chance']:.2f}) / (1 - {res['chance']:.2f}) "
          f"= {res['kappa']:.2f}   ({describe(res['kappa'])})")
    print(f"\n  '{res['observed']:.0%} agreement' sounds good. Kappa {res['kappa']:.2f} is the sober version:")
    print("  better than chance, but not a well-calibrated system.")
    return res["kappa"]


def risk_reading(k: float) -> None:
    print("\n" + "=" * 78 + "\nIS IT ENOUGH? DEPENDS ON WHAT THE LABELS DECIDE\n" + "=" * 78)
    rules = [("low-risk style check, spot reviews", 0.4), ("release gate for support answers", 0.7),
             ("privacy, medicine, finance", 0.8)]
    for use, need in rules:
        ok = "enough" if k >= need else "work on the rubric and the training"
        print(f"  {use:38} needs ~{need:.1f}: {ok}")
    print("  (These thresholds are a team decision, not a law. Write them down before measuring.)")


def prevalence() -> None:
    print("\n" + "=" * 78 + "\nTHE PREVALENCE TRAP\n" + "=" * 78)
    print("  100 answers, almost all of them 'acceptable'. Each reviewer flags 4 as risky,")
    print("  but they flag the same answer only once.")
    res = kappa_from_table(93, 1, 3, 3)
    print(f"  raw agreement {res['observed']:.0%}, chance agreement {res['chance']:.0%}, kappa {res['kappa']:.2f}")
    print("  Raw agreement looks excellent, kappa stays modest. That is not a flaw in the statistic:")
    print("  it warns that the set may not contain enough hard cases. Add hard cases before you trust it.")


def on_real_data() -> None:
    rows = load_jsonl(HERE / "data" / "reviews.jsonl")
    print("\n" + "=" * 78 + "\nON THE 100 ANSWERS (ola vs piotr), BEFORE AND AFTER THE NEW GUIDELINE\n" + "=" * 78)
    for g in ("v1", "v2"):
        sub = [r for r in rows if r["guideline"] == g]
        res = cohen_kappa([r["labels"]["ola"] for r in sub], [r["labels"]["piotr"] for r in sub])
        print(f"  {g}: raw agreement {res['observed']:.0%}, chance {res['chance']:.0%}, kappa {res['kappa']:.2f} "
              f"({describe(res['kappa'])})")
        for cat in ("faq", "safety"):
            s = [r for r in sub if r["category"] == cat]
            rc = cohen_kappa([r["labels"]["ola"] for r in s], [r["labels"]["piotr"] for r in s])
            print(f"      {cat:7} raw {rc['observed']:.0%}, kappa {rc['kappa']:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Cohen's kappa, step by step.")
    ap.add_argument("--table", type=int, nargs=4, metavar=("BOTH_OK", "BOTH_RISKY", "A_OK_B_RISKY", "A_RISKY_B_OK"),
                    default=(50, 30, 10, 10))
    a = ap.parse_args()
    k = by_hand(*a.table)
    risk_reading(k)
    prevalence()
    on_real_data()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
