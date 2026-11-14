"""
benchmarks_rot.py: benchmarks go stale.

Run:  python benchmarks_rot.py

  1. contamination: questions and answers get published, then scraped into training data.
     The model may literally have read the test before taking it.
       - compare the original questions with paraphrases and fresh questions of the same kind
       - look for the benchmark's text in the training data
  2. brittle agent benchmarks: the environment changes, a dialog pops up, and a benchmark that
     expects ONE path fails runs that completed the task another way (and passes some that did not)
"""

from __future__ import annotations

import sys
from pathlib import Path

from evals import found_in, load_jsonl, mean

HERE = Path(__file__).parent


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def contamination() -> None:
    rows = load_jsonl(HERE / "data" / "contamination.jsonl")
    corpus = (HERE / "data" / "training_snippets.txt").read_text(encoding="utf-8")
    for r in rows:
        r["leaked"] = found_in(r["question"], corpus)
    header(f"1. CONTAMINATION: {len(rows)} PUBLIC BENCHMARK QUESTIONS")
    print(f"  {'group':38} {'n':>4} {'original':>9} {'paraphrase':>11} {'fresh':>6}")
    groups = [("found verbatim in the training data", [r for r in rows if r["leaked"]]),
              ("not found", [r for r in rows if not r["leaked"]])]
    for name, g in groups:
        print(f"  {name:38} {len(g):>4} {mean([r['correct_original'] for r in g]):>9.0%} "
              f"{mean([r['correct_paraphrase'] for r in g]):>11.0%} {mean([r['correct_fresh'] for r in g]):>6.0%}")
    seen = groups[0][1]
    gap = mean([r["correct_original"] for r in seen]) - mean([r["correct_paraphrase"] for r in seen])
    print(f"\n  On questions it has seen, the model drops {gap * 100:.0f} points as soon as the wording changes.")
    print("  That gap is knowledge of the exam, not skill. Fresh and paraphrased questions show the skill.")
    example = seen[0]
    print(f"  Example found verbatim in the scraped data: \"{example['question'][:70]}...\"")


def agents() -> None:
    rows = load_jsonl(HERE / "data" / "agent_runs.jsonl")
    header(f"2. A BRITTLE AGENT BENCHMARK: {len(rows)} BROWSER TASKS")
    by_path = [r["actual_path"] == r["expected_path"] for r in rows]
    by_state = [r["final_state_ok"] for r in rows]
    print(f"  graded by the expected click path:  {mean(by_path):.0%} success")
    print(f"  graded by the final state:          {mean(by_state):.0%} success")
    false_fail = [r for r, p, s in zip(rows, by_path, by_state) if s and not p]
    false_pass = [r for r, p, s in zip(rows, by_path, by_state) if p and not s]
    notes = {}
    for r in false_fail:
        notes[r["note"]] = notes.get(r["note"], 0) + 1
    print(f"\n  {len(false_fail)} runs FAILED by the path check that actually completed the task:")
    for n, c in notes.items():
        print(f"    {c:>3}  {n}")
    print(f"  {len(false_pass)} runs PASSED by the path check that did not complete it:")
    for r in false_pass[:3]:
        print(f"         {r['task']}: {r['note']}")
    print("\n  Grade the outcome, not the route. And re-check the environment: a benchmark built on")
    print("  last year's website measures last year's website.")


def main() -> None:
    contamination()
    agents()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
