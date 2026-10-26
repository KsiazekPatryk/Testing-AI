"""
generate_data.py: builds the sample data in data/ (already committed).

Run:  python generate_data.py      # rewrites data/*, always with the same content

  scores.jsonl            100 scored answers of a support assistant (0-10), with slices
  delivery_delays.jsonl   400 grocery deliveries: how many minutes late, by neighborhood
  version_pairs.jsonl     600 test cases run through version A and two candidate versions B
  judge_confidence.jsonl  verdicts of two LLM judges with the confidence each one reported
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).parent
DATA = HERE / "data"

# score -> number of answers, per slice. A score below 5 counts as a failure.
SCORES: Dict[str, Dict[int, int]] = {
    "english_support": {10: 10, 9: 20, 8: 15, 7: 5},
    "billing": {10: 5, 9: 10, 8: 8, 7: 2},
    "spanish_support": {9: 4, 8: 6, 7: 3, 6: 1, 4: 1},
    "policy_edge_cases": {9: 2, 8: 3, 7: 1, 6: 1, 4: 2, 3: 1},
}
NEIGHBORHOODS = {"Centre": 100, "North": 100, "Riverside": 100, "Old Town": 60, "Airport District": 40}


def scores() -> List[Dict]:
    rng = random.Random("scores")
    rows = [{"slice": s, "score": v, "failed": v < 5}
            for s, hist in SCORES.items() for v, n in hist.items() for _ in range(n)]
    rng.shuffle(rows)
    return [{"id": f"case-{i:03d}", **r} for i, r in enumerate(rows, 1)]


def delivery_delays() -> List[Dict]:
    rng = random.Random("delays")
    rows = []
    for hood, n in NEIGHBORHOODS.items():
        for _ in range(n):
            if hood == "Airport District":
                delay = rng.randint(24, 68)          # one neighborhood carries most of the pain
            else:
                delay = rng.choices(range(0, 9), weights=[20, 22, 22, 14, 9, 6, 4, 2, 1])[0]
            rows.append({"neighborhood": hood, "delay_min": delay})
    rng.shuffle(rows)
    return [{"id": f"order-{i:03d}", **r} for i, r in enumerate(rows, 1)]


def version_pairs() -> List[Dict]:
    """Same 600 cases for every version, so versions can be compared case by case.
    A passes 492 (82%). The prompt tweak flips 30 passes to fails and 42 fails to passes
    (504, 84%). The retrieval fix flips 12 and 60 (540, 90%)."""
    rng = random.Random("pairs")
    a = [1] * 492 + [0] * 108
    passes = [i for i, x in enumerate(a) if x]
    fails = [i for i, x in enumerate(a) if not x]
    rows = []
    for name, down, up in (("b_prompt_tweak", 30, 42), ("b_retrieval_fix", 12, 60)):
        b = list(a)
        for i in rng.sample(passes, down):
            b[i] = 0
        for i in rng.sample(fails, up):
            b[i] = 1
        rows.append((name, b))
    return [{"id": f"case-{i:03d}", "a": a[i], **{name: b[i] for name, b in rows}} for i in range(600)]


def judge_confidence() -> List[Dict]:
    rng = random.Random("confidence")
    rows = []
    for _ in range(400):                          # always says 0.95, right 80% of the time
        rows.append({"judge": "always_sure", "language": "en", "confidence": 0.95,
                     "correct": rng.random() < 0.80})
    for language, n, offset in (("en", 400, 0.0), ("pl", 200, 0.15)):
        # Spreads its confidence. Within each 0.1 bucket, the share of correct verdicts matches
        # the stated confidence in English, and is 15 points lower in Polish.
        confs = sorted(round(rng.uniform(0.5, 0.99), 2) for _ in range(n))
        for lo in (0.5, 0.6, 0.7, 0.8, 0.9):
            bucket = [c for c in confs if lo <= c < lo + 0.1]
            k = round(len(bucket) * (sum(bucket) / len(bucket) - offset)) if bucket else 0
            hits = set(rng.sample(range(len(bucket)), k))
            for i, c in enumerate(bucket):
                rows.append({"judge": "calibrated", "language": language, "confidence": c,
                             "correct": i in hits})
    rng.shuffle(rows)
    return [{"id": f"verdict-{i:03d}", **r} for i, r in enumerate(rows, 1)]


def write(name: str, rows: List[Dict]) -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"data/{name}  ({len(rows)} rows)")


def main() -> None:
    write("scores.jsonl", scores())
    write("delivery_delays.jsonl", delivery_delays())
    write("version_pairs.jsonl", version_pairs())
    write("judge_confidence.jsonl", judge_confidence())


if __name__ == "__main__":
    main()
