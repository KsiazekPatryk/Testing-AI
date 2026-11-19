"""
red_team.py: random samples tell you about the average, attacks tell you about the edges.

Run:  python red_team.py
      python red_team.py --version v2 --runs 10
      python red_team.py --env production          (refused: not an approved environment)

A system that rarely fails on ordinary traffic but fails badly under deliberate pressure will be
missed by random sampling. Red-team cases aim at the boundaries: what it must refuse, what it must
never reveal, what needs confirmation, what happens when allowed and forbidden intent are mixed.

The script:
  1. checks that the run is authorized (approved environment, written rules, people who know)
  2. runs 500 ordinary conversations: the random-sample view
  3. runs every red-team case several times: family, severity, repeatability
  4. keeps the two results apart, and turns a serious bypass into a blocker
  5. re-runs the same attacks after the next change: does a fixed attack come back?
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from assistant import VERSIONS, attack_succeeds, ordinary_conversation_ok
from evalkit import load_json

HERE = Path(__file__).parent


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def authorized(env: str) -> bool:
    rules = load_json(HERE / "data" / "red_team_rules.json")
    header("1. IS THIS RUN AUTHORIZED?")
    if env not in rules["approved_environments"]:
        print(f"  Environment '{env}' is not approved ({', '.join(rules['approved_environments'])} is).")
        print("  Red-team traffic looks like an attack because it is one. On real accounts or without")
        print("  authorization it can get accounts blocked, or worse. Not running.")
        return False
    print(f"  environment: {env} (approved)    authorized by: {rules['authorized_by']}")
    print(f"  rules: {rules['written_rules']}")
    print(f"  people who know: {', '.join(rules['people_who_know'])}")
    return True


def bypasses(version: str, cases: List[Dict], runs: int) -> Dict[str, int]:
    return {c["id"]: sum(attack_succeeds(version, c, r) for r in range(runs)) for c in cases}


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the red-team suite against the offline assistant.")
    ap.add_argument("--version", choices=sorted(VERSIONS), default="v1")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--env", default="staging-redteam")
    a = ap.parse_args()
    if not authorized(a.env):
        return
    cases = load_json(HERE / "data" / "red_team_cases.json")["cases"]

    header(f"2. THE RANDOM-SAMPLE VIEW: 500 ORDINARY CONVERSATIONS ({a.version})")
    ok = sum(ordinary_conversation_ok(a.version, i) for i in range(500))
    print(f"  {ok} / 500 handled correctly ({ok / 500:.1%}). By this measure the system looks ready.")

    header(f"3. THE RED-TEAM VIEW: {len(cases)} ATTACKS x {a.runs} RUNS ({a.version})")
    res = bypasses(a.version, cases, a.runs)
    fam = defaultdict(lambda: [0, 0])
    for c in cases:
        fam[c["family"]][0] += res[c["id"]] > 0
        fam[c["family"]][1] += 1
    print(f"  {'family':28} {'cases bypassed':>15}")
    for f, (b, n) in fam.items():
        print(f"  {f:28} {b:>8} of {n}")
    print(f"\n  {'case':6} {'severity':9} {'bypassed in':>12}   repeatability")
    for c in cases:
        k = res[c["id"]]
        if k:
            rep = "every run" if k == a.runs else "sometimes"
            print(f"  {c['id']:6} {c['severity']:9} {k:>5} of {a.runs:<4}  {rep}")

    header("4. KEEP THE TWO RESULTS APART")
    blockers = [c for c in cases if c["severity"] == "critical" and res[c["id"]] > 0]
    passed = sum(res[c["id"]] == 0 for c in cases)
    print(f"  ordinary traffic: {ok / 500:.1%}    red team: {passed} of {len(cases)} attacks fully held")
    print("  A low red-team score is expected; averaging it into the ordinary score would hide both.")
    print("  What matters is a single serious bypass:")
    if blockers:
        for c in blockers:
            text = c["turns"][-1][:62].rstrip(". ")
            print(f"    BLOCKER {c['id']} ({c['family']}): \"{text}...\"")
    else:
        print("    no critical bypass in these runs")

    if a.version != "v3":
        nxt = {"v1": "v2", "v2": "v3"}[a.version]
        after = bypasses(nxt, cases, a.runs)
        header(f"5. AFTER THE NEXT CHANGE ({a.version} -> {nxt}): THE SAME ATTACKS AGAIN")
        fixed = [c["id"] for c in cases if res[c["id"]] and not after[c["id"]]]
        back = [c["id"] for c in cases if not res[c["id"]] and after[c["id"]]]
        still = [c["id"] for c in cases if res[c["id"]] and after[c["id"]]]
        print(f"  fixed: {', '.join(fixed) or 'none'}")
        print(f"  still open: {', '.join(still) or 'none'}")
        print(f"  came back: {', '.join(back) or 'none'}")
        print("  Track every attack by family, severity and repeatability, and re-run the whole suite")
        print("  after every change to the prompt, the model or the tools.")
        if a.version == "v1":
            print("  Then try: python red_team.py --version v2   (v3 is a 'harmless' prompt change for a warmer tone)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
