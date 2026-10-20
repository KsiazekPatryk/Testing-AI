"""
check_my_gate.py: the exercise from the post.

"Take one change you plan to ship and write a release gate for it in plain language.
 Answer five questions:
   1. What is the sample, and where does it come from (golden set, live traffic, both)?
   2. Which slices are risky and get their own thresholds?
   3. Which failures are a hard blocker, regardless of the average?
   4. What happens after release: canary, monitoring, rollback conditions?
   5. What single signal would change your decision from 'ship' to 'hold'?"

Run:  python exercise/check_my_gate.py
      python exercise/check_my_gate.py path/to/your_gate.json

The script checks that every question has a real answer, writes the gate as a short
plain-language document (output/my_release_gate.md), and, if you point it to evidence,
runs the release gate and adds the decision.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from release_gate import evaluate  # noqa: E402
from stats import load  # noqa: E402

DEFAULT_FILE = HERE / "my_release_gate.json"
QUESTIONS = {
    "1_sample": "What is the sample, and where does it come from?",
    "2_risky_slices": "Which slices are risky and get their own thresholds?",
    "3_hard_blockers": "Which failures are a hard blocker, regardless of the average?",
    "4_after_release": "What happens after release: canary, monitoring, rollback?",
    "5_signal_to_hold": "What single signal would change the decision from ship to hold?",
}
PLACEHOLDERS = ("todo", "tbd", "...", "fill in", "?")


def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return not value or all(is_empty(v) for v in value.values())
    if isinstance(value, list):
        return not value or all(is_empty(v) for v in value)
    text = str(value).strip().lower()
    return not text or text in PLACEHOLDERS


def review(answers: Dict) -> List[str]:
    """Problems that would make the gate an empty promise."""
    problems = []
    for key, question in QUESTIONS.items():
        if is_empty(answers.get(key)):
            problems.append(f"{key}: no answer to '{question}'")
    sample = str(answers.get("1_sample", "")).lower()
    if sample and not any(w in sample for w in ("golden", "live", "production", "traffic")):
        problems.append("1_sample: say where the sample comes from (golden set, live traffic or both)")
    if sample and not any(ch.isdigit() for ch in sample):
        problems.append("1_sample: say how many cases")
    slices = answers.get("2_risky_slices")
    if isinstance(slices, dict):
        for name, rule in slices.items():
            if not any(ch.isdigit() for ch in str(rule)):
                problems.append(f"2_risky_slices: '{name}' needs a number, not just a name")
    after = answers.get("4_after_release")
    if isinstance(after, dict):
        for part in ("canary", "monitoring", "rollback"):
            if is_empty(after.get(part)):
                problems.append(f"4_after_release: missing '{part}'")
    signal = answers.get("5_signal_to_hold")
    if isinstance(signal, list) and len(signal) > 1:
        problems.append("5_signal_to_hold: pick one signal, not a list")
    return problems


def as_markdown(spec: Dict, decision: str, reasons: List[str]) -> str:
    a = spec["answers"]
    lines = [f"# Release gate: {spec['change']}", ""]
    lines += ["## 1. Sample", "", str(a["1_sample"]), ""]
    lines += ["## 2. Risky slices with their own thresholds", ""]
    lines += [f"- **{k}**: {v}" for k, v in a["2_risky_slices"].items()] + [""]
    lines += ["## 3. Hard blockers (regardless of the average)", ""]
    lines += [f"- {b}" for b in a["3_hard_blockers"]] + [""]
    lines += ["## 4. After release", ""]
    lines += [f"- **{k}**: {v}" for k, v in a["4_after_release"].items()] + [""]
    lines += ["## 5. The one signal that changes ship to hold", "", str(a["5_signal_to_hold"]), ""]
    if decision:
        lines += ["## Decision on the current evidence", "", f"**{decision}**", ""]
        lines += [f"- {r}" for r in reasons] + [""]
    lines += ["We stopped asking whether the test passed. We ask whether the evidence is enough.", ""]
    return "\n".join(lines)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"Change: {spec['change']}\n")

    problems = review(spec.get("answers", {}))
    for key, question in QUESTIONS.items():
        ok = not any(p.startswith(key) for p in problems)
        print(f"  [{'OK  ' if ok else 'MISS'}] {question}")
    if problems:
        print("\nBefore this gate means anything:")
        for p in problems:
            print(f"  - {p}")
        return

    decision, reasons = "", []
    ev = spec.get("evidence") or {}
    if ev.get("gate") and ev.get("results"):
        gate_path = (path.parent / ev["gate"]).resolve()
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        rows = load((path.parent / ev["results"]).resolve())
        baseline = load(gate_path.parent / gate["baseline"]) if gate.get("baseline") else None
        with contextlib.redirect_stdout(io.StringIO()):
            decision, reasons = evaluate(gate, rows, baseline)
        print(f"\nDecision on the evidence ({Path(ev['results']).name}): {decision}")
        for r in reasons:
            print(f"  - {r}")

    out = ROOT / "output" / "my_release_gate.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(as_markdown(spec, decision, reasons), encoding="utf-8")
    print(f"\nAll five questions answered. The gate in plain language: {out.relative_to(ROOT)}")
    print("If you can answer these, you stopped asking whether the test passed.")
    print("You started asking whether the evidence is enough.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
