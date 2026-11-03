"""
blind_review.py: if the reviewer knows which answer is new, the new one wins.

Run:  python blind_review.py

60 cases. The old and the new version have the SAME true quality (that is how the data was made).
  unblinded: the reviewer sees "NEW MODEL" and the new answer is always shown first
  blinded:   the source is hidden and the order is random

Then: how the two biases (knowing the source, position) hide inside the unblinded result.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, List

from agreement import load_jsonl, mean

HERE = Path(__file__).parent


def diffs(rows: List[Dict], cond: str) -> List[int]:
    cases: Dict[str, Dict[str, int]] = {}
    for r in rows:
        if r["condition"] == cond:
            cases.setdefault(r["case"], {})[r["version"]] = r["score"]
    return [c["new"] - c["old"] for c in cases.values()]


def wins(d: List[int]) -> str:
    w, l, t = sum(x > 0 for x in d), sum(x < 0 for x in d), sum(x == 0 for x in d)
    return f"new wins {w}, old wins {l}, ties {t}"


def blind_order(case_ids: List[str], seed: int = 0) -> List[Dict]:
    """What a blinded review sheet looks like: neutral names, random order, the key kept separately."""
    rng = random.Random(seed)
    sheet = []
    for c in case_ids:
        pair = ["old", "new"]
        rng.shuffle(pair)
        sheet.append({"case": c, "answer_1": pair[0], "answer_2": pair[1]})
    return sheet


def main() -> None:
    rows = load_jsonl(HERE / "data" / "blind_review.jsonl")
    print("=" * 78 + "\nTHE SAME ANSWERS, REVIEWED TWICE\n" + "=" * 78)
    for cond in ("unblinded", "blinded"):
        d = diffs(rows, cond)
        print(f"  {cond:10} new - old = {mean(d):+.2f} points   ({wins(d)})")

    print("\n" + "=" * 78 + "\nWHERE THE UNBLINDED 'WIN' COMES FROM\n" + "=" * 78)
    blinded = [r for r in rows if r["condition"] == "blinded"]
    first = mean([r["score"] for r in blinded if r["shown_first"]])
    second = mean([r["score"] for r in blinded if not r["shown_first"]])
    print(f"  Position: in the blinded round, the answer shown first gets {first - second:+.2f} points on average.")
    print("  Randomizing the order spreads that bonus evenly over both versions.")
    print("  Unblinded, the new answer always went first, AND the reviewer knew it was new.")
    print("  Neither is bad will. Both are measurement error, and both favor the version you hope wins.")

    print("\n" + "=" * 78 + "\nHOW TO RUN A BLIND REVIEW\n" + "=" * 78)
    sheet = blind_order(sorted({r["case"] for r in rows})[:4])
    print("  The reviewer sees 'answer 1' and 'answer 2'. The key stays with whoever runs the evaluation:")
    for s in sheet:
        print(f"    {s['case']}: answer 1 = {s['answer_1']:3}, answer 2 = {s['answer_2']:3}   (hidden from the reviewer)")
    print("  Also hide: model names, vendor names, latency, the date the answer was produced.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
