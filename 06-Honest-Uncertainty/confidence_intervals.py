"""
confidence_intervals.py: "about", said with discipline.

Run:  python confidence_intervals.py
      python confidence_intervals.py --passed 47 --total 50
      python confidence_intervals.py --mean 8.1 --sd 1.4 --n 100

A confidence interval adds humility to a measurement. "92% passed" becomes
"92% passed in the sample; the approximate 95% confidence interval is 87-97%".

    interval = estimate ± 1.96 × standard error
    pass/fail:    SE = √( p × (1 − p) / n )
    mean score:   SE = standard deviation / √n
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from statistics import mean, stdev

from stats import load_jsonl, mean_ci, multiplier, proportion_ci, wilson

HERE = Path(__file__).parent


def explain_proportion(k: int, n: int) -> None:
    p = k / n
    se = math.sqrt(p * (1 - p) / n)
    _, lo, hi = proportion_ci(k, n)
    wlo, whi = wilson(k, n)
    print(f"PASS/FAIL: {k} of {n} passed")
    print(f"  p  = {k}/{n} = {p:.3f}")
    print(f"  SE = √({p:.2f} × {1 - p:.2f} / {n}) = {se:.4f}")
    print(f"  margin = 1.96 × {se:.4f} = {1.96 * se:.4f}")
    print(f"  interval = {lo:.3f}–{hi:.3f}, about {lo:.0%}–{hi:.0%}")
    print(f"  Wilson interval (better for small n or rates near 0% or 100%): {wlo:.0%}–{whi:.0%}")
    if k in (0, n) or n < 30:
        print("  ! The simple formula breaks down here (tiny sample or a rate at 0% or 100%).")
        print(f"  Report: \"{p:.0%} passed in the sample; 95% CI {wlo:.0%}–{whi:.0%} (Wilson).\"\n")
    else:
        print(f"  Report: \"{p:.0%} passed in the sample; approximate 95% CI {lo:.0%}–{hi:.0%}.\"\n")


def explain_mean(m: float, sd: float, n: int) -> None:
    se = sd / math.sqrt(n)
    k = multiplier(n)
    print(f"MEAN SCORE (0-10): mean {m}, standard deviation {sd}, n = {n}")
    print(f"  SE = {sd} / √{n} = {se:.3f}")
    print(f"  margin = {k:.2f} × {se:.3f} = {k * se:.2f}" + ("" if k == 1.96 else "   (t multiplier: small sample)"))
    print(f"  Report: \"mean score {m}, approximate 95% CI {m - k * se:.1f}–{m + k * se:.1f}.\"\n")


def sample_size_demo() -> None:
    rows = load_jsonl(HERE / "data" / "scores.jsonl")
    scores = [r["score"] for r in rows]
    rng = random.Random(7)
    print("SAMPLE SIZE CHANGES THE WIDTH, NOT NECESSARILY THE MEAN")
    print(f"  (resampling the {len(scores)} scores in data/scores.jsonl)")
    print(f"  {'n':>5} {'mean':>6} {'95% CI':>13} {'width':>6}")
    for n in (5, 20, 50, 200, 1000):
        sample = [rng.choice(scores) for _ in range(n)]
        m, lo, hi = mean_ci(sample)
        print(f"  {n:>5} {m:>6.2f} {lo:>6.2f}–{hi:<6.2f} {hi - lo:>5.2f}")
    print("  With 20 samples the interval is wide; with 200 it narrows. The mean barely moves,")
    print("  but the confidence in it grows.\n")
    print("  Note: with n = 5 the multiplier is 2.78, not 1.96 (t distribution).")
    print("  For release decisions, state which method you used.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Confidence intervals, step by step.")
    ap.add_argument("--passed", type=int, default=92)
    ap.add_argument("--total", type=int, default=100)
    ap.add_argument("--mean", type=float, default=8.1)
    ap.add_argument("--sd", type=float, default=1.4)
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    explain_proportion(a.passed, a.total)
    explain_mean(a.mean, a.sd, a.n)
    sample_size_demo()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
