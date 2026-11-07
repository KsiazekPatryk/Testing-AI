"""
harmful_or_healthy.py: disagreement is not always a defect.

Run:  python harmful_or_healthy.py

  harmful disagreement: reviewers do not understand the rubric, the policy is unclear,
                        or a judge rewards unsafe output.   -> fix the rubric, policy, training or judge
  healthy disagreement: different users reasonably value different acceptable outcomes.
                        -> understand the preference groups and design the product for them

Part 1 triages eight real disagreements (data/disagreement_cases.json).
Part 2 shows a healthy one up close: 300 users rate a concise and a detailed answer.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, Tuple

from agreement import load_json, load_jsonl

HERE = Path(__file__).parent

ACTIONS = {
    "error": ("harmful", "someone saw a blocker the others missed: treat it as a blocker, retrain the reviewers"),
    "judge": ("harmful", "the judge rewards unsafe output: recalibrate the judge against humans"),
    "policy": ("harmful", "the policy does not answer the question: clarify the policy"),
    "rubric": ("harmful", "reviewers score different dimensions: split the rubric into dimensions"),
    "preference": ("healthy", "acceptable answers, different tastes: find the preference groups, design for them"),
    "uncertainty": ("healthy", "the request itself is ambiguous: ask a clarifying question or offer options"),
}


def triage(case: Dict) -> Tuple[str, str, str]:
    """Returns (cause, kind, action). The order matters: safety questions first."""
    if case["judge_involved"] and case["blocker_seen_by"]:
        cause = "judge"
    elif case["blocker_seen_by"]:
        cause = "error"
    elif not case["policy_clear"]:
        cause = "policy"
    elif len(set(case["dimensions_cited"])) > 1 and not case.get("genuinely_ambiguous_request"):
        cause = "rubric"
    elif case.get("genuinely_ambiguous_request"):
        cause = "uncertainty"
    else:
        cause = "preference"
    kind, action = ACTIONS[cause]
    return cause, kind, action


def cases() -> None:
    data = load_json(HERE / "data" / "disagreement_cases.json")["cases"]
    print("=" * 78 + "\n1. TRIAGE: WHAT DID EACH DISAGREEMENT REVEAL?\n" + "=" * 78)
    tally: Dict[str, int] = {}
    for c in data:
        cause, kind, action = triage(c)
        tally[kind] = tally.get(kind, 0) + 1
        print(f"\n  {c['id']}  \"{c['question']}\"   scores {c['scores']}")
        for r in c["reasons"]:
            print(f"        - {r}")
        print(f"     -> {kind.upper()} ({cause}): {action}")
    print(f"\n  {tally.get('harmful', 0)} harmful, {tally.get('healthy', 0)} healthy.")
    print("  A mature question is not only 'did the reviewers agree?' but: when they disagreed, did they")
    print("  reveal an error, an unclear rubric, real uncertainty, or a useful preference signal?")


def preferences() -> None:
    rows = load_jsonl(HERE / "data" / "preferences.jsonl")
    print("\n" + "=" * 78 + "\n2. A HEALTHY DISAGREEMENT UP CLOSE: CONCISE OR DETAILED?\n" + "=" * 78)
    print(f"  {len(rows)} users rate two answers to the same question (1-5). Both answers meet the policy.")
    print(f"  average: concise {mean(r['rating_concise'] for r in rows):.2f}, "
          f"detailed {mean(r['rating_detailed'] for r in rows):.2f}   -> looks like a tie")
    short = [r for r in rows if r["rating_concise"] - r["rating_detailed"] >= 1]
    deep = [r for r in rows if r["rating_detailed"] - r["rating_concise"] >= 1]
    none = len(rows) - len(short) - len(deep)
    print(f"  but per user: {len(short)} clearly prefer concise, {len(deep)} clearly prefer detailed, {none} no preference")
    for name, grp in (("prefer concise", short), ("prefer detailed", deep)):
        print(f"    {name:16} concise {mean(r['rating_concise'] for r in grp):.1f}, "
              f"detailed {mean(r['rating_detailed'] for r in grp):.1f}")
    print("  Nobody here is wrong. The average describes no real user.")
    for task in ("support", "coding"):
        sub = [r for r in rows if r["task"] == task]
        s = sum(r["rating_concise"] > r["rating_detailed"] for r in sub) / len(sub)
        label = "minimal patch" if task == "coding" else "concise answer"
        print(f"  {task:8}: {s:.0%} prefer the {label}")
    print("\n  Product design, not a rubric fix:")
    print("    - answer briefly by default, offer 'show details' for people who want depth")
    print("    - remember the preference per user")
    print("    - when the request itself is ambiguous, ask a clarifying question or show options")


def main() -> None:
    cases()
    preferences()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
