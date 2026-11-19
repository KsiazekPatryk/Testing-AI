"""
ndcg.py: it matters not only what is on the list, but where.

Run:  python ndcg.py
      python ndcg.py --order 2 3 1 0

Users do not read results democratically. They start at the top and give the first positions
disproportionate attention. NDCG (normalized discounted cumulative gain) respects that:
  1. relevance grades: 0 not relevant, 1 somewhat, 2 relevant, 3 highly relevant
  2. a discount for position: relevance at the top is worth more than the same relevance lower down
  3. normalization against the ideal order for that query, so the result is between 0 and 1

  DCG@k  = sum over positions i = 1..k of relevance_i / log2(i + 1)
  NDCG@k = DCG@k / IDCG@k   (IDCG = DCG of the ideal order)
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import List, Sequence

from evalkit import dcg, load_jsonl, mean, ndcg

HERE = Path(__file__).parent
DOCS = {3: "official admin documentation", 2: "recent help-forum answer", 1: "policy page", 0: "random blog post"}


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def step_by_step(order: Sequence[int]) -> None:
    header(f"STEP BY STEP FOR THE ORDER {list(order)}")
    for i, g in enumerate(order, 1):
        print(f"  position {i}: {DOCS.get(g, '?'):30} {g} / log2({i + 1}) = {g / math.log2(i + 1):.3f}")
    ideal = sorted(order, reverse=True)
    print(f"  DCG@{len(order)} = {dcg(order):.3f}    IDCG@{len(order)} (order {ideal}) = {dcg(ideal):.3f}")
    print(f"  NDCG@{len(order)} = {dcg(order):.3f} / {dcg(ideal):.3f} = {ndcg(order):.2f}")


def post_example() -> None:
    header("THE POST'S EXAMPLE: HOW DO I TURN OFF A FEATURE ON MY CHILD'S SCHOOL ACCOUNT?")
    for g, d in DOCS.items():
        print(f"  {g}  {d}")
    print()
    for order, note in (([3, 2, 1, 0], "ideal"), ([3, 2, 0, 1], "last two swapped"),
                        ([2, 3, 1, 0], "first two swapped"), ([1, 0, 2, 3], "documentation last"),
                        ([0, 1, 2, 3], "reversed")):
        print(f"  {str(order):14} {note:20} NDCG@4 = {ndcg(order):.2f}")
    print("  In every variant the right answer is on the list. But with the official documentation")
    print("  under the blog and the policy page, the system failed at what the user actually sees.")
    print("  A swap at the bottom costs almost nothing; a swap at the top costs a lot.")


def precision_recall_at(grades: List[int], k: int, total_relevant: int):
    top = grades[:k]
    hits = sum(g >= 2 for g in top)
    return hits / k, hits / total_relevant if total_relevant else 0.0


def two_rankers() -> None:
    rows = load_jsonl(HERE / "data" / "rankings.jsonl")
    header(f"TWO RANKERS ON {len(rows)} QUERIES: CHOOSE @k ON PURPOSE, AND LOOK AT MORE THAN ONE METRIC")
    print(f"  {'ranker':7} {'NDCG@3':>7} {'NDCG@10':>8} {'P@3':>6} {'R@10':>6} {'latency':>9}")
    for name in ("a", "b"):
        g = [r[f"ranker_{name}"] for r in rows]
        rel = [sum(x >= 2 for x in q) for q in g]
        p3 = mean([precision_recall_at(q, 3, n)[0] for q, n in zip(g, rel)])
        r10 = mean([precision_recall_at(q, 10, n)[1] for q, n in zip(g, rel)])
        print(f"  {name.upper():7} {mean([ndcg(q, 3) for q in g]):>7.2f} {mean([ndcg(q, 10) for q in g]):>8.2f} "
              f"{p3:>6.2f} {r10:>6.2f} {mean([r['latency_ms_' + name] for r in rows]):>6.0f} ms")
    print("  Both rankers find every relevant document (recall@10 = 1.00), so recall alone sees no")
    print("  difference. NDCG@3 does: B often pushes the best result down. B is faster, though: a")
    print("  trade-off for the product team, not something one number can settle.")
    print("  Other metrics worth tracking: zero-result rate, diversity of the top results.")


def main() -> None:
    ap = argparse.ArgumentParser(description="NDCG, step by step.")
    ap.add_argument("--order", type=int, nargs="+", default=[1, 0, 2, 3])
    a = ap.parse_args()
    post_example()
    step_by_step(a.order)
    two_rankers()
    print("\n  Do not copy NDCG blindly into chatbots or robots. Use the idea only where the system really")
    print("  ranks evidence, sources, files or actions. The bigger lesson: you need a scoring function")
    print("  that matches how the product is really used.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
