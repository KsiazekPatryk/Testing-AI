"""
stats_tests.py: every statistical test from the post, written out with the standard library.

No scipy needed. If you have it, the results match scipy.stats to the shown precision:
  paired_t      ~ scipy.stats.ttest_rel        welch_t   ~ scipy.stats.ttest_ind(equal_var=False)
  chi_square    ~ scipy.stats.chi2_contingency(correction=False)
  mcnemar_exact ~ statsmodels mcnemar(exact=True)
  wilcoxon / mann_whitney use the normal approximation (fine for n above ~20).
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean, stdev
from typing import Callable, Dict, List, Sequence, Tuple

# --- Distributions -----------------------------------------------------------


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-12:
            break
    return h


def betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def t_two_sided_p(t: float, df: float) -> float:
    return betai(df / 2, 0.5, df / (df + t * t))


def t_critical(df: float, alpha: float = 0.05) -> float:
    """Two-sided critical value, found by bisection."""
    lo, hi = 0.0, 100.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if t_two_sided_p(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def chi2_sf(x: float, df: int) -> float:
    """P(chi-square with df degrees of freedom > x): the regularized upper incomplete gamma."""
    a, y = df / 2, x / 2
    if y <= 0:
        return 1.0
    if y < a + 1:                                   # series
        term = total = 1 / a
        for n in range(1, 500):
            term *= y / (a + n)
            total += term
            if term < total * 1e-14:
                break
        return 1 - total * math.exp(-y + a * math.log(y) - math.lgamma(a))
    b, c, d = y + 1 - a, 1e300, 1 / (y + 1 - a)      # continued fraction
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / d if abs(d) > 1e-300 else 1e300
        c = b + an / c
        h *= d * c
        if abs(d * c - 1) < 1e-14:
            break
    return math.exp(-y + a * math.log(y) - math.lgamma(a)) * h


def normal_two_sided_p(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


# --- Tests -------------------------------------------------------------------


def paired_t(a: Sequence[float], b: Sequence[float]) -> Dict[str, float]:
    """Same cases through A and B: a one-sample t-test on the differences B − A."""
    d = [y - x for x, y in zip(a, b)]
    n, md, sd = len(d), mean(d), stdev(d)
    se = sd / math.sqrt(n)
    t = md / se if se else float("inf")
    crit = t_critical(n - 1)
    return {"n": n, "diff": md, "t": t, "df": n - 1, "p": t_two_sided_p(t, n - 1),
            "ci_low": md - crit * se, "ci_high": md + crit * se}


def welch_t(a: Sequence[float], b: Sequence[float]) -> Dict[str, float]:
    """Different cases for A and B: Welch's t-test (does not assume equal variances)."""
    na, nb = len(a), len(b)
    va, vb = stdev(a) ** 2 / na, stdev(b) ** 2 / nb
    se = math.sqrt(va + vb)
    t = (mean(b) - mean(a)) / se
    df = (va + vb) ** 2 / (va ** 2 / (na - 1) + vb ** 2 / (nb - 1))
    crit = t_critical(df)
    diff = mean(b) - mean(a)
    return {"diff": diff, "t": t, "df": df, "p": t_two_sided_p(t, df),
            "ci_low": diff - crit * se, "ci_high": diff + crit * se}


def chi_square(table: List[List[int]]) -> Dict[str, object]:
    """Chi-square test of independence. Returns expected counts, χ², df and p."""
    rows, cols = len(table), len(table[0])
    rsum = [sum(r) for r in table]
    csum = [sum(table[i][j] for i in range(rows)) for j in range(cols)]
    total = sum(rsum)
    expected = [[rsum[i] * csum[j] / total for j in range(cols)] for i in range(rows)]
    chi2 = sum((table[i][j] - expected[i][j]) ** 2 / expected[i][j]
               for i in range(rows) for j in range(cols))
    df = (rows - 1) * (cols - 1)
    return {"expected": expected, "chi2": chi2, "df": df, "p": chi2_sf(chi2, df)}


