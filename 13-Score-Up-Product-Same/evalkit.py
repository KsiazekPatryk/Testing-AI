"""
evalkit.py: small tools for honest evaluation bookkeeping, standard library only.

- load_json / load_jsonl
- mean, stdev, ci95 (t-based interval for a mean)
- dcg / ndcg: ranking quality with a discount for position
- fingerprint / diff_packages: what changed between two evaluation packages
- PRODUCT_FIELDS / MEASUREMENT_FIELDS: which changes are the product, which are the measuring instrument
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import stdev
from typing import Dict, List, Sequence

PRODUCT_FIELDS = ("product_version", "prompt", "model", "ranking", "code")
MEASUREMENT_FIELDS = ("dataset", "labels", "expected_results", "rubric", "judge", "retrieval_snapshot",
                      "scorer_code", "query_set")
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23,
       15: 2.13, 20: 2.09, 30: 2.04, 60: 2.00}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def t95(df: int) -> float:
    keys = sorted(T95)
    for k in keys:
        if df <= k:
            return T95[k]
    return 1.96


def ci95(xs: Sequence[float]):
    m = mean(xs)
    half = t95(len(xs) - 1) * stdev(xs) / math.sqrt(len(xs))
    return m - half, m + half


def dcg(gains: Sequence[float], k: int = None) -> float:
    g = gains[:k] if k else gains
    return sum(x / math.log2(i + 2) for i, x in enumerate(g))


def ndcg(gains: Sequence[float], k: int = None) -> float:
    ideal = dcg(sorted(gains, reverse=True), k)
    return dcg(gains, k) / ideal if ideal else 0.0


def fingerprint(package: Dict) -> str:
    return hashlib.sha256(json.dumps(package, sort_keys=True).encode()).hexdigest()[:10]


def diff_packages(a: Dict, b: Dict) -> Dict[str, List[str]]:
    """Split the differences between two packages into product changes and measurement changes."""
    out = {"product": [], "measurement": [], "other": []}
    for k in sorted(set(a) | set(b)):
        if a.get(k) == b.get(k):
            continue
        kind = "product" if k in PRODUCT_FIELDS else "measurement" if k in MEASUREMENT_FIELDS else "other"
        out[kind].append(k)
    return out
