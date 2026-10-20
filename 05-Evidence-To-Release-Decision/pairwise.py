"""
pairwise.py: which version is better? Compare in pairs.

Run:  python pairwise.py
      python pairwise.py --seed 7     # a different random order, the same verdicts

Reviewers often disagree whether an answer deserves a 7 or an 8, but they easily agree
that B is clearer and safer than A. So the same question goes through two versions
(old prompt A, new prompt B) and a judge picks A, B or a tie.

The rules that keep this honest, all implemented below:
  1. "Better" is defined by a rubric: correct, helpful, safe. Not longer or more confident.
  2. The order is randomized and labels are hidden: the judge sees "Answer 1" and "Answer 2".
  3. Ties are allowed. A forced choice creates noise.
  4. Pairwise wins do not replace hard checks: B can beat A and still be unacceptable.

The naive judge shows what happens without rule 1 and 2: it rewards length and
confidence, and it prefers whatever it sees first.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from stats import wilson

HERE = Path(__file__).parent

OUTSIDE = r"outside|too late|not possible|can't take them back|\bno\b"
INSIDE = r"still within|you can return|\byes\b"
NEXT_STEP = r"order page|warranty|store credit|trade-in|start a return|gift receipt"
HARD_VIOLATION = r"exception|60 days|whenever you like"


def rubric(answer: str, expected_verdict: str) -> Tuple[int, List[str]]:
    """Score one answer. Returns (points, hard violations)."""
    t = answer.lower()
    points = 0
    states_policy = bool(re.search(r"30[- ]day", t))
    verdict_ok = bool(re.search(OUTSIDE if expected_verdict == "outside" else INSIDE, t))
    if states_policy and verdict_ok:
        points += 3           # correct: the right policy and the right verdict
    elif verdict_ok:
        points += 1           # right verdict, but no reason given
    if re.search(NEXT_STEP, t):
        points += 1           # helpful: a clear next step
    violations = re.findall(HARD_VIOLATION, t)
    if violations:
        points -= 3           # unsafe: invents an exception or a wrong policy
    return points, violations


def rubric_judge(answer_1: str, answer_2: str, expected: str) -> str:
    s1, _ = rubric(answer_1, expected)
    s2, _ = rubric(answer_2, expected)
    return "1" if s1 > s2 else "2" if s2 > s1 else "tie"


def naive_judge(answer_1: str, answer_2: str, expected: str) -> str:
    """Prefers longer, more confident answers, and whatever it reads first when unsure."""
    def appeal(a: str) -> float:
        return len(a) + 40 * a.count("!") + 40 * len(re.findall(r"absolutely|of course|definitely", a.lower()))
    a1, a2 = appeal(answer_1), appeal(answer_2)
    if abs(a1 - a2) < 0.15 * max(a1, a2):
        return "1"            # position bias
    return "1" if a1 > a2 else "2"


def compare(cases: List[Dict], judge, rng: random.Random) -> Dict[str, str]:
    """Run each pair with a random order and hidden labels. Returns case id -> A/B/tie."""
    verdicts = {}
    for c in cases:
        b_first = rng.random() < 0.5
        first, second = (c["new"], c["old"]) if b_first else (c["old"], c["new"])
        pick = judge(first, second, c["expected_verdict"])
        if pick == "tie":
            verdicts[c["id"]] = "tie"
        else:
            picked_new = (pick == "1") == b_first
            verdicts[c["id"]] = "B" if picked_new else "A"
    return verdicts


def summary(verdicts: Dict[str, str]) -> str:
    n = len(verdicts)
    a = sum(v == "A" for v in verdicts.values())
    b = sum(v == "B" for v in verdicts.values())
    t = n - a - b
    lo, hi = wilson(b, a + b) if a + b else (0.0, 1.0)
    return (f"B (new) wins {b}/{n} ({b / n:.0%}), A (old) wins {a}/{n} ({a / n:.0%}), ties {t}/{n} ({t / n:.0%})\n"
            f"    among decisive pairs, B wins {b}/{a + b}: 95% CI {lo:.0%}–{hi:.0%}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pairwise comparison of two prompt versions.")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    data = json.loads((HERE / "pairwise_cases.json").read_text(encoding="utf-8"))
    cases = data["support"]

    print("=" * 78)
    print(f"RUBRIC JUDGE: random order, hidden labels, ties allowed ({len(cases)} questions)")
    print("=" * 78)
    rubric_verdicts = compare(cases, rubric_judge, random.Random(a.seed))
    print("  " + summary(rubric_verdicts))
    swapped = compare(cases, rubric_judge, random.Random(a.seed + 1000))
    print(f"  Same verdicts with a different random order: "
          f"{sum(rubric_verdicts[k] == swapped[k] for k in rubric_verdicts)}/{len(cases)}")

    print("\n" + "=" * 78)
    print("NAIVE JUDGE: rewards length and confidence, reads the first answer more kindly")
    print("=" * 78)
    naive = compare(cases, naive_judge, random.Random(a.seed))
    print("  " + summary(naive))
    naive_swapped = compare(cases, naive_judge, random.Random(a.seed + 1000))
    flips = [k for k in naive if naive[k] != naive_swapped[k]]
    print(f"  Verdicts that flip when only the order changes: {len(flips)}/{len(cases)}"
          + (f" ({', '.join(flips)})" if flips else ""))
    disagree = [k for k in naive if naive[k] != rubric_verdicts[k]]
    print(f"  Disagrees with the rubric judge on {len(disagree)} questions: {', '.join(disagree)}")

    print("\n" + "=" * 78)
    print("HARD CHECKS: pairwise wins do not replace them")
    print("=" * 78)
    found = False
    for c in cases:
        _, violations = rubric(c["new"], c["expected_verdict"])
        if violations:
            found = True
            print(f"  ! {c['id']}: B {'beats' if rubric_verdicts[c['id']] == 'B' else 'does not beat'} A, "
                  f"but B still says: \"{c['new']}\"")
            print(f"    Hard violation: {', '.join(sorted(set(violations)))}. Better than the old answer, still unacceptable.")
    if not found:
        print("  No hard violations in B.")

    fix = data["code_fix"]
    print("\n" + "=" * 78)
    print("THE SAME IDEA FOR CODE: an agent fixing a flaky payment test")
    print("=" * 78)
    print(f"  A: {fix['old']}")
    print(f"  B: {fix['new']}")
    print("  Both make CI green. A hides the problem (a longer wait), B removes its cause")
    print("  (a deterministic clock) and checks that retries happen at the right time.")
    print("  The question is not which answer looks nicer, but which one we trust more.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
