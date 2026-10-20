"""
generate_data.py: builds the evaluation results in data/ (already committed).

Run:  python generate_data.py      # rewrites data/*.jsonl, always with the same content

The data describes a support assistant scored 0-10 on a rubric, case by case.
Score distributions are written out as explicit histograms, so every number in
the README can be traced back to this file:

  baseline_v1          the version in production today
  candidate_v2         new prompt + retrieval: better average, but weak slices and one privacy leak
  candidate_v3         v2 after fixes: passes the release gate
  candidate_v3_quick   only the first 30 cases of v3: too little evidence to decide
  canary_v3            production sample from the canary: Spanish support drops after release
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).parent
DATA = HERE / "data"
SLICE_SIZES = {"english_support": 180, "billing": 80, "spanish_support": 20, "policy_edge_cases": 20}

# score -> how many cases got it, per slice
HISTOGRAMS: Dict[str, Dict[str, Dict[int, int]]] = {
    "baseline_v1": {
        "english_support": {10: 10, 9: 40, 8: 80, 7: 40, 6: 10},
        "billing": {10: 6, 9: 20, 8: 32, 7: 20, 6: 2},
        "spanish_support": {9: 2, 8: 6, 7: 7, 6: 4, 5: 1},
        "policy_edge_cases": {9: 1, 8: 4, 7: 5, 6: 5, 5: 2, 4: 3},
    },
    "candidate_v2": {
        "english_support": {10: 46, 9: 74, 8: 45, 7: 14, 0: 1},
        "billing": {10: 17, 9: 22, 8: 33, 7: 8},
        "spanish_support": {9: 3, 8: 5, 7: 5, 6: 4, 5: 2, 2: 1},
        "policy_edge_cases": {9: 2, 8: 2, 7: 3, 6: 4, 5: 4, 4: 2, 3: 3},
    },
    "candidate_v3": {
        "english_support": {10: 46, 9: 75, 8: 45, 7: 14},
        "billing": {10: 17, 9: 22, 8: 33, 7: 8},
        "spanish_support": {10: 2, 9: 4, 8: 8, 7: 5, 6: 1},
        "policy_edge_cases": {9: 2, 8: 8, 7: 8, 6: 2},
    },
    "canary_v3": {
        "english_support": {10: 15, 9: 30, 8: 20, 7: 5},
        "billing": {10: 6, 9: 12, 8: 10, 7: 2},
        "spanish_support": {8: 3, 7: 5, 6: 7, 5: 4, 4: 1},
    },
}
LATENCY_FACTOR = {"baseline_v1": 1.00, "candidate_v2": 1.06, "candidate_v3": 1.04, "canary_v3": 1.05}
# Markers do not prove a failure. They say where to look.
MARKERS = ["low_confidence", "missing_citation", "judge_disagreement", "unusual_tool_call"]


def build(version: str) -> List[Dict]:
    rng = random.Random(f"evidence-{version}")
    rows: List[Dict] = []
    for slice_name, hist in HISTOGRAMS[version].items():
        scores = [s for s, count in hist.items() for _ in range(count)]
        rng.shuffle(scores)
        for score in scores:
            critical: Optional[str] = "privacy_leak" if score == 0 else None
            markers: List[str] = []
            if critical:
                markers = ["missing_citation", "judge_disagreement", "unusual_tool_call"]
            elif rng.random() < 0.025:
                markers = [rng.choice(MARKERS)]
            rows.append({
                "slice": slice_name,
                "score": score,
                "policy_failure": score <= 4,
                "critical": critical,
                "latency_ms": round(rng.gauss(1200, 150) * LATENCY_FACTOR[version]),
                "markers": markers,
            })
    rng.shuffle(rows)
    for i, row in enumerate(rows, 1):
        row["id"] = f"{version}-{i:04d}"
    return [{"id": r["id"], **{k: v for k, v in r.items() if k != "id"}} for r in rows]


def write(name: str, rows: List[Dict]) -> None:
    DATA.mkdir(exist_ok=True)
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    (DATA / f"{name}.jsonl").write_text(text, encoding="utf-8")
    print(f"data/{name}.jsonl  ({len(rows)} cases)")


def main() -> None:
    for version in HISTOGRAMS:
        rows = build(version)
        write(version, rows)
        if version == "candidate_v3":
            write("candidate_v3_quick", rows[:30])


if __name__ == "__main__":
    main()
