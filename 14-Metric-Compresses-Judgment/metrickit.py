"""
metrickit.py: small tools for building a metric you can defend, standard library only.

- load_json / load_jsonl
- weighted_score / contributions: a weighted sum of 0-1 criterion scores, with the weights checked
- fingerprint: a short hash, so you can prove the weights were frozen before the results
- wilson: a 95% interval for a pass rate (works near 0% and 100%, unlike the normal approximation)
- contrast_ratio: the WCAG contrast ratio between two colours
- percentile_rank: where a value sits inside a peer group
- ngrams / overlap: word n-gram overlap, a cheap contamination check
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def check_weights(weights: Dict[str, float]) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"weights must sum to 1.0, they sum to {total:.3f}")
    if any(w < 0 for w in weights.values()):
        raise ValueError("weights must not be negative")


def contributions(scores: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
    """How many points of the final score each criterion brings."""
    check_weights(weights)
    missing = set(weights) - set(scores)
    if missing:
        raise ValueError(f"no score for: {', '.join(sorted(missing))}")
    return {k: weights[k] * scores[k] for k in weights}


def weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(contributions(scores, weights).values())


def fingerprint(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:12]


def wilson(passed: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = passed / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2.x contrast ratio. Body text needs at least 4.5, large text at least 3.0."""
    a, b = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def percentile_rank(value: float, peers: Iterable[float], lower_is_better: bool = False) -> float:
    """Share of peers that this value beats (0.0 = worst of the group, 1.0 = best)."""
    peers = list(peers)
    beaten = sum(1 for p in peers if (value < p if lower_is_better else value > p))
    return beaten / len(peers)


def ngrams(text: str, n: int = 8) -> Set[Tuple[str, ...]]:
    words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def overlap(text: str, corpus: Set[Tuple[str, ...]], n: int = 8) -> float:
    """Share of the text's word n-grams that also appear in the corpus."""
    grams = ngrams(text, n)
    return len(grams & corpus) / len(grams) if grams else 0.0
