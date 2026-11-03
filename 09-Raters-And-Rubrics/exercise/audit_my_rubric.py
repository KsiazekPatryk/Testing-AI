"""
audit_my_rubric.py: the exercise from the post.

"Take the rubric or instruction that someone uses to score your system's outputs, and check:
   1. Does every point on the scale have a described anchor, or just '1 = bad, 10 = good'?
   2. Are there blockers that override every score?
   3. Do you know who created the labels in your evaluation set, and with what expertise?
 If the answer to the third question is 'I don't know', that is where to start."

Run:  python exercise/audit_my_rubric.py
      python exercise/audit_my_rubric.py path/to/your_rubric.json
      python exercise/audit_my_rubric.py data/rubric_support.json   (the folder's own rubric)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from agreement import load_jsonl  # noqa: E402

DEFAULT_FILE = HERE / "my_rubric.json"
MAX_GAP = 4          # at most 3 undescribed points between two anchors (the post: 10, 7, 4, 0)
MIN_WORDS = 4        # "good" is a label, not a description
CARD_FIELDS = ("created_by", "rater_type", "expertise", "guideline_version")


def q1(spec: Dict) -> Tuple[str, str]:
    anchors = {int(k): v for k, v in (spec.get("anchors") or {}).items()}
    scale = spec.get("scale") or {"min": min(anchors, default=0), "max": max(anchors, default=10)}
    lo, hi = scale["min"], scale["max"]
    if not anchors:
        return "NO", f"Scale {lo}-{hi}, no anchors at all. Every reviewer invents their own."
    thin = [k for k, v in sorted(anchors.items()) if len(str(v).split()) < MIN_WORDS]
    points = sorted(set(anchors) | {lo, hi})
    gaps = [(a, b) for a, b in zip(points, points[1:]) if b - a > MAX_GAP]
    missing_ends = [p for p in (lo, hi) if p not in anchors]
    problems = []
    if thin:
        problems.append("anchors that only name a grade: " + ", ".join(f"{k} = '{anchors[k]}'" for k in thin))
    if gaps:
        problems.append("undescribed stretches: " + ", ".join(f"{a + 1}-{b - 1}" for a, b in gaps))
    if missing_ends:
        problems.append("ends of the scale without an anchor: " + ", ".join(map(str, missing_ends)))
    if problems:
        return "NO", "; ".join(problems) + ". Write what a typical answer at each level looks like."
    return "YES", f"{len(anchors)} described anchors on a {lo}-{hi} scale, at most {MAX_GAP - 1} undescribed points between them."


def q2(spec: Dict) -> Tuple[str, str]:
    blockers = spec.get("blockers") or []
    if isinstance(blockers, dict):
        blockers = list(blockers)
    if not blockers:
        return "NO", ("No blockers. An answer that leaks personal data or invents a policy can still "
                      "average its way to a pass.")
    return "YES", "Blockers that override the score: " + ", ".join(blockers) + "."


def dataset_cards(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    rows = load_jsonl(path)
    complete = sum(all(r.get(k) for k in CARD_FIELDS) for r in rows)
    gate = [r for r in rows if r.get("used_in_release_gate")]
    gate_complete = sum(all(r.get(k) for k in CARD_FIELDS) for r in gate)
    return {"n": len(rows), "complete": complete, "gate": len(gate), "gate_complete": gate_complete}


def q3(spec: Dict, base: Path) -> Tuple[str, str]:
    labels = spec.get("labels") or {}
    who, expertise = labels.get("created_by"), labels.get("expertise")
    cards = dataset_cards((base / labels["dataset"]).resolve()) if labels.get("dataset") else None
    if cards and cards["complete"] < cards["n"]:
        unknown = cards["n"] - cards["complete"]
        return "NO", (f"The dataset has {cards['n']} labels; {unknown} of them have no complete card "
                      f"(who, type, expertise, guideline), including {cards['gate'] - cards['gate_complete']} "
                      f"used in a release gate.")
    if cards:
        return "YES", f"All {cards['n']} labels say who made them, with what expertise and guideline."
    if not who or not expertise:
        return "UNKNOWN", "Nobody wrote down who created the labels or with what expertise."
    return "YES", f"Created by {who}, expertise: {expertise}."


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"The rubric: \"{spec.get('name', path.name)}\"\n")
    answers = [
        ("1. Every point on the scale has a described anchor?", q1(spec)),
        ("2. Blockers that override every score?", q2(spec)),
        ("3. Known who created the labels, with what expertise?", q3(spec, path.parent)),
    ]
    for question, (verdict, why) in answers:
        print(f"  [{verdict:7}] {question}\n            {why}")

    print()
    if answers[2][1][0] != "YES":
        print("Start with question 3: find out who made the labels and give each important one a card.")
        print("  Until then, every number computed on these labels is precise counting of an unknown thing.")
    weak = [q for q, (v, _) in answers[:2] if v != "YES"]
    if weak:
        print("Then fix the rubric: " + " and ".join(
            "anchors for every level" if q.startswith("1") else "blockers that override the score" for q in weak) + ".")
    if all(v == "YES" for _, (v, _) in answers):
        print("All three answered. Now check how well your raters agree (python rater_calibration.py).")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
