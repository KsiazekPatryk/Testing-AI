"""
generate_data.py: builds the sample data in data/ (already committed).

Run:  python generate_data.py      # rewrites data/*, always with the same content

  prompt_eval.jsonl         100 test cases, each scored 0-10 for the old and the new prompt
                            (paired: the same case went through both versions)
  ab_independent.jsonl      a different 80 cases for each version (not paired)
  repeated_runs.jsonl       100 prompts x 20 runs each, for old and new (2,000 rows per version)
  escalation_policy.json    outcomes of 100 conversations per returns policy (counts)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).parent
DATA = HERE / "data"


def clip(x: float) -> int:
    return max(0, min(10, round(x)))


def prompt_eval() -> List[Dict]:
    """Old mean 7.8, new mean 8.3 on the same 100 cases. Written as explicit histograms so every
    number in the README can be traced: old scores and per-case differences (new - old).
    One new answer is a policy failure the old one did not have: the mean is not the gate."""
    old_hist = {10: 13, 9: 20, 8: 30, 7: 19, 6: 10, 5: 5, 4: 3}
    diff_hist = {-3: 5, -2: 8, -1: 13, 0: 21, 1: 26, 2: 15, 3: 10, 4: 2}
    old = [s for s, n in old_hist.items() for _ in range(n)]
    diffs = [d for d, n in diff_hist.items() for _ in range(n)]
    rng = random.Random("prompt-eval")
    rng.shuffle(diffs)
    pairs = []
    for o in sorted(old, reverse=True):           # pair them so every new score stays in 0-10
        d = next(x for x in diffs if 0 <= o + x <= 10)
        diffs.remove(d)
        pairs.append((o, o + d))
    rng.shuffle(pairs)
    rows = []
    for i, (o, n) in enumerate(pairs, 1):
        rows.append({"id": f"case-{i:03d}", "old": o, "new": n, "old_pass": o >= 7, "new_pass": n >= 7,
                     "new_policy_failure": False})
    worst = min(rows, key=lambda r: (r["new"] - r["old"], r["new"]))
    worst["new_policy_failure"] = True
    return rows


def ab_independent() -> List[Dict]:
    rng = random.Random("ab")
    rows = [{"version": "old", "score": clip(rng.gauss(7.8, 1.6))} for _ in range(80)]
    rows += [{"version": "new", "score": clip(rng.gauss(8.3, 1.6))} for _ in range(80)]
    return [{"id": f"ab-{i:03d}", **r} for i, r in enumerate(rows, 1)]


def repeated_runs() -> List[Dict]:
    """Each prompt has its own 'personality': runs of the same prompt are correlated.
    The new prompt is no better on average at the prompt level."""
    rng = random.Random("runs")
    rows = []
    for p in range(1, 101):
        base = rng.gauss(7.8, 1.0)
        prompt_effect = rng.gauss(0.08, 0.6)    # how the new prompt does on this particular prompt
        for run in range(1, 21):
            noise = rng.gauss(0, 0.5)
            rows.append({"prompt": f"prompt-{p:03d}", "run": run, "version": "old",
                         "score": round(base + noise, 2)})
            rows.append({"prompt": f"prompt-{p:03d}", "run": run, "version": "new",
                         "score": round(base + prompt_effect + rng.gauss(0, 0.5), 2)})
    return rows


def write_jsonl(name: str, rows: List[Dict]) -> None:
    (DATA / name).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"data/{name}  ({len(rows)} rows)")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    write_jsonl("prompt_eval.jsonl", prompt_eval())
    write_jsonl("ab_independent.jsonl", ab_independent())
    write_jsonl("repeated_runs.jsonl", repeated_runs())
    policy = {
        "_note": "100 support conversations per returns policy, by outcome.",
        "categories": ["resolved automatically", "escalated to a human", "refused"],
        "old_policy": [70, 20, 10],
        "new_policy": [55, 35, 10],
    }
    (DATA / "escalation_policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    print("data/escalation_policy.json")


if __name__ == "__main__":
    main()
