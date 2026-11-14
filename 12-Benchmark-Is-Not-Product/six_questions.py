"""
six_questions.py: six questions for every benchmark result.

Run:  python six_questions.py
      python six_questions.py --product coding_agent      (support_chatbot, search, coding_agent)

  1. What is the unit of work?        one answer, a conversation, a tool trajectory, a patch, a ranked list?
  2. What is the population of cases, and does it resemble real product traffic?
  3. What is the oracle?              exact answer, unit test, rubric, human vote, expert label?
  4. What is aggregated?              means, slices, rare failures, blockers, cost, latency?
  5. How likely is contamination?     could the model have seen the questions in training?
  6. Would this result change the release decision, or does it only look good on a slide?

The script asks them of all eight benchmarks, for one of your products (data/products.json).
"An evaluation that cannot change a decision is not evidence. It is decoration."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from evals import load_json

HERE = Path(__file__).parent


def ask(b: Dict, p: Dict) -> Tuple[List[Tuple[str, str, str]], str]:
    unit_ok = b["unit_of_work"] in p["comparable_units"]
    oracle_ok = any(k in b["oracle"].lower() for k in p["oracle_keywords"])
    agg_ok = any(m in b["aggregate"] for m in ("blocker", "slice", "trade-off"))
    clean = b["contamination_risk"] != "high"
    answers = [
        ("unit of work", "close" if unit_ok else "gap", f"{b['unit_of_work']} vs your {p['unit_of_work']}"),
        ("population", "gap", f"public tasks, not your traffic ({p['population']})"),
        ("oracle", "close" if oracle_ok else "gap", f"{b['oracle']}; you need {', '.join(p['oracle_needed'])}"),
        ("aggregation", "partial" if agg_ok else "gap", f"{b['aggregate']}; you need {', '.join(p['must_aggregate'])}"),
        ("contamination", "ok" if clean else "risk", f"{b['contamination_risk']} risk"),
    ]
    if unit_ok and oracle_ok and clean:
        decision = "weak signal: use it to shortlist models, not to ship"
    else:
        decision = "decoration: it cannot change the decision"
    return answers, decision


def main() -> None:
    products = load_json(HERE / "data" / "products.json")["products"]
    ap = argparse.ArgumentParser(description="Ask six questions of every benchmark result.")
    ap.add_argument("--product", choices=sorted(products), default="support_chatbot")
    a = ap.parse_args()
    p = products[a.product]
    print(f"Product: {p['description']}\nDecision: \"{p['decision']}\"")
    tally = {}
    for b in load_json(HERE / "data" / "benchmarks.json")["benchmarks"]:
        answers, decision = ask(b, p)
        print("\n" + "-" * 78 + f"\n  {b['name']}")
        for i, (q, ok, why) in enumerate(answers, 1):
            print(f"    {i}. {q:14} [{ok:7}] {why}")
        print(f"    6. {'decision':14} -> {decision}")
        tally[decision.split(':')[0]] = tally.get(decision.split(':')[0], 0) + 1
    print("\n" + "=" * 78)
    print("  " + ", ".join(f"{v} x {k}" for k, v in tally.items()))
    print("  No public benchmark matches your population or aggregates your blockers.")
    print("  The last question is the one teams skip most often: would it change the release decision?")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
