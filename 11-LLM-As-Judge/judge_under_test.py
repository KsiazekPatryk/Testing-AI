"""
judge_under_test.py: the judge is also a system under test.

Run:  python judge_under_test.py
      python judge_under_test.py --runs 10

A judge can be inconsistent, too lenient, fooled by fluent but wrong answers, biased toward
length, and it can mistake a warm tone for policy compliance. Test it like any other system:
  1. consistency: the same reply, scored several times
  2. probes: pairs of replies that differ in ONE thing, so you know what the judge should do
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from statistics import pstdev

from judge import judge_v1, judge_v2
from metrics import load_json, load_jsonl, mean

HERE = Path(__file__).parent


def consistency(runs: int) -> None:
    rows = load_jsonl(HERE / "data" / "replies.jsonl")[::12]          # 20 replies across the segments
    print("=" * 78 + f"\n1. CONSISTENCY: {len(rows)} REPLIES, EACH SCORED {runs} TIMES\n" + "=" * 78)
    for j in (judge_v1, judge_v2):
        spreads, changed = [], 0
        for r in rows:
            s = [j(r["reply"], run)[0] for run in range(runs)]
            spreads.append(max(s) - min(s))
            changed += len(set(s)) > 1
        print(f"  {j.__name__}: score changed between runs for {changed} of {len(rows)} replies, "
              f"average range {mean(spreads):.1f} points, largest {max(spreads)}")
    print("  A score that moves by 2 points between runs cannot tell a 7 from a 9.")
    print("  Score important cases several times, or report the range, not one draw.")


def probes(runs: int) -> None:
    data = load_json(HERE / "data" / "probes.json")["pairs"]
    print("\n" + "=" * 78 + "\n2. PROBES: PAIRS THAT DIFFER IN ONE THING (mean of runs)\n" + "=" * 78)
    passed = {"judge_v1": 0, "judge_v2": 0}
    for p in data:
        print(f"\n  {p['bias']}  (expected: {p['expected']})")
        for j in (judge_v1, judge_v2):
            a = mean([j(p["a"], k)[0] for k in range(runs)])
            b = mean([j(p["b"], k)[0] for k in range(runs)])
            ok = abs(a - b) <= 1 if p["expected"] == "same score" else a > b + 1
            passed[j.__name__] += ok
            print(f"    {j.__name__}: a {a:4.1f}   b {b:4.1f}   {'ok' if ok else 'FAILS'}")
    print()
    for name, n in passed.items():
        print(f"  {name}: {n} of {len(data)} probes passed")
    print("  judge_v1 rewards length and warmth, and cannot see the policy: it prefers the fluent wrong")
    print("  answer and the friendly one that breaks the rules. judge_v2 has the policy, anchors and")
    print("  blocker checks in its prompt.")


def known_failure_modes() -> None:
    print("\n" + "=" * 78 + "\nWHAT TO PROBE FOR\n" + "=" * 78)
    for m in ("inconsistency between runs", "excessive leniency", "fluent but wrong answers",
              "rewarding verbosity", "penalizing safe, short answers", "warm tone mistaken for policy compliance",
              "subtle contradictions of the policy", "a wrong sense of the current date (copyright_year.py)",
              "over-generosity in one segment, e.g. privacy (calibration.py)"):
        print(f"  - {m}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Test the judge itself.")
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    consistency(a.runs)
    probes(a.runs)
    known_failure_modes()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
