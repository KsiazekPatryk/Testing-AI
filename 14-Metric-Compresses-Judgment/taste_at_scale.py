"""
taste_at_scale.py: judging style on more than a demo.

Run:  python taste_at_scale.py

The rubric from correct_but_ugly.py tells raters what to look for. Three more habits keep style
ratings honest once there are many outputs:

  1. prefer pairwise comparisons ("which version fits the reader better, and why?"): they limit scale drift
  2. sample widely: systems often look good in the demo and fall apart on long documents, other
     languages or dense data
  3. measure the distance from human effort: how much time the AI saves, and how much it takes to
     make the output ready to send. If the best output always needs a talented person to rework it,
     the system is at most a first-draft generator.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from statistics import median_low as median

from metrickit import load_jsonl, mean

HERE = Path(__file__).parent


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def drift(ratings, pairs) -> None:
    header("1. ABSOLUTE SCORES DRIFT, PAIRWISE PREFERENCES DO NOT")
    early, late = ratings[:20], ratings[-20:]
    print("  One rater, 60 outputs in one long session. The outputs are equally good on average.")
    print(f"  {'':22} {'true quality (hidden)':>22} {'absolute score given':>22}")
    for name, part in (("first 20 rated", early), ("last 20 rated", late)):
        print(f"  {name:22} {mean([r['latent_quality'] for r in part]):22.2f} "
              f"{mean([r['absolute_score'] for r in part]):22.2f}")
    inverted = total = 0
    for a in early:
        for b in late:
            if b["latent_quality"] > a["latent_quality"] + 0.5:
                total += 1
                inverted += a["absolute_score"] > b["absolute_score"]
    print(f"\n  Pairs where a late output is clearly better (by 0.5+) than an early one: {total}.")
    print(f"  The absolute scores rank the early one higher in {inverted} of them ({inverted / total:.0%}).")
    agree = [p["preferred"] == p["better_by_latent"] for p in pairs]
    h = len(agree) // 2
    print(f"\n  Pairwise judgments from the same rater ('which one fits the reader better?'):")
    print(f"    agree with the hidden quality: first half {mean(agree[:h]):.0%}, second half {mean(agree[h:]):.0%}")
    print("  A pair carries its own reference point, so the rater's slipping scale cancels out.")


def slices(rows) -> None:
    by = defaultdict(list)
    for r in rows:
        by[r["slice"]].append(r)

    header("2. SAMPLE WIDELY: THE DEMO IS ONE SLICE")
    print(f"  {'slice':30} {'n':>3} {'mean':>5} {'7+':>5} {'4 or less':>10}")
    for name, rs in by.items():
        s = [r["style_score"] for r in rs]
        print(f"  {name:30} {len(s):3} {mean(s):5.1f} {mean([x >= 7 for x in s]):5.0%} {mean([x <= 4 for x in s]):10.0%}")
    all_s = [r["style_score"] for r in rows]
    print(f"  {'all slices together':30} {len(all_s):3} {mean(all_s):5.1f}")
    print("\n  The demo slice is what gets shown in meetings. Long documents, Polish and dense data are")
    print("  where users meet the system, and one average over everything hides all of them.")

    header("3. DISTANCE FROM HUMAN EFFORT")
    manual = rows[0]["manual_minutes"]
    print(f"  Writing it by hand takes about {manual} minutes. Per slice, the minutes a person needed to")
    print("  make the AI output ready to send:")
    print(f"  {'slice':30} {'median edit':>11} {'saved':>6} {'full rewrite':>13}  verdict")
    for name, rs in by.items():
        edit = median([r["edit_minutes"] for r in rs])
        rewrite = mean([r["needed_full_rewrite"] for r in rs])
        saved = manual - edit
        verdict = ("ready to send after a light edit" if edit <= manual * 0.2 and rewrite < 0.1
                   else "first-draft generator")
        print(f"  {name:30} {edit:9.0f} m {saved:4.0f} m {rewrite:12.0%}   {verdict}")
    print("\n  A first-draft generator can still be worth having. It should not be sold, tested or")
    print("  priced as a system that produces finished work.")


def main() -> None:
    drift(load_jsonl(HERE / "data" / "style_ratings.jsonl"), load_jsonl(HERE / "data" / "style_pairs.jsonl"))
    slices(load_jsonl(HERE / "data" / "style_slices.jsonl"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
