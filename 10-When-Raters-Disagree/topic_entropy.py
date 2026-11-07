"""
topic_entropy.py: when a query has many reasonable meanings, the best result set is not the one
with the highest average rating.

Run:  python topic_entropy.py

  entropy (bits) = how spread out the interpretations of a query are
    low:  one obvious answer         ("python list append")
    high: many plausible readings   ("best agent framework to replace my QA team")

For the high-entropy query, three result sets are compared:
  vendor_wall  ten near-identical vendor pages: consistent, narrow, commercially biased
  balanced     one strong result per main interpretation
  lost         "diverse", but the official docs and the evidence are buried under hot takes
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

from agreement import entropy, load_json

HERE = Path(__file__).parent
STRONG = 7          # a result rated 7+ counts as a strong answer for its interpretation
TOP = 5             # what most users actually look at


def coverage(results: List[Dict], intents: Dict[str, float], top: int = TOP) -> float:
    """Share of users whose interpretation has a strong result in the top N."""
    covered = {r["covers"] for r in results[:top] if r["rating"] >= STRONG}
    return sum(p for name, p in intents.items() if name in covered)


def main() -> None:
    data = load_json(HERE / "data" / "search_results.json")
    print("=" * 78 + "\nTOPIC ENTROPY\n" + "=" * 78)
    for q in data["queries"]:
        probs = list(q["interpretations"].values())
        h = entropy(probs)
        top = max(q["interpretations"], key=q["interpretations"].get)
        print(f"  {h:4.2f} bits  \"{q['query']}\"   ({len(probs)} readings, most common: {top} {max(probs):.0%})")
    print(f"  Maximum for 5 equally likely readings: {entropy([0.2] * 5):.2f} bits.")
    print("  Low entropy: reviewers should agree, and disagreement is a warning.")
    print("  High entropy: reviewers who imagine different users will disagree, legitimately.")

    q = data["queries"][-1]
    intents = q["interpretations"]
    print("\n" + "=" * 78 + f"\nTHREE RESULT SETS FOR \"{q['query']}\"\n" + "=" * 78)
    print(f"  {'set':12} {'mean rating':>11} {'readings in top ' + str(TOP):>18} {'users served':>13}  first official docs")
    for name, results in data["result_sets"].items():
        readings = len({r['covers'] for r in results[:TOP]})
        docs = next((i + 1 for i, r in enumerate(results) if r["kind"] == "official_docs"), None)
        print(f"  {name:12} {mean(r['rating'] for r in results):>11.1f} {readings:>18} "
              f"{coverage(results, intents):>12.0%}  {('rank ' + str(docs)) if docs else 'none'}")
    print("\n  vendor_wall has the HIGHEST average rating: each page looks fine on its own. But it serves")
    print("  one reading of the query, from one commercial angle.")
    print("  balanced has one strong result per main interpretation: documentation, a comparison,")
    print("  a benchmark, a warning and a case study.")
    print("  lost is 'diverse' only on paper: the official docs sit at rank 8, under hot takes.")
    print("  Diversity is not a goal on its own. Each interpretation needs its STRONGEST result.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
