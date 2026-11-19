"""
generate_data.py: writes the generated example data in data/ (always the same content).

Run:  python generate_data.py

  search_eval.jsonl   120 search queries and how the (unchanged) product answers them, with the
                      properties that decide whether each evaluation package counts the answer as a pass
  dashboard.json      nightly scores of the search evaluation, each with the package it was measured with
  rankings.jsonl      30 queries with graded results from two rankers (for ndcg.py)
The red-team cases, the red-team rules and the evaluation packages are hand-written JSON files.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"


def search_eval(rng: random.Random):
    """The product never changes. What differs between packages is how its answers are judged.

      expected_stale      the old expected result is out of date: a correct answer is marked wrong
      snapshot_dependent  the answer cites a document missing from the old search-data snapshot
      citation_weak       right answer, weak citation: rubric v14 fails it, the widened v15 rubric passes it
      judge_borderline    the old judge fails it, the updated (more lenient) judge passes it
      disputed            reviewers could not agree on the right answer (all hard queries)
    """
    plan = (["clean_pass"] * 88 + ["clean_fail"] * 10 + ["expected_stale"] * 1 + ["snapshot_dependent"] * 1
            + ["citation_weak"] * 2 + ["judge_borderline"] * 1 + ["disputed_fail"] * 6 + ["disputed_pass"] * 6
            + ["weak_and_wrong"] * 5)
    rng.shuffle(plan)
    rows = []
    for i, kind in enumerate(plan):
        rows.append({
            "query": f"q-{i + 1:03d}",
            "answer_correct": kind not in ("clean_fail", "disputed_fail", "weak_and_wrong"),
            "expected_stale": kind == "expected_stale",
            "snapshot_dependent": kind == "snapshot_dependent",
            "citation_weak": kind in ("citation_weak", "weak_and_wrong"),
            "judge_borderline": kind in ("judge_borderline", "weak_and_wrong"),
            "disputed": kind.startswith("disputed"),
            "hard": kind.startswith("disputed") or rng.random() < 0.1,
        })
    return rows


def rankings(rng: random.Random):
    """Two rankers on the same 30 queries; both find the same documents, they differ in order."""
    rows = []
    for i in range(30):
        grades = sorted([3, 2, 1, 0, 0, 1, 0, 2, 0, 0], reverse=True)
        a = grades[:]
        if rng.random() < 0.3:                        # A sometimes swaps two lower results
            a[3], a[5] = a[5], a[3]
        b = grades[:]
        if rng.random() < 0.6:                        # B often pushes the best result down
            b.insert(rng.choice([2, 3, 4]), b.pop(0))
        rows.append({"query": f"r-{i + 1:03d}", "ranker_a": a, "ranker_b": b,
                     "latency_ms_a": rng.randint(80, 140), "latency_ms_b": rng.randint(60, 110)})
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    with open(DATA / "search_eval.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in search_eval(random.Random(13)):
            f.write(json.dumps(r) + "\n")
    with open(DATA / "rankings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rankings(random.Random(13)):
            f.write(json.dumps(r) + "\n")
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
