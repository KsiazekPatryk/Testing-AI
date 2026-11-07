"""
agreement.py: measuring agreement between raters, with the standard library only.

- percent_agreement: raw share of items where two raters gave the same label
- cohen_kappa: two raters, agreement corrected for chance (returns the parts too)
- krippendorff_alpha: any number of raters, missing ratings allowed, nominal / ordinal / interval scales
- agreement_pattern: for 3 raters: all agree, two agree, nobody agrees
- entropy: how spread out a distribution is (in bits)
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Callable, Dict, Hashable, List, Optional, Sequence

Rating = Optional[Hashable]


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv(path) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def percent_agreement(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> Dict[str, float]:
    """kappa = (observed - chance) / (1 - chance). Chance = sum over labels of p_A(label) * p_B(label)."""
    n = len(a)
    observed = percent_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    chance = sum(ca[k] / n * cb[k] / n for k in set(ca) | set(cb))
    kappa = 1.0 if chance == 1 else (observed - chance) / (1 - chance)
    return {"observed": observed, "chance": chance, "kappa": kappa}


def kappa_from_table(both_yes: int, both_no: int, a_yes_b_no: int, a_no_b_yes: int) -> Dict[str, float]:
    a = ["yes"] * (both_yes + a_yes_b_no) + ["no"] * (both_no + a_no_b_yes)
    b = ["yes"] * both_yes + ["no"] * a_yes_b_no + ["no"] * both_no + ["yes"] * a_no_b_yes
    return cohen_kappa(a, b)


def _metric(kind: str, values: Sequence[Hashable]) -> Callable[[Hashable, Hashable], float]:
    if kind == "nominal":
        return lambda x, y: 0.0 if x == y else 1.0
    if kind == "interval":
        return lambda x, y: (float(x) - float(y)) ** 2
    if kind == "ordinal":
        # Krippendorff's ordinal metric: distance grows with how many values lie between x and y.
        freq = Counter(values)
        order = sorted(freq)
        pos = {v: i for i, v in enumerate(order)}

        def d(x, y):
            if x == y:
                return 0.0
            i, j = sorted((pos[x], pos[y]))
            s = sum(freq[order[k]] for k in range(i, j + 1)) - (freq[order[i]] + freq[order[j]]) / 2
            return s * s
        return d
    raise ValueError(kind)


def krippendorff_alpha(units: Sequence[Sequence[Rating]], level: str = "nominal") -> Dict[str, float]:
    """units[i] = ratings of item i, one per rater, None where a rater did not rate the item.

    alpha = 1 - observed disagreement / expected disagreement
    Items rated by fewer than two raters are dropped (they cannot show agreement or disagreement).
    """
    pairable = [[v for v in u if v is not None] for u in units]
    pairable = [u for u in pairable if len(u) >= 2]
    values = [v for u in pairable for v in u]
    n = len(values)
    d = _metric(level, values)
    observed = sum(sum(d(x, y) for i, x in enumerate(u) for j, y in enumerate(u) if i != j) / (len(u) - 1)
                   for u in pairable) / n
    expected = sum(d(x, y) for i, x in enumerate(values) for j, y in enumerate(values) if i != j) / (n * (n - 1))
    alpha = 1.0 if expected == 0 else 1 - observed / expected
    return {"observed": observed, "expected": expected, "alpha": alpha, "values": n}


def agreement_pattern(labels: Sequence[Hashable]) -> str:
    """For one item rated by 3 raters: 'all', 'two' or 'none'."""
    top = Counter(labels).most_common(1)[0][1]
    return "all" if top == len(labels) else "two" if top >= 2 else "none"


def pairwise_agreement(rows: Sequence[Sequence[Hashable]]) -> float:
    """Share of rater pairs, over all items, that gave the same label."""
    agree = total = 0
    for labels in rows:
        for x, y in combinations(labels, 2):
            agree += x == y
            total += 1
    return agree / total


def entropy(probs: Sequence[float]) -> float:
    return -sum(p * math.log2(p) for p in probs if p > 0)


def describe(k: float) -> str:
    if k < 0:
        return "worse than chance"
    for limit, name in ((0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")):
        if k <= limit:
            return name
    return "almost perfect"
