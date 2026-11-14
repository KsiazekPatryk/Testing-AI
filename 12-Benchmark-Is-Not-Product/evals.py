"""
evals.py: the measurement ideas behind public benchmarks, with the standard library only.

- accuracy / per-group accuracy          (MMLU-style multiple choice)
- pass_at_k                              (HumanEval-style: unbiased estimator from n samples, c correct)
- bradley_terry                          (Arena-style: a relative ranking from pairwise votes)
- dcg / ndcg / reciprocal_rank           (ranking metrics: position matters)
- normalize / found_in                   (a simple contamination check: the test text inside training data)
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that at least one of k samples (drawn from n, of which c are correct) passes."""
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def bradley_terry(votes: Iterable[Tuple[str, str]], rounds: int = 200) -> Dict[str, float]:
    """votes: (winner, loser) pairs. Returns a strength per player (higher = preferred), scaled to Elo-like points."""
    wins: Dict[str, int] = defaultdict(int)
    games: Dict[Tuple[str, str], int] = defaultdict(int)
    players: Set[str] = set()
    for w, l in votes:
        wins[w] += 1
        games[tuple(sorted((w, l)))] += 1
        players |= {w, l}
    p = {x: 1.0 for x in players}
    for _ in range(rounds):
        new = {}
        for i in players:
            den = sum(n / (p[i] + p[j]) for (a, b), n in games.items() for j in ((b,) if a == i else (a,) if b == i else ()))
            new[i] = wins[i] / den if den else p[i]
        g = math.exp(sum(math.log(v) for v in new.values()) / len(new))
        p = {k: v / g for k, v in new.items()}
    return {k: 1000 + 400 * math.log10(v) for k, v in p.items()}


def dcg(gains: Sequence[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg(gains: Sequence[float], k: int = 10) -> float:
    ideal = dcg(sorted(gains, reverse=True)[:k])
    return dcg(gains[:k]) / ideal if ideal else 0.0


def reciprocal_rank(relevant: Sequence[bool]) -> float:
    for i, r in enumerate(relevant):
        if r:
            return 1 / (i + 1)
    return 0.0


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def found_in(text: str, corpus: str) -> bool:
    """True if the whole normalized text appears in the normalized corpus.
    Real contamination checks also look for long partial overlaps (e.g. 13 words in a row)."""
    return normalize(text) in normalize(corpus)
