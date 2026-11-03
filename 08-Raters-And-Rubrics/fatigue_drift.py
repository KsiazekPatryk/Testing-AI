"""
fatigue_drift.py: long sessions lower label quality. Gold items catch it.

Run:  python fatigue_drift.py
      python fatigue_drift.py --block 30 --min-gold 0.8

Three reviewers, 150 items each. Every 5th item is a gold item: an answer whose correct label
is known in advance (an attention check). The reviewers do not know which items are gold.

The script tracks, per block of the session:
  - accuracy on gold items
  - the share of items labeled "pass" (drift: a tired reviewer starts passing everything)
and flags the labels that should not be counted as they are.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from agreement import load_jsonl

HERE = Path(__file__).parent


def blocks(rows: List[Dict], size: int):
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def report(rater: str, rows: List[Dict], size: int, min_gold: float) -> List[int]:
    print(f"\n  {rater}")
    print(f"    {'items':>9}  {'minutes':>9}  {'gold correct':>12}  {'pass rate':>9}")
    flagged = []
    for b in blocks(rows, size):
        gold = [r for r in b if r["is_gold"]]
        acc = sum(r["label"] == r["gold_label"] for r in gold) / len(gold)
        pass_rate = sum(r["label"] == "pass" for r in b) / len(b)
        flag = acc < min_gold
        if flag:
            flagged.append(b[0]["position"])
        print(f"    {b[0]['position']:>3}-{b[-1]['position']:<5}  {b[0]['minute']:>4.0f}-{b[-1]['minute']:<4.0f}"
              f"  {sum(r['label'] == r['gold_label'] for r in gold):>5} / {len(gold):<5}  {pass_rate:>8.0%}"
              f"{'   <- below ' + format(min_gold, '.0%') + ' on gold' if flag else ''}")
    return flagged


def main() -> None:
    ap = argparse.ArgumentParser(description="Detect fatigue and drift with gold items.")
    ap.add_argument("--block", type=int, default=30, help="items per block (default 30)")
    ap.add_argument("--min-gold", type=float, default=0.8, help="minimum gold accuracy (default 0.8)")
    a = ap.parse_args()
    rows = load_jsonl(HERE / "data" / "session_log.jsonl")
    print("=" * 78 + "\nGOLD ITEMS AND PASS RATE ACROSS EACH SESSION\n" + "=" * 78)
    summary = {}
    for rater in ("anna", "ben", "chen"):
        own = sorted((r for r in rows if r["rater"] == rater), key=lambda r: r["position"])
        summary[rater] = report(rater, own, a.block, a.min_gold)

    print("\n" + "=" * 78 + "\nWHAT TO DO WITH IT\n" + "=" * 78)
    for rater, flagged in summary.items():
        if flagged:
            start = flagged[0]
            print(f"  {rater}: from item {start} on, gold accuracy is below {a.min_gold:.0%} and the pass rate climbs.")
            print(f"    Do not count items {start}-150 as they are: re-label them in a fresh session or with overlap.")
            print("    Next time: shorter sessions, breaks, and rotation off emotionally heavy content.")
        else:
            print(f"  {rater}: stable over the whole session.")
    print("\n  Note: the pass rate alone would not prove anything (the items differ between blocks).")
    print("  Gold items do, because their correct answer is known.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
