"""
ship_it_slow_down.py: "Ship it, the result is significant." Slow down.

Run:  python ship_it_slow_down.py

We changed the returns-policy prompt. Version B cut automatic refunds from 18% of conversations
to 14%, p = 0.003. The script reproduces that headline, then looks at the slices:
order value, escalations, complaints, angry customers, handling time and tone.

A p-value only says that something changed. Whether it changed for the better depends on
product values, risk tolerance and promises to customers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

from stats_tools import load_jsonl, p_str, pp, two_proportions

HERE = Path(__file__).parent
SLICES = ("low (< 500 PLN)", "mid (500-3000 PLN)", "high (> 3000 PLN)")


def rate(rows: List[Dict], field: str) -> str:
    k = sum(r[field] for r in rows)
    return f"{k:4} / {len(rows):<5} {k / len(rows):5.1%}"


def compare(old: List[Dict], new: List[Dict], field: str) -> Dict:
    return two_proportions(sum(r[field] for r in old), len(old), sum(r[field] for r in new), len(new))


def main() -> None:
    rows = load_jsonl(HERE / "data" / "refund_policy.jsonl")
    old = [r for r in rows if r["version"] == "old"]
    new = [r for r in rows if r["version"] == "new"]

    res = compare(old, new, "auto_refund")
    print("=" * 78 + "\nTHE HEADLINE\n" + "=" * 78)
    print(f"  automatic refunds: {res['p1']:.0%} -> {res['p2']:.0%} of conversations, {p_str(res['p'])}")
    print(f"  difference {pp(res['diff'])}, 95% CI {pp(res['ci_low'])} to {pp(res['ci_high'])}")
    print("  Tempting to announce a success. Look at the slices first.")

    print("\n" + "=" * 78 + "\nTHE SLICES\n" + "=" * 78)
    print(f"  {'order value':20} {'':10} {'auto refunds':>20} {'escalations':>20} {'complaints':>20}")
    for s in SLICES:
        for label, part in (("old", old), ("new", new)):
            sub = [r for r in part if r["order_value"] == s]
            print(f"  {s if label == 'old' else '':20} {label:10} {rate(sub, 'auto_refund'):>20} "
                  f"{rate(sub, 'escalated'):>20} {rate(sub, 'complaint'):>20}")
    hi_old = [r for r in old if r["order_value"] == SLICES[2]]
    hi_new = [r for r in new if r["order_value"] == SLICES[2]]
    esc = compare(hi_old, hi_new, "escalated")
    print(f"\n  Orders above 3000 PLN: escalations {esc['p1']:.1%} -> {esc['p2']:.1%} (doubled), {p_str(esc['p'])}.")
    print("  Fewer automatic refunds there, but every one of them became a person's job.")

    print("\n  Angry customers:")
    for label, part in (("old", old), ("new", new)):
        angry = [r for r in part if r["customer_angry"]]
        print(f"    {label}: {mean(r['handle_minutes'] for r in angry):4.1f} min per conversation, "
              f"defensive tone in {sum(r['tone_defensive'] for r in angry) / len(angry):.0%}")
    calm_new = [r for r in new if not r["customer_angry"]]
    print(f"    (calm customers, new version: {mean(r['handle_minutes'] for r in calm_new):.1f} min, "
          f"defensive tone in {sum(r['tone_defensive'] for r in calm_new) / len(calm_new):.0%})")

    print("\n" + "=" * 78 + "\nWHAT GOES IN THE REPORT\n" + "=" * 78)
    print("  The p-value never stands alone. Next to it:")
    print(f"    effect size and interval:  auto refunds {pp(res['diff'])} (95% CI {pp(res['ci_low'])} to {pp(res['ci_high'])})")
    print(f"    failure indicators:        complaints {rate(old, 'complaint').split()[-1]} -> {rate(new, 'complaint').split()[-1]}")
    print(f"    high-risk slices:          escalations above 3000 PLN {esc['p1']:.0%} -> {esc['p2']:.0%}")
    print("    cost:                      longer, more defensive conversations with angry customers")
    print("\n  Statistically: something changed. Whether it is better is a product decision, not a p-value.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
