"""
stats.py: the few statistics this folder needs, written out so you can read them.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List, Tuple

# Two-sided 95% t multipliers for small samples (degrees of freedom -> t).
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26,
       10: 2.23, 15: 2.13, 20: 2.09, 25: 2.06, 30: 2.04}


def t_multiplier(n: int) -> float:
    df = n - 1
    if df >= 30:
        return 1.96
    return T95[max(k for k in T95 if k <= df)] if df >= 1 else float("inf")


def mean_ci(values: List[float]) -> Tuple[float, float, float]:
    """Mean with an approximate 95% confidence interval: mean ± t × sd / √n."""
    m = mean(values)
    if len(values) < 2:
        return m, float("-inf"), float("inf")
    margin = t_multiplier(len(values)) * stdev(values) / math.sqrt(len(values))
    return m, m - margin, m + margin


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% confidence interval for a rate (Wilson method)."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def by_slice(rows: List[Dict]) -> Dict[str, List[Dict]]:
    out: Dict[str, List[Dict]] = {}
    for r in rows:
        out.setdefault(r["slice"], []).append(r)
    return out


def load(path: Path) -> List[Dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
