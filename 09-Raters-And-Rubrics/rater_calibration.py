"""
rater_calibration.py: a rater is an instrument. Calibrate it before you count what it says.

Run:  python rater_calibration.py
      python rater_calibration.py --pass-at 8

Three reviewers score the same 40 support answers twice:
  before: "Rate the quality from 1 to 10" (the vague instruction)
  after:  the anchored rubric (data/rubric_support.json) and one calibration session

The script shows:
  1. how far apart the reviewers are before calibration, and on which items
  2. agreement beyond chance (kappa) before and after
  3. overlap and arbitration: what happens to the items where reviewers still disagree
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Dict, List

from agreement import cohen_kappa, describe_kappa, fleiss_kappa, load_jsonl, mean, weighted_kappa

HERE = Path(__file__).parent
RATERS = ("anna", "ben", "chen")

# Decided BEFORE the labels are counted. Each rule says what happens to a disagreement.
ARBITRATION = [
    ("all agree", "the label counts"),
    ("2 of 3 agree, spread of scores <= 2", "majority label counts"),
    ("2 of 3 agree, spread of scores >= 3", "senior reviewer decides, the item goes to the next calibration session"),
    ("used in a release gate and not unanimous", "labeled 'uncertain': it cannot pass the gate on its own"),
]


def by_rater(rows: List[Dict], rnd: str) -> Dict[str, List[int]]:
    return {r: [x["score"] for x in rows if x["round"] == rnd and x["rater"] == r] for r in RATERS}


def show_round(scores: Dict[str, List[int]], items: List[str], title: str, pass_at: int) -> float:
    print("=" * 78 + f"\n{title}\n" + "=" * 78)
    n = len(items)
    print(f"  {'rater':6} {'mean':>5} {'passes (>= ' + str(pass_at) + ')':>16}")
    for r in RATERS:
        p = sum(s >= pass_at for s in scores[r])
        print(f"  {r:6} {mean(scores[r]):5.1f} {p:>9} / {n} ({p / n:.0%})")
    labels = {r: ["pass" if s >= pass_at else "fail" for s in scores[r]] for r in RATERS}
    print("\n  agreement on the 0-10 scale (weighted kappa):")
    for a, b in (("anna", "ben"), ("anna", "chen"), ("ben", "chen")):
        k = weighted_kappa(scores[a], scores[b])
        print(f"    {a + ' vs ' + b:13} {k:5.2f}  {describe_kappa(k)}")
    fk = fleiss_kappa(list(zip(*labels.values())))
    print(f"  agreement on pass/fail, all three (Fleiss' kappa): {fk:.2f}  {describe_kappa(fk)}")
    return fk


def disputed(scores: Dict[str, List[int]], items: List[str], top: int = 5) -> None:
    spread = sorted(((max(v) - min(v), items[i], v) for i, v in enumerate(zip(*scores.values()))), reverse=True)
    print(f"\n  Bring these to the calibration session (largest spread between reviewers):")
    for s, item, v in spread[:top]:
        print(f"    {item}: anna {v[0]:2}, ben {v[1]:2}, chen {v[2]:2}   spread {s}")
    print("  Reviewers explain their reasoning, the instruction gets anchors, and only then do labels count.")


def arbitrate(scores: Dict[str, List[int]], items: List[str], pass_at: int) -> None:
    print("\n" + "=" * 78 + "\nOVERLAP AND ARBITRATION (after calibration)\n" + "=" * 78)
    print("  The rules, written down before counting:")
    for cond, action in ARBITRATION:
        print(f"    - {cond}: {action}")
    outcome = {"unanimous": 0, "majority": 0, "senior": 0}
    for i, v in enumerate(zip(*scores.values())):
        votes = [s >= pass_at for s in v]
        if all(votes) or not any(votes):
            outcome["unanimous"] += 1
        elif max(v) - min(v) <= 2:
            outcome["majority"] += 1
        else:
            outcome["senior"] += 1
    n = len(items)
    print(f"\n  {outcome['unanimous']} of {n} items unanimous, {outcome['majority']} decided by majority, "
          f"{outcome['senior']} sent to a senior reviewer.")
    print(f"  {n - outcome['unanimous']} items would be 'uncertain' if they were part of a release gate.")
    print("  Without overlap you would never see those items: one person's label would just look like truth.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate raters before counting their labels.")
    ap.add_argument("--pass-at", type=int, default=7, help="score that counts as a pass (default 7)")
    a = ap.parse_args()
    rows = load_jsonl(HERE / "data" / "calibration.jsonl")
    items = sorted({r["item"] for r in rows})
    before, after = by_rater(rows, "before"), by_rater(rows, "after")

    k0 = show_round(before, items, "BEFORE: 'Rate the quality from 1 to 10'", a.pass_at)
    disputed(before, items)
    print()
    k1 = show_round(after, items, "AFTER: anchored rubric + one calibration session", a.pass_at)

    sd_before = statistics.pstdev([mean(v) for v in before.values()])
    sd_after = statistics.pstdev([mean(v) for v in after.values()])
    print(f"\n  Spread of the reviewers' means: {sd_before:.2f} -> {sd_after:.2f}. "
          f"Pass/fail kappa: {k0:.2f} -> {k1:.2f}.")
    print("  Same answers, same people. Only the instrument changed.")
    arbitrate(after, items, a.pass_at)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
