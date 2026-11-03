"""
stats_tools.py: everything the scripts in this folder compute, with the standard library only.

- two_proportions: difference of two rates, z-test p-value, 95% CI (Newcombe, from Wilson intervals)
- two_means: difference of two means from summary numbers (n, mean, sd), z-test and 95% CI
- fisher_exact: exact p-value for a 2x2 table (small counts)
- n_per_group_proportions: cases per version needed to detect p1 -> p2 (with continuity correction)
- n_paired_means / power_paired_means: the same for a mean difference on paired cases
- holm / benjamini_hochberg: corrections for many comparisons
- precision_recall / f_beta: classifier quality when different errors cost differently
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Dict, List, Sequence

N = NormalDist()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def z_crit(alpha: float = 0.05) -> float:
    return N.inv_cdf(1 - alpha / 2)


def wilson(k: int, n: int, z: float = 1.959964) -> Sequence[float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def two_proportions(k1: int, n1: int, k2: int, n2: int) -> Dict:
    """Version 1 vs version 2. diff = p2 - p1."""
    p1, p2 = k1 / n1, k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se if se else 0.0
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p2 - p1
    low = d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    high = d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return {"p1": p1, "p2": p2, "diff": d, "z": z, "p": 2 * (1 - N.cdf(abs(z))), "ci_low": low, "ci_high": high}


def two_means(n1: int, m1: float, sd1: float, n2: int, m2: float, sd2: float) -> Dict:
    se = math.sqrt(sd1 ** 2 / n1 + sd2 ** 2 / n2)
    d = m2 - m1
    z = d / se
    zc = z_crit()
    return {"diff": d, "z": z, "p": 2 * (1 - N.cdf(abs(z))), "ci_low": d - zc * se, "ci_high": d + zc * se}


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided exact p for [[a, b], [c, d]]: sum of tables no more likely than the observed one."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2

    def prob(x: int) -> float:
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    obs = prob(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= obs * (1 + 1e-9)))


def n_per_group_proportions(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Cases per version to detect p1 -> p2 (two-sided), with Fleiss' continuity correction."""
    za, zb = z_crit(alpha), N.inv_cdf(power)
    pbar = (p1 + p2) / 2
    d = abs(p1 - p2)
    n = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / d ** 2
    n_cc = n / 4 * (1 + math.sqrt(1 + 4 / (n * d))) ** 2
    return math.ceil(n_cc)


def power_proportions(p1: float, p2: float, n: int, alpha: float = 0.05) -> float:
    za = z_crit(alpha)
    pbar = (p1 + p2) / 2
    se0 = math.sqrt(2 * pbar * (1 - pbar) / n)
    se1 = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n)
    return N.cdf((abs(p1 - p2) - za * se0) / se1)


def power_paired_means(effect: float, sd_diff: float, n: int, alpha: float = 0.05) -> float:
    """Chance that a paired comparison of n cases reaches p < alpha, if the true effect is `effect`."""
    return N.cdf(abs(effect) / sd_diff * math.sqrt(n) - z_crit(alpha))


def n_paired_means(effect: float, sd_diff: float, alpha: float = 0.05, power: float = 0.8) -> int:
    n = ((z_crit(alpha) + N.inv_cdf(power)) * sd_diff / effect) ** 2
    return math.ceil(n + z_crit(alpha) ** 2 / 2)       # small-sample correction for the t-test


def smallest_detectable_paired(sd_diff: float, n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    return (z_crit(alpha) + N.inv_cdf(power)) * sd_diff / math.sqrt(n)


def p_any_false_alarm(m: int, alpha: float = 0.05) -> float:
    return 1 - (1 - alpha) ** m


def holm(pvalues: Sequence[float], alpha: float = 0.05) -> List[bool]:
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    keep = [False] * len(pvalues)
    m = len(pvalues)
    for rank, i in enumerate(order):
        if pvalues[i] <= alpha / (m - rank):
            keep[i] = True
        else:
            break
    return keep


def benjamini_hochberg(pvalues: Sequence[float], q: float = 0.05) -> List[bool]:
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    cutoff = 0
    for rank, i in enumerate(order, start=1):
        if pvalues[i] <= rank / m * q:
            cutoff = rank
    keep = [False] * m
    for rank, i in enumerate(order, start=1):
        keep[i] = rank <= cutoff
    return keep


def precision_recall(tp: int, fp: int, fn: int) -> Dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r}


def f_beta(precision: float, recall: float, beta: float = 1.0) -> float:
    """beta > 1 weighs recall more, beta < 1 weighs precision more. The weight is beta squared."""
    b2 = beta * beta
    den = b2 * precision + recall
    return (1 + b2) * precision * recall / den if den else 0.0


def p_str(p: float) -> str:
    """'p = 0.003' or 'p < 0.001'."""
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def pp(x: float) -> str:
    """A difference of two rates, in percentage points."""
    return f"{x * 100:+.1f} pp"
