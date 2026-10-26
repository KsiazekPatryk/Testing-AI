"""
stats.py: every formula from the post, written out so you can read it.

Nothing here needs a package. If you prefer a spreadsheet: the standard deviation is
STDEV.S, the mean is AVERAGE, the median is MEDIAN, a percentile is PERCENTILE.INC.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Sequence, Tuple

Z95 = 1.96
# Two-sided 95% t multipliers for small samples (degrees of freedom -> t).
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26,
       10: 2.23, 12: 2.18, 15: 2.13, 20: 2.09, 25: 2.06, 30: 2.04}


def multiplier(n: int) -> float:
    """1.96 for large samples; a bigger t multiplier for small ones."""
    df = n - 1
    if df >= 30:
        return Z95
    if df < 1:
        return float("inf")
    return T95[max(k for k in T95 if k <= df)]


def percentile(values: Sequence[float], p: float) -> float:
    """Linear interpolation, the same as PERCENTILE.INC in a spreadsheet."""
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def six_numbers(values: Sequence[float], fails: Sequence[bool]) -> Dict[str, float]:
    return {
        "n": len(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "failure_rate": sum(fails) / len(fails),
        "std_dev": stdev(values) if len(values) > 1 else 0.0,
        "p95": percentile(values, 95),
    }


def proportion_ci(k: int, n: int) -> Tuple[float, float, float]:
    """The simple formula from the post: p ± 1.96 × √(p(1−p)/n). Returns (p, low, high)."""
    p = k / n
    se = math.sqrt(p * (1 - p) / n)
    return p, max(0.0, p - Z95 * se), min(1.0, p + Z95 * se)


def wilson(k: int, n: int) -> Tuple[float, float]:
    """Better for small samples and for rates near 0% or 100%."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + Z95 ** 2 / n
    centre = (p + Z95 ** 2 / (2 * n)) / denom
    margin = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def mean_ci(values: Sequence[float]) -> Tuple[float, float, float]:
    """mean ± multiplier × sd / √n. Returns (mean, low, high)."""
    m = mean(values)
    if len(values) < 2:
        return m, float("-inf"), float("inf")
    margin = multiplier(len(values)) * stdev(values) / math.sqrt(len(values))
    return m, m - margin, m + margin


def paired_difference_ci(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    """Interval for the mean of (B − A), computed case by case on the same test cases."""
    return mean_ci([y - x for x, y in zip(a, b)])


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def group(rows: List[Dict], key: str) -> Dict[str, List[Dict]]:
    out: Dict[str, List[Dict]] = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return out
