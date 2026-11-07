"""
too_good_agreement.py: when agreement is too beautiful.

Run:  python too_good_agreement.py
      python too_good_agreement.py --min-agreement 0.97 --max-gap 30

Almost 100% agreement across several accounts, with labels arriving at nearly the same moment,
can mean coordinated fraud: accounts sharing one answer sheet to get paid fast, without caring
whether it is right.

12 labeling accounts, 200 items each, with timestamps and a hidden gold answer per item.
The script:
  1. finds pairs of accounts that agree suspiciously often
  2. checks how close in time their labels arrived
  3. compares with gold: high agreement with each other is not accuracy
Then the ibuprofen example: two honest labelers, only one of whom measures the risk that matters.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from statistics import median
from typing import Dict, List

from agreement import load_json, load_jsonl

HERE = Path(__file__).parent


def by_account(rows: List[Dict]) -> Dict[str, Dict[str, Dict]]:
    out: Dict[str, Dict[str, Dict]] = defaultdict(dict)
    for r in rows:
        out[r["account"]][r["item"]] = r
    return out


def suspicious(acc: Dict[str, Dict[str, Dict]], min_agree: float, max_gap: float) -> List[tuple]:
    found = []
    for a, b in combinations(sorted(acc), 2):
        items = sorted(set(acc[a]) & set(acc[b]))
        agree = sum(acc[a][i]["label"] == acc[b][i]["label"] for i in items) / len(items)
        gaps = [abs((datetime.fromisoformat(acc[a][i]["submitted_at"]) -
                     datetime.fromisoformat(acc[b][i]["submitted_at"])).total_seconds()) for i in items]
        found.append((a, b, agree, median(gaps), agree >= min_agree and median(gaps) <= max_gap))
    return found


def main() -> None:
    ap = argparse.ArgumentParser(description="Flag agreement that is too good to be true.")
    ap.add_argument("--min-agreement", type=float, default=0.97)
    ap.add_argument("--max-gap", type=float, default=30, help="median seconds between the two accounts' labels")
    a = ap.parse_args()
    rows = load_jsonl(HERE / "data" / "label_log.jsonl")
    acc = by_account(rows)

    pairs = suspicious(acc, a.min_agreement, a.max_gap)
    print("=" * 78 + f"\n1-2. ACCOUNT PAIRS: AGREEMENT AND TIMING ({len(pairs)} pairs)\n" + "=" * 78)
    normal = [p for p in pairs if not p[4]]
    print(f"  typical pair: agreement {median(p[2] for p in normal):.0%}, "
          f"labels {median(p[3] for p in normal) / 60:.0f} min apart (median)")
    flagged = [p for p in pairs if p[4]]
    print(f"  flagged (agreement >= {a.min_agreement:.0%} and labels <= {a.max_gap:.0f} s apart): {len(flagged)}")
    for x, y, agree, gap, _ in flagged:
        print(f"    {x} + {y}: agreement {agree:.1%}, labels {gap:.0f} s apart")
    ring = sorted({p[0] for p in flagged} | {p[1] for p in flagged})

    print("\n" + "=" * 78 + "\n3. AGREEING WITH EACH OTHER IS NOT BEING RIGHT\n" + "=" * 78)
    for name in sorted(acc):
        items = acc[name].values()
        accuracy = sum(r["label"] == r["gold"] for r in items) / len(items)
        mark = "  <- flagged" if name in ring else ""
        print(f"  {name}: {accuracy:5.0%} correct against gold{mark}")
    if ring:
        print(f"\n  {', '.join(ring)}: perfect agreement with each other, the lowest accuracy against gold.")
        print("  Remove their labels, re-label the items, and look at the incentive: pay per label rewards speed.")
    print("  Every part of the labeling process (people, vendor, workflow, incentives) deserves healthy skepticism.")

    ib = load_json(HERE / "data" / "ibuprofen_pages.json")
    print("\n" + "=" * 78 + f"\nTWO HONEST LABELERS: \"{ib['query']}\"\n" + "=" * 78)
    print(f"  {'page':7} {'cheap generalist (clarity)':>27} {'medical reviewer':>18}")
    for p in ib["pages"]:
        safe = p["mentions_interactions"] and p["refers_to_doctor_or_pharmacist"]
        med = "good" if safe else "too general, risky"
        print(f"  {p['id']:7} {p['clarity']:>27} {med:>18}   {p['summary']}")
    print("  The generalist rewards the clearest wording. The medical reviewer notices that page-A skips")
    print("  interactions and contraindications and never sends you to a doctor or pharmacist.")
    print("  Both did the job; only one measured the risk that matters.")
    print("\n  Only when the human measurement system is visible and checked is it worth automating.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
