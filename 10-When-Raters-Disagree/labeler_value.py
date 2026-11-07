"""
labeler_value.py: a labeler's value is not clicks per hour.

Run:  python labeler_value.py

Labelers create the ground truth that many evaluations depend on. Their value should be measured,
not assumed. Five questions, answered on 100 answers labeled by three reviewers, with an expert
arbitration label and what happened later (did the customer complain?):

  1. Do the labels predict outcomes?
  2. Are there systematic biases? (strict, middle of the scale, missed policy details)
  3. Where does the disagreement live?
  4. Does an extra rater add anything?
  5. Test the guideline itself: did splitting a vague label into two dimensions help?
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from agreement import cohen_kappa, krippendorff_alpha, load_jsonl

HERE = Path(__file__).parent
RATERS = ("ola", "piotr", "kasia")


def header(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def majority(labels: List[str]) -> Optional[str]:
    top, n = Counter(labels).most_common(1)[0]
    return top if n > len(labels) / 2 else None


def predicts(rows: List[Dict]) -> None:
    header("1. DO THE LABELS PREDICT WHAT HAPPENED LATER?")
    complaints = [r for r in rows if r["later_complaint"]]
    print(f"  {len(complaints)} of {len(rows)} answers later led to a complaint. For each source of labels:")
    print(f"  {'source':8} {'flagged (not acceptable)':>25} {'complaints it had called acceptable':>37}")
    sources = [(r, (lambda x, r=r: x["labels"][r])) for r in RATERS] + [("expert", lambda x: x["expert_label"])]
    for name, f in sources:
        flagged = sum(f(r) != "acceptable" for r in rows)
        missed = sum(f(r) == "acceptable" for r in complaints)
        print(f"  {name:8} {flagged:>25} {missed:>30} of {len(complaints)}")
    print("  The expert flags the fewest answers and still misses few complaints.")
    print("  piotr misses none, but only by flagging far more: every flag costs a review.")
    print("  kasia flags as few as the expert and misses twice as many complaints.")
    print("  Labels that predict outcomes are worth more than labels produced quickly.")


def biases(rows: List[Dict]) -> None:
    header("2. SYSTEMATIC BIASES THAT AN AGGREGATE HIDES")
    print(f"  {'rater':6} {'mean score':>10} {'scores 5-6':>11} {'risky safety answers called acceptable':>40}")
    risky_safety = [r for r in rows if r["category"] == "safety" and r["expert_label"] == "risky"]
    for rater in RATERS:
        sc = [r["scores"][rater] for r in rows if r["scores"][rater] is not None]
        mid = sum(5 <= s <= 6 for s in sc) / len(sc)
        miss = sum(r["labels"][rater] == "acceptable" for r in risky_safety)
        print(f"  {rater:6} {mean(sc):>10.1f} {mid:>11.0%} {miss:>30} of {len(risky_safety)}")
    print("  piotr is stricter across the board. kasia sticks to the middle of the scale and misses")
    print("  policy details in safety answers. The average of the three hides both.")


def where(rows: List[Dict]) -> None:
    header("3. WHERE DOES THE DISAGREEMENT LIVE?")
    for cat in ("faq", "tone", "safety"):
        sub = [r for r in rows if r["category"] == cat]
        a = krippendorff_alpha([list(r["labels"].values()) for r in sub])["alpha"]
        print(f"  {cat:7} {len(sub):>3} answers   alpha {a:5.2f}")
    allr = krippendorff_alpha([list(r["labels"].values()) for r in rows])["alpha"]
    print(f"  all     {len(rows):>3} answers   alpha {allr:5.2f}")
    print("  The overall number mixes easy FAQ answers with the safety answers that need attention.")


def extra_rater(rows: List[Dict]) -> None:
    header("4. DOES AN EXTRA RATER ADD ANYTHING? (vs expert arbitration)")
    one = mean(r["labels"]["ola"] == r["expert_label"] for r in rows)
    two_agree = [r for r in rows if r["labels"]["ola"] == r["labels"]["piotr"]]
    two_acc = mean(r["labels"]["ola"] == r["expert_label"] for r in two_agree)
    three = [(majority(list(r["labels"].values())), r["expert_label"]) for r in rows]
    decided = [(m, e) for m, e in three if m is not None]
    three_acc = mean(m == e for m, e in decided)
    print(f"  1 rater (ola):                     matches the expert on {one:.0%} of all {len(rows)} answers")
    print(f"  2 raters (ola + piotr):            agree on {len(two_agree)}; on those, {two_acc:.0%} match the expert;")
    print(f"                                     the other {len(rows) - len(two_agree)} go to the expert")
    print(f"  3 raters, majority:                a majority on {len(decided)}; on those, {three_acc:.0%} match the expert")
    print("  The second rater's value is that it tells you which items to escalate.")
    print("  Compare such numbers before buying more labels: stop buying labels that grow the dataset")
    print("  but not its reliability.")


def guideline(all_rows: List[Dict]) -> None:
    header("5. TEST THE GUIDELINE ITSELF")
    print("  v2 splits the vague 'quality' label into tone and safety, with anchor examples.")
    print(f"  {'':8} {'v1 alpha':>9} {'v2 alpha':>9}   ola vs kasia kappa v1 -> v2")
    for cat in ("faq", "tone", "safety", "all"):
        vals = []
        for g in ("v1", "v2"):
            sub = [r for r in all_rows if r["guideline"] == g and (cat == "all" or r["category"] == cat)]
            vals.append((krippendorff_alpha([list(r["labels"].values()) for r in sub])["alpha"],
                         cohen_kappa([r["labels"]["ola"] for r in sub], [r["labels"]["kasia"] for r in sub])["kappa"]))
        print(f"  {cat:8} {vals[0][0]:>9.2f} {vals[1][0]:>9.2f}   {vals[0][1]:.2f} -> {vals[1][1]:.2f}")
    print("  Same reviewers, same answers. The instrument changed, and agreement was measured, not assumed.")


def main() -> None:
    all_rows = load_jsonl(HERE / "data" / "reviews.jsonl")
    rows = [r for r in all_rows if r["guideline"] == "v1"]
    print(f"{len(rows)} answers labeled under guideline v1 (and again under v2 for question 5).")
    predicts(rows)
    biases(rows)
    where(rows)
    extra_rater(rows)
    guideline(all_rows)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
