"""
label_provenance.py: treat labels as evidence with a chain of custody.

Run:  python label_provenance.py
      python label_provenance.py data/eval_labels.jsonl

Every important label should carry a record ("label card"):
  who created it, under which guideline, with what expertise, with what disagreement.

The script audits an evaluation set (one JSON label per line):
  1. how many labels have a complete card
  2. which labels are too weak for what they are used for (high risk, release gate)
  3. which guideline versions are mixed in one set
  4. what tier each risky label should have come from
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from agreement import load_jsonl

HERE = Path(__file__).parent
CARD_FIELDS = ("created_by", "rater_type", "expertise", "guideline_version")


def card_complete(r: Dict) -> bool:
    return all(r.get(k) for k in CARD_FIELDS)


def required_tier(r: Dict) -> str:
    if r.get("used_in_release_gate") or r.get("high_risk"):
        return "expert"
    if r.get("agreement") is not None and r["agreement"] < 1.0:
        return "overlap"
    return "generalist"


def problem(r: Dict) -> Optional[str]:
    """Why this label is not good enough for its use, or None."""
    if not card_complete(r):
        return "no provenance: nobody can say who made it or how"
    need = required_tier(r)
    if need == "expert" and r["rater_type"] in ("generalist", "llm"):
        return f"{'release gate' if r['used_in_release_gate'] else 'high risk'}, labeled by {r['rater_type']}"
    if r.get("used_in_release_gate") and r["n_raters"] == 1:
        return "release gate, a single rater, disagreement unknown"
    return None


def audit(rows: List[Dict]) -> None:
    n = len(rows)
    complete = sum(card_complete(r) for r in rows)
    print("=" * 78 + f"\nLABEL CARDS: {n} labels\n" + "=" * 78)
    print(f"  complete card (who, type, expertise, guideline): {complete} / {n} ({complete / n:.0%})")
    for k in CARD_FIELDS:
        missing = sum(not r.get(k) for r in rows)
        print(f"    missing {k:18} {missing}")
    kinds = Counter(r["rater_type"] or "unknown" for r in rows)
    print("  who made the labels: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()))

    versions = Counter(r["guideline_version"] or "unknown" for r in rows)
    print("\n  guideline versions in this one set: " + ", ".join(f"{k} {v}" for k, v in versions.most_common()))
    if len([v for v in versions if v != "unknown"]) > 1:
        print("  -> scores from different rubric versions are not comparable. Re-label, or report them separately.")

    gate = [r for r in rows if r["used_in_release_gate"]]
    weak = [(r, problem(r)) for r in rows]
    weak = [(r, p) for r, p in weak if p]
    weak_gate = [w for w in weak if w[0]["used_in_release_gate"]]
    print("\n" + "=" * 78 + "\nLABELS TOO WEAK FOR WHAT THEY ARE USED FOR\n" + "=" * 78)
    print(f"  {len(weak)} labels have a problem; {len(weak_gate)} of the {len(gate)} release-gate labels are among them.")
    reasons = Counter(p for _, p in weak)
    for reason, c in reasons.most_common():
        print(f"    {c:3}  {reason}")
    print("\n  First five release-gate labels to fix:")
    for r, p in weak_gate[:5]:
        print(f"    {r['label_id']} ({r['domain']}): {p} -> needs {required_tier(r)}")

    print("\n" + "=" * 78 + "\nA COMPLETE LABEL CARD LOOKS LIKE THIS\n" + "=" * 78)
    good = next(r for r in rows if card_complete(r) and r["rater_type"] == "expert" and r["n_raters"] > 1)
    for k in ("label_id", "label", "created_by", "rater_type", "expertise", "guideline_version", "n_raters", "agreement"):
        print(f"  {k:18} {good[k]}")
    print("\n  If a dataset cannot answer 'who made this label?', start there.")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "data" / "eval_labels.jsonl"
    audit(load_jsonl(path))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
