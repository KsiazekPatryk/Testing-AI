"""
golden_vs_live.py: golden sets catch regressions, live samples catch drift.

Run:  python golden_vs_live.py
      python golden_vs_live.py --promote     # write the next version of the golden set

Golden set (golden_set.json):
  Question: did we regress on known, important cases?   Weakness: it ages.
Live samples (live_samples/*.jsonl, one file per week, labeled by reviewers):
  Question: how do we handle today's reality?            Weakness: no memory of the past.

The loop: an important new failure found in live samples goes into the golden set.
--promote writes output/golden_set_next.json with those failures (and any broken
metamorphic relations from metamorphic.py) added, so you can review and replace
golden_set.json with it.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from assistant import answer, extract_facts

HERE = Path(__file__).parent
OUTPUT = HERE / "output"


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% confidence interval for a pass rate (Wilson method)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def check(case: Dict, seed: int) -> Tuple[bool, str, List[str]]:
    """Run one case. Returns (passed, answer text, list of problems)."""
    text = answer(case["question"], seed=seed).text
    facts = extract_facts(text)
    problems = []
    for key, expected in case.get("expect", {}).items():
        if facts.get(key) != expected:
            problems.append(f"{key}: expected {expected}, got {facts.get(key)}")
    for pattern in case.get("must_include", []):
        if not re.search(pattern, text):
            problems.append(f"missing: /{pattern}/")
    for pattern in case.get("must_not_include", []):
        if re.search(pattern, text):
            problems.append(f"forbidden: /{pattern}/")
    return not problems, text, problems


def run(cases: List[Dict], title: str, seed: int) -> List[Dict]:
    failures = []
    for i, case in enumerate(cases):
        ok, text, problems = check(case, seed + i)
        if not ok:
            failures.append({**case, "answer": text, "problems": problems})
    passed = len(cases) - len(failures)
    lo, hi = wilson(passed, len(cases))
    print(f"\n{title}")
    print(f"  passed {passed}/{len(cases)} ({passed / len(cases):.0%}), "
          f"95% CI {lo:.0%}–{hi:.0%}")
    for f in failures:
        print(f"  [FAIL] {f['id']}: {f['question']}")
        print(f"         answer:   {f['answer']}")
        print(f"         problems: {'; '.join(f['problems'])}")
        if f.get("note"):
            print(f"         note:     {f['note']}")
    return failures


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Golden set vs live samples.")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--promote", action="store_true", help="write output/golden_set_next.json")
    a = ap.parse_args()

    golden = json.loads((HERE / "golden_set.json").read_text(encoding="utf-8"))
    print("=" * 78)
    print("GOLDEN SET: did we regress on known, important cases?")
    golden_failures = run(golden["cases"], f"golden_set.json ({len(golden['cases'])} cases)", a.seed)
    if not golden_failures:
        print("  No regressions. But the golden set only knows the past.")

    print("\n" + "=" * 78)
    print("LIVE SAMPLES: how do we handle today's reality?")
    live_failures: List[Dict] = []
    for path in sorted((HERE / "live_samples").glob("*.jsonl")):
        week = path.stem
        fails = run(load_jsonl(path), f"live sample {week}", a.seed)
        for f in fails:
            f["source"] = f"live sample {week}"
        live_failures += fails

    print("\n" + "=" * 78)
    print("WHAT THIS MEANS")
    if golden_failures:
        print("  The golden set is red: something we already knew about broke. That is a regression.")
    else:
        print("  The golden set is green, so nothing we already knew about broke.")
    if live_failures:
        print("  The live samples are not: new wording, a new policy and growing Spanish traffic")
        print("  are things the golden set has never seen. That is drift, and only live")
        print("  sampling catches it.")
    else:
        print("  The live samples are green too. Keep sampling: drift rarely announces itself.")

    candidates = [
        {"id": f["id"], "question": f["question"], "expect": f.get("expect", {}),
         "why": f"Found in {f['source']}: {'; '.join(f['problems'])}" + (f" ({f['note']})" if f.get("note") else "")}
        for f in live_failures
    ]
    meta_path = OUTPUT / "golden_set_candidates.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))["candidates"]
        candidates += meta
        print(f"\n  Also found {len(meta)} candidates from metamorphic.py ({meta_path.relative_to(HERE)}).")

    if not a.promote:
        print(f"\n  {len(candidates)} candidates for the golden set. Run with --promote to write the next version.")
        return

    known = {c["question"] for c in golden["cases"]}
    new = [c for c in candidates if c["question"] not in known]
    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / "golden_set_next.json"
    out.write_text(json.dumps({**golden, "cases": golden["cases"] + new}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n  Wrote {out.relative_to(HERE)}: {len(golden['cases'])} known cases + {len(new)} new ones.")
    print("  Review it, fix the 'expect' fields where the new policy applies, then replace golden_set.json.")
    print("  From then on, these failures can never quietly come back.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