def binomial_tail(k: int, n: int) -> float:
    """P(X ≥ k) for X ~ Binomial(n, 0.5): how often a fair coin gives k or more heads."""
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n


def sign_test(wins: int, losses: int) -> Dict[str, float]:
    n = wins + losses
    one = binomial_tail(wins, n)
    two = min(1.0, 2 * min(binomial_tail(wins, n), binomial_tail(losses, n)))
    return {"n": n, "p_one_sided": one, "p_two_sided": two}


def mcnemar_exact(a: Sequence[int], b: Sequence[int]) -> Dict[str, float]:
    """Paired pass/fail: only the cases where A and B differ count."""
    b_only = sum(1 for x, y in zip(a, b) if y and not x)
    a_only = sum(1 for x, y in zip(a, b) if x and not y)
    res = sign_test(b_only, a_only)
    return {"b_fixed": b_only, "b_broke": a_only, "p": res["p_two_sided"]}


def fisher_exact(table: List[List[int]]) -> float:
    """Two-sided Fisher exact test for a 2×2 table: for small counts."""
    (a, b), (c, d) = table
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def prob(x: int) -> float:
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    observed = prob(a)
    return min(1.0, sum(prob(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1)
                        if prob(x) <= observed * (1 + 1e-9)))


def _ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def wilcoxon_signed_rank(a: Sequence[float], b: Sequence[float]) -> Dict[str, float]:
    """Paired ordinal scores: ranks of |B − A|, zero differences dropped (normal approximation)."""
    d = [y - x for x, y in zip(a, b) if y != x]
    n = len(d)
    r = _ranks([abs(x) for x in d])
    w_plus = sum(rk for rk, x in zip(r, d) if x > 0)
    mu = n * (n + 1) / 4
    ties = {}
    for x in (abs(v) for v in d):
        ties[x] = ties.get(x, 0) + 1
    var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in ties.values()) / 48
    z = (w_plus - mu) / math.sqrt(var)
    return {"n_nonzero": n, "w_plus": w_plus, "z": z, "p": normal_two_sided_p(z)}


def mann_whitney(a: Sequence[float], b: Sequence[float]) -> Dict[str, float]:
    """Independent ordinal scores: rank all values together (normal approximation)."""
    na, nb = len(a), len(b)
    r = _ranks(list(a) + list(b))
    u = sum(r[na:]) - nb * (nb + 1) / 2
    mu = na * nb / 2
    counts: Dict[float, int] = {}
    for v in list(a) + list(b):
        counts[v] = counts.get(v, 0) + 1
    n = na + nb
    var = na * nb / 12 * ((n + 1) - sum(t ** 3 - t for t in counts.values()) / (n * (n - 1)))
    z = (u - mu) / math.sqrt(var)
    return {"u": u, "z": z, "p": normal_two_sided_p(z), "prob_b_higher": u / (na * nb)}


def permutation_paired(a: Sequence[float], b: Sequence[float], *, rounds: int = 10000,
                       seed: int = 0) -> float:
    """Under H0 the sign of each difference is a coin flip. Flip them and count."""
    rng = random.Random(seed)
    d = [y - x for x, y in zip(a, b)]
    observed = abs(mean(d))
    hits = sum(abs(mean([x if rng.random() < 0.5 else -x for x in d])) >= observed - 1e-12
               for _ in range(rounds))
    return (hits + 1) / (rounds + 1)


def bootstrap_ci(values: Sequence[float], stat: Callable[[Sequence[float]], float] = mean, *,
                 rounds: int = 5000, seed: int = 0) -> Tuple[float, float]:
    """Resample the units with replacement; the middle 95% of the statistic is the interval."""
    rng = random.Random(seed)
    n = len(values)
    sims = sorted(stat([values[rng.randrange(n)] for _ in range(n)]) for _ in range(rounds))
    return sims[int(0.025 * rounds)], sims[int(0.975 * rounds) - 1]


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def fmt_p(p: float) -> str:
    return f"{p:.3f}" if p >= 0.001 else "< 0.001"
