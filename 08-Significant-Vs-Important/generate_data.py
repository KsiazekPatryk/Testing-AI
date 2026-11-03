"""
generate_data.py: writes the example data in data/ (always the same content).

Run:  python generate_data.py

  refund_policy.jsonl   3,000 support conversations, old vs new returns-policy prompt
  agent_search.jsonl    200 configurations of a flaky-test-fixing agent, each run on 200 dev tasks
  agent_confirm.json    the winner and production, re-run on a fresh held-out set
  bug_findings.jsonl    100 suspicious places in code, a bug detector's score, and the truth
The summary numbers for the post's other examples are in data/significance_cases.json (hand-written).
"""

from __future__ import annotations

import json
import random
from itertools import product
from pathlib import Path

DATA = Path(__file__).parent / "data"
AGENT_SEED = 35          # chosen so that the search reproduces the post: production 84%, best 91%


def write_jsonl(name: str, rows) -> None:
    with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def flags(n: int, k: int, rng: random.Random):
    out = [True] * k + [False] * (n - k)
    rng.shuffle(out)
    return out


def refund_policy(rng: random.Random):
    # (slice, conversations per version, auto refunds old/new, escalations old/new, complaints old/new)
    slices = [
        ("low (< 500 PLN)", 900, (180, 162), (18, 19), (27, 27)),
        ("mid (500-3000 PLN)", 450, (72, 39), (13, 14), (14, 15)),
        ("high (> 3000 PLN)", 150, (18, 9), (14, 28), (5, 6)),
    ]
    rows, i = [], 0
    for version_idx, version in enumerate(("old", "new")):
        for name, n, refunds, escalations, complaints in slices:
            r = flags(n, refunds[version_idx], rng)
            e = flags(n, escalations[version_idx], rng)
            c = flags(n, complaints[version_idx], rng)
            angry = flags(n, n // 4, rng)
            for j in range(n):
                i += 1
                base = 9.0 if angry[j] else 6.0
                extra = 4.0 if (version == "new" and angry[j]) else 0.0
                defensive_rate = (0.15 if angry[j] else 0.06) if version == "new" else (0.04 if angry[j] else 0.03)
                rows.append({"id": f"conv-{i:05d}", "version": version, "order_value": name,
                             "customer_angry": angry[j], "auto_refund": r[j], "escalated": e[j],
                             "complaint": c[j], "handle_minutes": round(max(1.0, rng.gauss(base + extra, 1.5)), 1),
                             "tone_defensive": rng.random() < defensive_rate})
    return rows


def agent_search(rng: random.Random):
    prompts = [f"prompt-{c}" for c in "ABCDE"]
    models = ["model-1", "model-2", "model-3", "model-4"]
    tools = ["read_only", "run_tests", "edit_tests"]
    rubrics = ["judge-v1", "judge-v2", "judge-v3", "judge-v4"]
    combos = list(product(prompts, models, tools, rubrics))
    rng.shuffle(combos)
    combos = [("prompt-A", "model-1", "run_tests", "judge-v1")] + \
             [c for c in combos if c != ("prompt-A", "model-1", "run_tests", "judge-v1")][:200]
    rows = []
    for idx, (p, m, t, j) in enumerate(combos):
        honest = 0.84 if idx == 0 else min(0.9, max(0.78, rng.gauss(0.84, 0.005)))
        easy = sum(rng.random() < honest + 0.08 for _ in range(120))
        hard = sum(rng.random() < honest - 0.12 for _ in range(80))
        # With write access to test files, some "fixes" weaken or delete the flaky test.
        weakened = sum(rng.random() < 0.1 for _ in range(200 - easy - hard)) if t == "edit_tests" else 0
        weak_easy = min(weakened, 120 - easy)
        rows.append({"config": f"cfg-{idx:03d}", "prompt": p, "model": m, "tools": t, "judge_rubric": j,
                     "production": idx == 0, "honest_rate": round(honest, 4),
                     "tasks": 200, "passed": easy + hard + weakened,
                     "easy_passed": easy + weak_easy, "easy_tasks": 120,
                     "hard_passed": hard + weakened - weak_easy, "hard_tasks": 80,
                     "passes_that_weakened_a_test": weakened})
    return rows


def agent_confirm(rows, rng: random.Random):
    prod = next(r for r in rows if r["production"])
    best = max((r for r in rows if not r["production"]), key=lambda r: r["passed"])
    out = {"fresh_tasks": 200, "note": "fresh held-out set; test files are read-only for every configuration"}
    for name, r in (("production", prod), ("winner", best)):
        runs = [sum(rng.random() < r["honest_rate"] for _ in range(200)) for _ in range(5)]
        out[name] = {"config": r["config"], "fresh_runs_passed": runs}
    return out


def bug_findings(rng: random.Random):
    # 60 real bugs and 40 clean places. At threshold 0.5: 40 TP, 10 FP, 20 FN, 30 TN (the post's numbers).
    rows = []
    groups = [(True, 40, 0.5, 0.98), (True, 20, 0.25, 0.49), (False, 10, 0.5, 0.66),
              (False, 20, 0.02, 0.3), (False, 10, 0.3, 0.49)]
    for is_bug, n, lo, hi in groups:
        for _ in range(n):
            rows.append({"is_bug": is_bug, "score": round(rng.uniform(lo, hi), 3)})
    rng.shuffle(rows)
    return [{"place": f"spot-{i + 1:03d}", **r} for i, r in enumerate(rows)]


def main() -> None:
    DATA.mkdir(exist_ok=True)
    write_jsonl("refund_policy.jsonl", refund_policy(random.Random(8)))
    agents = agent_search(random.Random(AGENT_SEED))
    write_jsonl("agent_search.jsonl", agents)
    (DATA / "agent_confirm.json").write_text(json.dumps(agent_confirm(agents, random.Random(AGENT_SEED + 1)),
                                                        indent=2) + "\n", encoding="utf-8")
    write_jsonl("bug_findings.jsonl", bug_findings(random.Random(8)))
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
