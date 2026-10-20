"""
stratified_report.py: the average lies in two ways.

Run:  python stratified_report.py                          # candidate v2
      python stratified_report.py data/candidate_v3.jsonl
      python stratified_report.py path/to/your_results.jsonl

Each line of the input is one scored case:
  {"id": ..., "slice": ..., "score": 0-10, "policy_failure": bool,
   "critical": null or "privacy_leak", "latency_ms": ..., "markers": [...]}

Lie 1: the average hides weak slices.   Fix: stratified reporting.
Lie 2: the average hides rare disasters. Fix: look at the worst cases and at markers,
       and remember that zero failures in a sample is not proof of safety.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from stats import by_slice, load, mean_ci

HERE = Path(__file__).parent
DEFAULT = HERE / "data" / "candidate_v2.jsonl"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    rows = load(path)
    scores = [r["score"] for r in rows]
    m, lo, hi = mean_ci(scores)
    n = len(rows)

    print(f"Results: {path.name}  ({n} scored cases)\n")
    print(f"Overall mean score: {m:.2f} out of 10 (95% CI {lo:.2f}–{hi:.2f}). Sounds good.")

    # --- Lie 1 -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("LIE 1: THE AVERAGE HIDES WEAK SLICES")
    print("=" * 78)
    print(f"{'slice':20} {'n':>4} {'mean':>6} {'95% CI':>13} {'min':>4} {'≥7':>6}")
    slices = by_slice(rows)
    order = sorted(slices, key=lambda s: -sum(r["score"] for r in slices[s]) / len(slices[s]))
    for name in order:
        vals = [r["score"] for r in slices[name]]
        sm, slo, shi = mean_ci(vals)
        share = sum(v >= 7 for v in vals) / len(vals)
        flag = "  <- below the overall mean" if sm < m - 1 else ""
        ci = f"{slo:>6.1f}–{shi:<5.1f}" if math.isfinite(slo) else f"{'n/a':^13}"
        print(f"{name:20} {len(vals):>4} {sm:>6.1f} {ci} {min(vals):>4} {share:>6.0%}{flag}")
    weak = [name for name in order if mean_ci([r["score"] for r in slices[name]])[0] < m - 1]
    print("\nThe average was not false. It was incomplete.")
    if weak:
        print("Instead of 'quality is bad', the report can now say: 'quality is good overall,")
        print(f"but {' and '.join(weak)} are failing'. Now you know what to work on.")
    print("Small slices have wide intervals: there, the next step is often more samples.")

    # --- Lie 2 -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("LIE 2: THE AVERAGE HIDES RARE DISASTERS")
    print("=" * 78)
    critical = [r for r in rows if r["critical"]]
    print(f"Worst score: {min(scores)}. Critical failures: {len(critical)} out of {n}.")
    for r in critical:
        print(f"  ! {r['id']} ({r['slice']}): {r['critical']}, score {r['score']}")
    if critical and n > 100:
        miss = math.comb(n - len(critical), 100) / math.comb(n, 100)
        print(f"\nIf you had reviewed only 100 random cases out of these {n}, you would have missed")
        print(f"{'this failure' if len(critical) == 1 else 'all of them'} with probability about {miss:.0%}.")
    if critical:
        print("A bigger random sample is not enough for rare failures. Look for markers too.")

    flagged = [r for r in rows if r["markers"]]
    print(f"\nCases with markers (low confidence, missing citation, judge disagreement,")
    print(f"unusual tool call): {len(flagged)} out of {n}")
    for r in sorted(flagged, key=lambda r: r["score"]):
        hit = "  <- the real problem" if r["critical"] else ""
        print(f"  {r['id']}  score {r['score']:>2}  {', '.join(r['markers'])}{hit}")
    print("A marker does not prove a failure. It tells you where to look first.")

    clean = n - sum(r["policy_failure"] or bool(r["critical"]) for r in rows)
    print(f"\nAnd the sentence worth remembering: with 0 failures in 100 cases, the true failure")
    print(f"rate could still be up to about 3% (3/n). That is an absence of evidence, not")
    print(f"evidence of safety. Here, {clean} of {n} cases were free of policy or critical failures.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
