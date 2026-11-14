"""
check_my_benchmark.py: the exercise from the post.

"Take one public result that recently came up when your team discussed choosing a model,
 and answer the six questions from this post. Then write in one sentence which case from
 your product should replace this benchmark in your evaluation."

Run:  python exercise/check_my_benchmark.py
      python exercise/check_my_benchmark.py path/to/your_result.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Tuple

HERE = Path(__file__).parent
DEFAULT_FILE = HERE / "my_benchmark_result.json"
QUESTIONS = {
    "1_unit_of_work": "What is the unit of work?",
    "2_population": "What is the population of cases? Does it resemble your traffic?",
    "3_oracle": "What is the oracle?",
    "4_aggregation": "What is aggregated?",
    "5_contamination": "How likely is contamination?",
    "6_changes_the_decision": "Would it change the release decision?",
}


def verdict(key: str, entry: Dict) -> Tuple[str, str]:
    ans = (entry or {}).get("answer")
    if not ans:
        if key == "5_contamination":
            return "UNKNOWN", "nobody checked: assume the model may have seen the questions"
        if key == "6_changes_the_decision":
            return "UNKNOWN", "if you cannot say how, the result is decoration, not evidence"
        return "UNKNOWN", "find out before the result goes on a slide"
    if entry.get("matches_product") is False:
        return "GAP", ans
    return "OK", ans


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"Result:   {spec.get('result')}\nProduct:  {spec.get('our_product')}\nDecision: {spec.get('our_decision')}\n")
    qs = spec.get("six_questions", {})
    tally = {}
    for key, q in QUESTIONS.items():
        v, why = verdict(key, qs.get(key))
        tally[v] = tally.get(v, 0) + 1
        print(f"  [{v:7}] {q}\n            {why}")

    rep = (spec.get("replacement_case") or "").strip()
    print("\n  Replacement case from your product:")
    if len(rep.split()) < 8:
        print("    missing or too vague. Write one concrete case: the task, the environment, and how it is graded.")
    else:
        print(f"    \"{rep}\"")

    print()
    decision = verdict("6_changes_the_decision", qs.get("6_changes_the_decision"))[0]
    if decision != "OK" or tally.get("GAP", 0) >= 2:
        print(f"  {tally.get('GAP', 0)} gaps, {tally.get('UNKNOWN', 0)} unknowns. For this decision the public result")
        print("  is a reference point, not evidence. Put the replacement case into your evaluation instead.")
    else:
        print("  The result speaks to your decision. Still: re-run it on your own cases before you ship.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
