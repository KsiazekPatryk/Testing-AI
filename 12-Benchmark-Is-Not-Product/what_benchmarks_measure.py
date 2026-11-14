"""
what_benchmarks_measure.py: benchmark names appear side by side as if they measured the same thing.
They do not.

Run:  python what_benchmarks_measure.py
      python what_benchmarks_measure.py --k 5

  1. the eight benchmarks from the post: unit of work, oracle, metric, blind spot
  2. MMLU-style accuracy: the overall number hides weak subjects
  3. HumanEval-style pass@k: the same model, a different k, a different number
  4. Arena-style ranking from pairwise votes: it can reward length over truth
Accuracy, pass@k, resolved rate and an Arena rating are not four versions of one number.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from evals import bradley_terry, load_json, load_jsonl, mean, pass_at_k

HERE = Path(__file__).parent


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def table() -> None:
    header("1. EIGHT BENCHMARKS, EIGHT DIFFERENT QUESTIONS")
    for b in load_json(HERE / "data" / "benchmarks.json")["benchmarks"]:
        print(f"  {b['name']}")
        print(f"    unit of work: {b['unit_of_work']:16} oracle: {b['oracle']:24} metric: {b['metric']}")
        print(f"    does not see: {b['blind_spot']}")


def mmlu() -> None:
    rows = load_jsonl(HERE / "data" / "mc_results.jsonl")
    header("2. MULTIPLE-CHOICE ACCURACY: THE AVERAGE HIDES THE WEAK SUBJECTS")
    by = defaultdict(list)
    for r in rows:
        by[r["subject"]].append(r["correct"])
    overall = mean([r["correct"] for r in rows])
    print(f"  overall accuracy: {overall:.1%} on {len(rows):,} questions")
    for s, v in sorted(by.items(), key=lambda kv: mean(kv[1])):
        acc = mean(v)
        print(f"    {s:20} {acc:5.0%}  {'#' * int(acc * 40)}{'   <- weak' if acc < overall - 0.1 else ''}")
    print("  If your product answers questions about law or security, the headline number tells you little.")


def humaneval(k: int) -> None:
    rows = load_jsonl(HERE / "data" / "code_samples.jsonl")
    header(f"3. PASS@K: 40 PROBLEMS, 10 SAMPLES EACH")
    for kk in sorted({1, 5, 10, k}):
        print(f"  pass@{kk:<2} = {mean([pass_at_k(r['n_samples'], r['n_correct'], kk) for r in rows]):.1%}")
    print("  Same model, same problems. pass@10 asks 'can it get there in ten tries?', pass@1 asks")
    print("  'does it get there on the first try?'. Your user usually gets the first try.")


def arena() -> None:
    votes = load_jsonl(HERE / "data" / "arena_votes.jsonl")
    header(f"4. PAIRWISE PREFERENCE: {len(votes):,} VOTES BETWEEN THREE MODELS")
    pairs = [(v["winner"], v["b"] if v["winner"] == v["a"] else v["a"]) for v in votes]
    rating = bradley_terry(pairs)
    stats = defaultdict(lambda: {"len": [], "correct": []})
    for v in votes:
        for side in ("a", "b"):
            stats[v[side]]["len"].append(v[f"length_{side}"])
            stats[v[side]]["correct"].append(v[f"correct_{side}"])
    print(f"  {'model':10} {'rating':>7} {'avg length':>11} {'factually correct':>18}")
    for m, r in sorted(rating.items(), key=lambda kv: -kv[1]):
        print(f"  {m:10} {r:>7.0f} {mean(stats[m]['len']):>8.0f} ch {mean(stats[m]['correct']):>18.0%}")
    longer = [v for v in votes if v["length_a"] != v["length_b"]]
    longer_won = mean([(v["winner"] == v["a"]) == (v["length_a"] > v["length_b"]) for v in longer])
    print(f"\n  The longer answer won {longer_won:.0%} of the votes. The top-rated model is the least often right.")
    print("  A relative ranking of preferences, not a measure of truth.")


def main() -> None:
    ap = argparse.ArgumentParser(description="What benchmarks actually measure.")
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args()
    table()
    mmlu()
    humaneval(a.k)
    arena()
    print("\n  Accuracy, pass@k, resolved rate and an Arena rating answer different questions with different")
    print("  methods. Do not compare them as if they were one number.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
