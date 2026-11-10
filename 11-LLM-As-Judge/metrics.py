"""
metrics.py: comparing a judge with humans, standard library only.

- load_jsonl / load_json
- within(a, b, k): share of items where two scores differ by at most k points
- pass_agreement(a, b, at): share of items where both say pass (>= at) or both say fail
- cohen_kappa(a, b): agreement on labels, corrected for chance
- mean_diff(a, b): average of b - a (positive: b scores higher)
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


def within(a: Sequence[float], b: Sequence[float], k: float = 1) -> float:
    return sum(abs(x - y) <= k for x, y in zip(a, b)) / len(a)


def pass_agreement(a: Sequence[float], b: Sequence[float], at: float = 7) -> float:
    return sum((x >= at) == (y >= at) for x, y in zip(a, b)) / len(a)


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    chance = sum(ca[k] / n * cb[k] / n for k in set(ca) | set(cb))
    return 1.0 if chance == 1 else (observed - chance) / (1 - chance)


def mean_diff(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(y - x for x, y in zip(a, b)) / len(a)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)
