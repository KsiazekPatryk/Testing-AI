"""
quality_is_relative.py: quality is relative. Benchmarking is a lens, not an answer.

Run:  python quality_is_relative.py
      python quality_is_relative.py --no-method     # what happens when nobody wrote the method down

When absolute truth is hard to measure, comparing with similar systems says a lot. A 4.2 s login
sounds "good enough" until the competitors load in under 1.5 s. Benchmarking is especially valuable
when evidence is scarce: if twenty comparable products have clear error messages and a visible
support contact and yours does not, that absence becomes evidence. But competitors are not the
truth: a market can converge on bad patterns.

  1. the method, written down first: peer group, tasks, measurement, what is not controlled
  2. numbers that sound fine on their own, and where they sit in the group
  3. absence as evidence
  4. the chart that changes the mood in the team
  5. competitors are not the truth: "they do it" vs "users need it" vs "the law requires it"
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import median

from metrickit import load_json, percentile_rank

HERE = Path(__file__).parent
REQUIRED_METHOD = ("peer_group", "tasks", "measurement", "not_controlled")


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def main() -> None:
    d = load_json(HERE / "data" / "peer_group.json")
    if "--no-method" in sys.argv:
        d["method"] = {}

    header("1. THE METHOD, WRITTEN DOWN FIRST")
    missing = [k for k in REQUIRED_METHOD if not d["method"].get(k)]
    if missing:
        print(f"  Missing from the method: {', '.join(missing)}.")
        print("  Not comparing. Without a defined group, tasks and measurement, a comparison is an")
        print("  anecdote with a chart attached.")
        return
    m = d["method"]
    print(f"  peer group:   {m['peer_group']}")
    print(f"  tasks:        {'; '.join(m['tasks'])}")
    print(f"  measurement:  {m['measurement']}")
    print("  not controlled (say so in the report, do not pretend this is a lab experiment):")
    for x in m["not_controlled"]:
        print(f"    - {x}")

    header("2. NUMBERS THAT SOUND FINE ON THEIR OWN")
    for key, x in d["numeric"].items():
        lower = x["lower_is_better"]
        rank = percentile_rank(x["us"], x["peers"], lower_is_better=lower)
        best = min(x["peers"]) if lower else max(x["peers"])
        worst = max(x["peers"]) if lower else min(x["peers"])
        print(f"  {x['label']}: {x['us']} {x['unit']}   (on its own it sounds like: \"{x['sounds_like']}\")")
        print(f"    peers (n={len(x['peers'])}): median {median(x['peers'])} {x['unit']}, best {best}, worst {worst}")
        print(f"    we beat {rank:.0%} of the group" + (f"   ({x['peer_note']})" if x.get("peer_note") else ""))
    print("  None of these numbers is bad in a vacuum. Next to the group, every one of them is last.")

    header("3. ABSENCE AS EVIDENCE")
    n_peers = len(d["numeric"]["login_s"]["peers"])
    for key, f in d["features"].items():
        us = "yes" if f["us"] else "NO"
        note = ""
        if not f["us"] and f["peers_with"] == n_peers:
            note = "  <- every comparable product has it: its absence is a finding"
        print(f"  {f['label']:44} us: {us:3}  peers: {f['peers_with']:2}/{n_peers}{note}")
    print("  With little evidence about what users need, 'all twenty peers do it and we do not' is")
    print("  a strong lead. It is still a lead: section 5 is how you check it.")

    header("4. THE CHART THAT CHANGES THE MOOD")
    dic = d["dictionary_app"]
    print(f"  {dic['metric']}")
    top = max(dic["apps"].values())
    for name, v in sorted(dic["apps"].items(), key=lambda kv: kv[1]):
        print(f"  {name:15} {v:4.1f} s  {'#' * int(round(v / top * 50))}")
    print(f"  Why: {dic['cause']}.")
    print("  'Your app is slow' goes into the backlog. This chart goes into the planning meeting.")

    header("5. COMPETITORS ARE NOT THE TRUTH")
    for key, r in d["requirements"].items():
        if key.startswith("_"):
            continue
        print(f"  {key}")
        print(f"    competitors do it: {r['competitors']}")
        print(f"    users need it:     {r['users']}")
        print(f"    the law:           {r['law'] or '-'}")
    print("\n  pre_ticked_marketing_consent: 17 of 20 competitors do it, and it is not valid consent.")
    print("  The market converged on a bad pattern; copying it would be a defect, not a benchmark win.")
    print("  Keep the three columns apart. Benchmarking is a lens, not an answer: evidence, not authority.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
