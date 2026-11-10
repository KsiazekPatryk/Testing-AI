"""
routing.py: apply the routing rules that calibration produced to a new batch.

Run:  python calibration.py    (writes output/routing_rules.json)
      python routing.py

120 new replies, no human scores yet. For each one:
  - a blocker found         -> the release is blocked until it is fixed
  - segment routed to human -> human review queue (the judge's score is a pre-sort)
  - automatic               -> the judge's score counts (corrected where calibration said so),
                               and a random share goes to a human audit
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from judge import blockers_v2, judge_v2
from metrics import load_jsonl, mean

HERE = Path(__file__).parent
RULES = HERE / "output" / "routing_rules.json"


def audited(item_id: str, rate: float) -> bool:
    h = int(hashlib.sha256(item_id.encode()).hexdigest(), 16) % 1000
    return h < rate * 1000


def main() -> None:
    if not RULES.exists():
        print("No routing rules yet: running calibration.py first.\n")
        import calibration
        calibration.main()
        print()
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    batch = load_jsonl(HERE / "data" / "new_batch.jsonl")

    routes, blocked, scores = Counter(), [], []
    for r in batch:
        found = blockers_v2(r["reply"], r["question"])
        rule = rules[r["segment"]]
        if found:
            routes["release blocked (blocker)"] += 1
            blocked.append((r, found[0][0]))
            continue
        score = judge_v2(r["reply"], context=r["question"])[0]
        score = max(0.0, min(10.0, score + rule["correction"].get(str(score), 0.0)))
        if rule["route"] == "human":
            routes["human review queue"] += 1
        elif audited(r["id"], rule["audit_rate"]):
            routes["automatic + human audit"] += 1
            scores.append(score)
        else:
            routes["automatic"] += 1
            scores.append(score)

    print("=" * 78 + f"\nNEW BATCH: {len(batch)} REPLIES\n" + "=" * 78)
    for k in ("automatic", "automatic + human audit", "human review queue", "release blocked (blocker)"):
        print(f"  {k:28} {routes[k]:>4}")
    print(f"\n  mean judge score of automatically scored replies (after correction): {mean(scores):.1f}")
    print("\n  The release is blocked by:")
    for (r, why), _ in zip(blocked, range(6)):
        print(f"    {r['id']} ({r['segment']}): {why}")
    if len(blocked) > 6:
        print(f"    ... and {len(blocked) - 6} more")
    print("\n  The judge scales the review. It does not own the quality definition or the release decision:")
    print("  the rules came from calibration against humans, and humans still see the risky segment,")
    print("  the audits and everything that blocks a release.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
