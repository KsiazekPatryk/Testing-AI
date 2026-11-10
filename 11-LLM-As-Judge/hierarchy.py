"""
hierarchy.py: use the cheapest check that can do the job, and the judge only where it adds value.

Run:  python hierarchy.py

The evaluation hierarchy from the post, applied to 200 assistant outputs:
  1. deterministic checks, where the rule can be written down exactly
     (valid schema, banned phrases, a missing citation): no judge needed
  2. one calibrated LLM judge for semantic evaluation at moderate risk
  3. human review for serious failures, ambiguous cases, policy boundaries, calibration samples
  4. several judges or arbitration, only where the risk justifies the cost and the complexity
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict

from metrics import load_jsonl

HERE = Path(__file__).parent
COST = {"deterministic": 0.0, "judge": 0.002, "human": 1.50, "multi_judge": 0.006}   # USD per output
HIGH_RISK = {"medical"}
CALIBRATION_SAMPLE = 0.05


def route(o: Dict, i: int) -> str:
    if not o["valid_json"] or o["banned_phrase"] or not o["cites_source"]:
        return "1 deterministic: failed, no judge needed"
    if o["segment"] in HIGH_RISK:
        return "4 two judges + human arbitration (high risk)"
    if o["ambiguous"]:
        return "3 human: ambiguous case"
    if i % int(1 / CALIBRATION_SAMPLE) == 0:
        return "3 human: calibration sample"
    return "2 one calibrated judge"


def cost(layer: str) -> float:
    if layer.startswith("1"):
        return COST["deterministic"]
    if layer.startswith("2"):
        return COST["deterministic"] + COST["judge"]
    if layer.startswith("3"):
        return COST["deterministic"] + COST["judge"] + COST["human"]
    return COST["deterministic"] + COST["multi_judge"] + COST["human"]


def main() -> None:
    outputs = load_jsonl(HERE / "data" / "outputs.jsonl")
    print("=" * 78 + f"\nTHE EVALUATION HIERARCHY ON {len(outputs)} OUTPUTS\n" + "=" * 78)
    layers = Counter(route(o, i) for i, o in enumerate(outputs))
    for layer in sorted(layers):
        n = layers[layer]
        print(f"  {layer:46} {n:>4}  {'#' * (n // 2)}")
    fails = Counter()
    for o in outputs:
        if not o["valid_json"]:
            fails["invalid JSON schema"] += 1
        elif o["banned_phrase"]:
            fails["banned phrase"] += 1
        elif not o["cites_source"]:
            fails["missing citation"] += 1
    print("\n  Caught by plain code: " + ", ".join(f"{k} {v}" for k, v in fails.items()))
    print("  Asking an LLM whether a JSON object is valid is slower, costlier and less reliable than parsing it.")

    total = sum(cost(route(o, i)) for i, o in enumerate(outputs))
    all_human = len(outputs) * COST["human"]
    all_multi = len(outputs) * (COST["multi_judge"] + COST["human"])
    print("\n" + "=" * 78 + "\nCOST OF ONE EVALUATION RUN\n" + "=" * 78)
    print(f"  hierarchy:                        ${total:7.2f}")
    print(f"  every output to a human:          ${all_human:7.2f}")
    print(f"  every output to judges + human:   ${all_multi:7.2f}")
    print("  The judge does the bulk of semantic review cheaply. Humans see what the judge cannot be")
    print("  trusted with, plus a calibration sample that keeps the judge honest.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
