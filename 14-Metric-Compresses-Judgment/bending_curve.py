"""
bending_curve.py: the curve that bends.

Run:  python bending_curve.py

AI quality rises fast at first, because the obvious problems get removed: wrong oracles, missing
simple guards, visible errors. Then growth slows. The remaining failures are rarer, more ambiguous
and harder to reproduce. Every next point needs more data, better judges and experts, and improving
one group of queries can quietly make two others worse.

A team catching up with the leader can see almost linear growth and think it will catch up soon.
In practice both are on asymptotic curves, and the leader has used up the easy fixes.

  1. your quality over time, with uncertainty bands, not just points
  2. the straight line you are tempted to draw, and the curve that fits
  3. the leader: diminishing returns and a plateau
  4. the last release, per segment: one group better, two quietly worse
  5. an acceptable level of measured risk instead of "perfect AI"
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Tuple

from metrickit import load_json, wilson

HERE = Path(__file__).parent
LO, HI, WIDTH = 0.50, 1.00, 50


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def band_line(lo: float, p: float, hi: float) -> str:
    pos = lambda x: int(round((x - LO) / (HI - LO) * WIDTH))  # noqa: E731
    row = [" "] * (WIDTH + 1)
    for i in range(max(0, pos(lo)), min(WIDTH, pos(hi)) + 1):
        row[i] = "-"
    row[pos(p)] = "o"
    return "|" + "".join(row) + "|"


def distinguishable(p1: int, p2: int, n: int) -> bool:
    """Two-proportion z-test at 95%: is the change bigger than the noise of n cases?"""
    a, b = p1 / n, p2 / n
    pooled = (p1 + p2) / (2 * n)
    se = math.sqrt(2 * pooled * (1 - pooled) / n)
    return abs(b - a) / se > 1.96 if se else False


def fit_line(ys: List[float]) -> Tuple[float, float]:
    xs = list(range(len(ys)))
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - slope * mx, slope


def fit_curve(ys: List[float]) -> Tuple[float, float, float]:
    """Least-squares fit of q(t) = cap - (cap - q0) * exp(-k t) by grid search."""
    best = None
    for cap100 in range(int(max(ys) * 100) + 1, 100):
        cap = cap100 / 100
        for k1000 in range(20, 600, 5):
            k = k1000 / 1000
            q0 = ys[0]
            err = sum((cap - (cap - q0) * math.exp(-k * t) - y) ** 2 for t, y in enumerate(ys))
            if best is None or err < best[0]:
                best = (err, cap, q0, k)
    return best[1], best[2], best[3]


def main() -> None:
    d = load_json(HERE / "data" / "quality_history.json")
    n = d["n_cases"]
    you, lead = d["yours"], d["leader"]

    header("1. YOUR QUALITY OVER TIME, WITH UNCERTAINTY BANDS")
    print(f"  pass rate on the same {n} evaluation cases; o = measured, --- = 95% interval")
    print(f"  {'':10}{LO:<26.0%}{HI:>26.0%}")
    for i, (r, p) in enumerate(zip(you["releases"], you["passed"])):
        lo, hi = wilson(p, n)
        real = "" if i == 0 else ("  real change" if distinguishable(you["passed"][i - 1], p, n) else "  within noise")
        print(f"  {r:5} {p / n:4.0%} {band_line(lo, p / n, hi)}{real}")
    drops = [you["releases"][i] for i in range(1, len(you["passed"])) if you["passed"][i] < you["passed"][i - 1]]
    if drops:
        print(f"  Points alone would make {', '.join(drops)} look like a regression. The bands overlap: it is noise.")
    print("  From a distance the points form an almost straight line upwards.")

    header("2. THE STRAIGHT LINE, AND THE CURVE")
    ys = [p / n for p in you["passed"]]
    a, b = fit_line(ys)
    leader_now = lead["passed"][-1] / n
    steps = (leader_now - a) / b - (len(ys) - 1)
    print(f"  A straight line through your 8 releases gains {b:.1%} per release.")
    print(f"  It reaches the leader's current {leader_now:.0%} in about {steps:.0f} more releases.")
    cap, q0, k = fit_curve(ys)
    sse_line = sum((a + b * t - y) ** 2 for t, y in enumerate(ys))
    sse_curve = sum((cap - (cap - q0) * math.exp(-k * t) - y) ** 2 for t, y in enumerate(ys))
    print(f"\n  A saturating curve q(t) = cap - (cap - q0) * e^(-kt) fits the same points (cap ~ {cap:.0%}).")
    print(f"  Squared error of the fit: line {sse_line:.4f}, curve {sse_curve:.4f}. Your data cannot tell them apart.")
    for ahead in (2, 4, 8):
        t = len(ys) - 1 + ahead
        print(f"    in {ahead} releases: line says {a + b * t:5.1%}, curve says {cap - (cap - q0) * math.exp(-k * t):5.1%}")
    print("  The early part of a saturating curve looks like a line. The only evidence about what comes")
    print(f"  later is someone further along: the leader's last 4 releases moved from "
          f"{lead['passed'][-5] / n:.1%} to {leader_now:.1%}.")
    print("  Both teams are on curves; the leader has used up the easy fixes.")

    header("3. THE LEADER: DIMINISHING RETURNS")
    print("  measured = what the dashboard shows; underlying = the true rate (known only because the data")
    print("  is simulated); pw = person-weeks spent on the release")
    print(f"  {'release':8} {'measured':>8} {'change':>7}  {'':12} {'underlying':>10} {'gain':>6} {'effort':>7} {'pw per point':>13}")
    for i, (r, p, w) in enumerate(zip(lead["releases"], lead["passed"], lead["person_weeks"])):
        true = lead["true_rate"][i]
        true_gain = true - lead["true_rate"][i - 1] if i else 0.0
        seen = "" if i == 0 else ("real" if distinguishable(lead["passed"][i - 1], p, n) else "within noise")
        change = f"{(p - lead['passed'][i - 1]) / n:+.1%}" if i else ""
        per_point = f"{w / (true_gain * 100):.0f}" if i else ""
        gain = f"{true_gain:+.1%}" if i else ""
        print(f"  {r:8} {p / n:8.1%} {change:>7}  {seen:12} {true:10.1%} {gain:>6} {w:7} {per_point:>13}")
    print("  The true gain per release shrinks while the effort grows (pw = person-weeks). Most of the")
    print(f"  leader's single-release changes are smaller than the noise of {n} cases. That is a plateau:")
    print("  further progress may need a different model, a new data source, or a product redesign.")
    print("  It is not a reason to stop testing: on a plateau, regressions are what move the number.")

    header("4. THE LAST RELEASE, PER SEGMENT")
    m = d["segment_cases"]
    print(f"  {m} cases per segment. Before -> after, with the 95% interval of 'after':")
    before_all = after_all = 0.0
    for seg, (b0, b1) in d["segments_last_release"].items():
        lo, hi = wilson(round(b1 * m), m)
        delta = b1 - b0
        flag = "improved" if delta > 0.02 else "WORSE" if delta < -0.02 else "same"
        print(f"  {seg:18} {b0:4.0%} -> {b1:4.0%}  [{lo:4.0%}, {hi:4.0%}]  {delta:+5.0%}  {flag}")
        before_all += b0
        after_all += b1
    k_ = len(d["segments_last_release"])
    print(f"  {'all segments':18} {before_all / k_:4.1%} -> {after_all / k_:4.1%}")
    print("  The headline moved up a little. The fix for returns came with quieter losses in shipping")
    print("  and billing. With 150 cases per segment each change alone is close to the noise, which is")
    print("  exactly why regressions in other segments slip through: track segments, not just the total.")

    header("5. AN ACCEPTABLE LEVEL OF MEASURED RISK, NOT 'PERFECT AI'")
    target = d["acceptable_failure_upper_bound"]
    print(f"  Agreed target: the upper end of the 95% interval for the failure rate stays below {target:.0%}.")
    for who, data in (("you", you), ("leader", lead)):
        p = data["passed"][-1]
        lo, hi = wilson(n - p, n)
        print(f"    {who:7} failure rate {(n - p) / n:5.1%}  interval [{lo:.1%}, {hi:.1%}]  "
              f"-> {'meets the target' if hi < target else 'does not meet the target yet'}")
    print("  'When will it be perfect?' has no answer. 'Is the measured risk acceptable for this use?' does.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
