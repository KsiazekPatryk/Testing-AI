"""
score_went_up.py: the score went up, and the product did not change.

Run:  python score_went_up.py

The search dashboard jumps overnight from 78 to 86. Everyone assumes the new ranking worked.
But no ranking, prompt, model or code was deployed. While refreshing the test set, the team
changed several things at once: replaced stale expected results, refreshed the search-data
snapshot, updated the judge model, widened the rubric to reward weaker citations, and removed
twelve hard queries because reviewers could not agree on the answer.

  1. the dashboard, drawn the honest way: no continuous line across incomparable packages
  2. what changed: in the product, and in the measuring instrument
  3. where the 8 points came from: one measurement change at a time, on the same product
  4. the honest comparison: the product on the SAME package
  5. privacy: an evaluation set that copies production is production data
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

from evalkit import diff_packages, fingerprint, load_json, load_jsonl

HERE = Path(__file__).parent

# How each package judges an answer. The product's answers are the same in both.
SETTINGS = {
    "search-eval-v14": {"expected": "old", "snapshot": "old", "judge": "old", "rubric": "strict", "drop_disputed": False},
    "search-eval-v15": {"expected": "new", "snapshot": "new", "judge": "new", "rubric": "wide", "drop_disputed": True},
}
STEPS = [("replace stale expected results", "expected", "new"),
         ("refresh the search-data snapshot", "snapshot", "new"),
         ("update the judge model", "judge", "new"),
         ("widen the rubric (weaker citations pass)", "rubric", "wide"),
         ("remove 12 disputed hard queries", "drop_disputed", True)]


def score(rows: List[Dict], s: Dict) -> Tuple[int, int]:
    passed = total = 0
    for q in rows:
        if s["drop_disputed"] and q["disputed"]:
            continue
        total += 1
        ok = q["answer_correct"]
        if s["expected"] == "old" and q["expected_stale"]:
            ok = False
        if s["snapshot"] == "old" and q["snapshot_dependent"]:
            ok = False
        if s["rubric"] == "strict" and q["citation_weak"]:
            ok = False
        if s["judge"] == "old" and q["judge_borderline"]:
            ok = False
        passed += ok
    return passed, total


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def dashboard(data: Dict) -> None:
    header("1. THE DASHBOARD")
    prev = None
    for n in data["nights"]:
        fp = fingerprint(data["packages"][n["package"]])
        if prev and fp != prev:
            print(f"  {'':10} ---- package changed ({n['package']}): trend line broken, not comparable ----")
        bar = "#" * int((n["score"] - 70) * 3)
        print(f"  {n['date']}  {n['score']:5.1f}  {bar}")
        prev = fp
    print("  A dashboard that draws one continuous line across these packages is telling a story")
    print("  the data does not support.")


def main() -> None:
    data = load_json(HERE / "data" / "packages.json")
    rows = load_jsonl(HERE / "data" / "search_eval.jsonl")
    dashboard(data)

    header("2. WHAT CHANGED: THE PRODUCT, OR THE MEASURING INSTRUMENT?")
    a, b = data["packages"]["search-eval-v14"], data["packages"]["search-eval-v15"]
    d = diff_packages(a, b)
    print(f"  product:     {', '.join(d['product']) or 'nothing'}")
    print(f"  measurement: {', '.join(d['measurement'])}")
    for k in d["measurement"]:
        print(f"    {k:20} {a[k]}  ->  {b[k]}")
    print("  The useful question is not 'why did the score go up?' but 'what changed in the product,")
    print("  and what changed in the measuring instrument?'")

    header("3. WHERE THE POINTS CAME FROM (same product, one change at a time)")
    s = dict(SETTINGS["search-eval-v14"])
    p, t = score(rows, s)
    print(f"  {'starting package v14':45} {p:>3}/{t:<3} {p / t:6.1%}")
    for name, key, value in STEPS:
        s[key] = value
        before = p / t
        p, t = score(rows, s)
        print(f"  + {name:43} {p:>3}/{t:<3} {p / t:6.1%}  ({(p / t - before) * 100:+.1f})")
    print("  Every point came from the instrument. The team accidentally measured an easier test.")
    print("  Some changes are fixes (stale expectations, an old snapshot), some make the test easier")
    print("  (a lenient judge, a wider rubric, dropping hard queries). Either way: not product progress.")

    header("4. THE HONEST COMPARISON: SAME PACKAGE, BOTH PRODUCT VERSIONS")
    for pkg in ("search-eval-v14", "search-eval-v15"):
        p, t = score(rows, SETTINGS[pkg])
        print(f"  {pkg}: last week's product {p / t:.1%}, this week's product {p / t:.1%}  (no product change)")
    print("  Version everything that makes up an evaluation like code: dataset, labels, rubric, judge")
    print("  prompt and model, retrieval snapshot, scorer code, product version.")

    header("5. PRIVACY: AN EVALUATION SET THAT COPIES PRODUCTION")
    for name, pkg in data["packages"].items():
        g = pkg["data_governance"]
        missing = [k for k in ("who_can_view", "who_can_edit", "retention") if not g.get(k)]
        broad = "anyone" in " ".join(g.get("who_can_edit") or [])
        status = "OK" if not missing and not broad else "FIX: " + ", ".join(
            [f"{m} not set" for m in missing] + (["editing open to anyone with repo access"] if broad else []))
        print(f"  {name}: real user queries: {g['contains_real_user_queries']}; {status}")
    print("  An evaluation is not 'just a test' when it is a copy of production. Know who can view it,")
    print("  who can change it, and how long it is kept.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
