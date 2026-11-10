"""
copyright_year.py: even a simple task can fail.

Run:  python copyright_year.py

The judge checks whether the year in a site's copyright footer is current. Two problems:
  - the data is inconsistent: ©, (c), the word "copyright", a range like 2019-2026, no year at all
  - the model has its own sense of time: even with "The current year is 2026" in the prompt,
    it may call 2026 outdated (or 'in the future') and invent a confident reason

Changing the prompt, the model or the temperature may not fix it. A deterministic check might;
or the category should be switched off, because the measurement is worse than the problem.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Tuple

from judge import judge_copyright
from metrics import load_json

HERE = Path(__file__).parent


def deterministic(footer: str, current_year: int) -> Tuple[str, str]:
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", footer)]
    if not years:
        return "outdated", "no year in the footer"
    latest = max(years)
    return ("current", f"latest year {latest}") if latest == current_year else ("outdated", f"latest year {latest}")


def main() -> None:
    data = load_json(HERE / "data" / "footers.json")
    year = data["current_year"]
    print(f"Prompt: \"{data['prompt']}\"\n")
    print(f"  {'footer':42} {'truth':9} {'LLM judge':10} {'code':9}")
    j_ok = c_ok = 0
    wrong = []
    for f in data["footers"]:
        jv, jwhy = judge_copyright(f["footer"], year)
        cv, _ = deterministic(f["footer"], year)
        j_ok += jv == f["truth"]
        c_ok += cv == f["truth"]
        if jv != f["truth"]:
            wrong.append((f["footer"], jwhy))
        print(f"  {f['footer']:42} {f['truth']:9} {jv:10} {cv:9}")
    n = len(data["footers"])
    print(f"\n  LLM judge correct: {j_ok} / {n}   deterministic check correct: {c_ok} / {n}")
    print("\n  The judge's reasons for its mistakes (confident, and wrong):")
    for footer, why in wrong[:4]:
        print(f"    \"{footer}\": {why}")
    print("\n  The prompt told it the year. It still trusted its own sense of time.")
    print("  Here a ten-line rule beats the judge. When neither works, turn the category off:")
    print("  a measurement worse than the problem only produces noise and false alarms.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
