"""
agreement.py: how much do raters agree, beyond what chance would give?

Standard library only. Every formula is written out so you can read it.

- percent_agreement: the share of items where two raters gave the same label
- cohen_kappa: agreement between two raters, corrected for chance
- weighted_kappa: the same for ordered scales (0-10): a 7 vs 8 is a smaller miss than 2 vs 9
- fleiss_kappa: agreement among many raters, each item rated by the same number of people
- describe_kappa: a rough reading of the number (Landis & Koch)
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Hashable, List, Sequence


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def percent_agreement(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    """kappa = (observed agreement - chance agreement) / (1 - chance agreement)."""
    n = len(a)
    observed = percent_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    chance = sum(ca[k] / n * cb[k] / n for k in set(ca) | set(cb))
    return 1.0 if chance == 1 else (observed - chance) / (1 - chance)


def weighted_kappa(a: Sequence[int], b: Sequence[int], lo: int = 0, hi: int = 10) -> float:
    """Quadratic-weighted kappa: a disagreement costs (distance / range) squared."""
    n = len(a)
    k = hi - lo + 1
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x - lo][y - lo] += 1 / n
    row = [sum(r) for r in obs]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = ((i - j) / (k - 1)) ** 2
            num += w * obs[i][j]
            den += w * row[i] * col[j]
    return 1.0 if den == 0 else 1 - num / den


def fleiss_kappa(ratings: Sequence[Sequence[Hashable]]) -> float:
    """ratings[i] = the labels that the raters gave to item i (same number of raters per item)."""
    n_items, m = len(ratings), len(ratings[0])
    cats = sorted({c for r in ratings for c in r}, key=str)
    counts = [[Counter(r)[c] for c in cats] for r in ratings]
    p_item = [(sum(x * x for x in row) - m) / (m * (m - 1)) for row in counts]
    p_bar = sum(p_item) / n_items
    p_cat = [sum(row[j] for row in counts) / (n_items * m) for j in range(len(cats))]
    p_e = sum(p * p for p in p_cat)
    return 1.0 if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def describe_kappa(k: float) -> str:
    if k < 0.0:
        return "worse than chance"
    for limit, name in ((0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")):
        if k <= limit:
            return name
    return "almost perfect"


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)
