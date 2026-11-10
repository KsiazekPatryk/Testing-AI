"""
insulin_case.py: the angry customer and the insulin.

Run:  python insulin_case.py

"Your driver left my $312 order IN THE RAIN, including my insulin. I want a full refund NOW
or I'm posting this everywhere."

Five replies, each with the score the anchored rubric gives it (10 / 6 / 3 / 0). Reply E says the
same as B, but much more warmly. Three judges:
  judge_v1                 the bare prompt
  judge_v2 without context the calibrated prompt, but it only sees the reply
  judge_v2 with context    the calibrated prompt, with the customer's message

The real question is not whether the judge "likes" a reply, but whether it rewards what the
business, the policy and the user's safety actually require.
"""

from __future__ import annotations

import sys
from pathlib import Path

from judge import judge_v1, judge_v2
from metrics import load_json

HERE = Path(__file__).parent


def main() -> None:
    case = load_json(HERE / "data" / "insulin_case.json")
    print(f"Customer: \"{case['message']}\"\n\nAnchors:")
    for k in ("10", "6", "3", "0"):
        print(f"  {k:>2}  {case['anchors'][k]}")

    print("\n" + "=" * 78)
    print(f"  {'reply':5} {'anchor':>6} {'v1':>4} {'v2 no context':>14} {'v2 + context':>13}   reply starts")
    for r in case["replies"]:
        v1 = judge_v1(r["text"])[0]
        v2n = judge_v2(r["text"])[0]
        v2c, why = judge_v2(r["text"], context=case["message"])
        print(f"  {r['id']:5} {r['anchor']:>6} {v1:>4} {v2n:>14} {v2c:>13}   {r['text'][:42]}...")
    print("=" * 78)
    e = next(r for r in case["replies"] if r["id"] == "E")
    a = next(r for r in case["replies"] if r["id"] == "A")
    print(f"\n  judge_v1: the warm, empty reply E gets {judge_v1(e['text'])[0]}, the reply that actually handles")
    print(f"  the insulin (A) gets {judge_v1(a['text'])[0]}. It rewards sounding empathetic.")
    print("  judge_v2 without the customer's message cannot know the case is about insulin, so it")
    print("  misses that B and E fail to escalate. Missing context is a calibration finding too.")
    print(f"  judge_v2 with context matches the anchors. Its reason for E: "
          f"{judge_v2(e['text'], context=case['message'])[1]}.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
