"""
calibration.py: "I'm confident" is not a confidence interval.

Run:  python calibration.py

Two meanings of "confidence":
  model-reported confidence  one judgment's self-assessment: "score 8/10, confidence medium"
  statistical confidence     computed from many measured examples: "mean 8.2, 95% CI 7.8-8.6"

Reported confidence is useful only when it is calibrated: of 100 decisions marked
"80% sure", about 80 should be correct. This script checks that for two LLM judges
(data/judge_confidence.jsonl), turns calibration into action rules, and shows that
calibration is local: a judge calibrated in English can be overconfident in Polish.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

from stats import load_jsonl, wilson

HERE = Path(__file__).parent
BUCKETS = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
RULES = [(0.90, "answer on its own"), (0.70, "ask a clarifying question"), (0.0, "hand over to a human")]


def brier(rows: List[Dict]) -> float:
    """Mean squared gap between confidence and outcome (1 correct, 0 wrong). Lower is better."""
    return mean((r["confidence"] - r["correct"]) ** 2 for r in rows)


def ece(rows: List[Dict]) -> Tuple[float, List[Tuple[str, int, float, float, int]]]:
    """Expected calibration error: the weighted gap between confidence and accuracy per bucket."""
    table, total = [], 0.0
    for lo, hi in BUCKETS:
        b = [r for r in rows if lo <= r["confidence"] < hi or (hi == 1.0 and r["confidence"] == 1.0)]
        if not b:
            continue
        conf, acc = mean(r["confidence"] for r in b), mean(r["correct"] for r in b)
        total += len(b) / len(rows) * abs(conf - acc)
        table.append((f"{lo:.1f}–{hi:.1f}", len(b), conf, acc, sum(r["correct"] for r in b)))
    return total, table


def show(title: str, rows: List[Dict]) -> None:
    e, table = ece(rows)
    print(f"\n{title}  ({len(rows)} verdicts)")
    print(f"  {'confidence':>10} {'n':>5} {'says':>6} {'really':>7} {'95% CI':>10}  verdict")
    for label, n, conf, acc, k in table:
        lo, hi = wilson(k, n)
        verdict = "overconfident" if hi < conf else "underconfident" if lo > conf else "fine, within noise"
        print(f"  {label:>10} {n:>5} {conf:>6.0%} {acc:>7.0%} {lo:>4.0%}–{hi:<4.0%}  {verdict}")
    print(f"  Brier score {brier(rows):.3f}   ECE {e:.3f}   (lower is better for both)")
    print("  A bucket counts as miscalibrated only if its 95% CI excludes the stated confidence.")


def rule_for(c: float) -> str:
    return next(action for threshold, action in RULES if c >= threshold)


def action_rules(title: str, rows: List[Dict]) -> None:
    print(f"\n{title}")
    for _, action in RULES:
        zone = [r for r in rows if rule_for(r["confidence"]) == action]
        if zone:
            wrong = sum(not r["correct"] for r in zone)
            print(f"  {action:28} {len(zone):>4} cases, wrong {wrong:>3} ({wrong / len(zone):.0%})")


def main() -> None:
    print("A forced single number hides ambiguity:")
    print('  Q: "How many planets are in the Solar System? Give me one number."  A: "8."')
    print('  Q: "...answer with your confidence."  A: "The conventional answer is 8 (Pluto was')
    print('      reclassified as a dwarf planet in 2006), confidence: medium."')
    print("  A useful signal for routing the case to a human. Still the model's claim, not a measurement.")

    rows = load_jsonl(HERE / "data" / "judge_confidence.jsonl")
    sure = [r for r in rows if r["judge"] == "always_sure"]
    cal_en = [r for r in rows if r["judge"] == "calibrated" and r["language"] == "en"]
    cal_pl = [r for r in rows if r["judge"] == "calibrated" and r["language"] == "pl"]

    print("\n" + "=" * 78 + "\nCALIBRATION: does \"80% sure\" mean 80%?\n" + "=" * 78)
    show("Judge 'always_sure' (says 0.95 every time)", sure)
    print("  Sounds certain, tells you nothing about which cases are actually safe.")
    show("Judge 'calibrated', English questions", cal_en)

    print("\n" + "=" * 78 + "\nACTION RULES (low-risk support assistant)\n" + "=" * 78)
    print("  ≥ 0.90 answer on its own · 0.70–0.90 ask a clarifying question · < 0.70 hand over to a human")
    action_rules("English questions:", cal_en)

    print("\n" + "=" * 78 + "\nCALIBRATION IS LOCAL: the same judge on Polish questions\n" + "=" * 78)
    show("Judge 'calibrated', Polish questions", cal_pl)
    action_rules("The same rules on Polish questions:", cal_pl)
    print("\n  The thresholds that are safe in English let far more errors through in Polish.")
    print("  After changing the model, the prompt, the tools or the language: check calibration again.")
    print("  A medical or financial flow needs much higher thresholds.")
    print("\nModel confidence is a signal; statistical confidence is a calculation.")
    print("Report them separately, and never let a model's confidence pose as evidence.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
