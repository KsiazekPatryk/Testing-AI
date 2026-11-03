"""
rubric.py: a rubric gives repeatable scores, or false precision.

Run:  python rubric.py

A rubric that works has:
  dimensions   instead of good/bad (data/rubric_support.json)
  anchors      what a 10, 7, 4 and 0 actually look like
  blockers     failures that override every score
  specificity  a medical summary weighs things differently than a support answer
  versioning   scores from different rubric versions are not mixed in one experiment

The answers in data/support_responses.jsonl were scored per dimension, following the anchors.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

from agreement import load_json, load_jsonl

HERE = Path(__file__).parent


def score(resp: Dict, rubric: Dict) -> Tuple[float, float, str]:
    """Returns (weighted score without blockers, final score, verdict)."""
    dims = rubric["dimensions"]
    raw = sum(resp["scores"][d] * spec["weight"] for d, spec in dims.items())
    if resp["blockers"]:
        return raw, 0.0, "BLOCKED: " + ", ".join(resp["blockers"])
    return raw, raw, "pass" if raw >= 7 else "fail"


def validate(rubric: Dict) -> list:
    problems = []
    if not rubric.get("dimensions"):
        problems.append("no dimensions: one number for everything")
    if not rubric.get("anchors"):
        problems.append("no anchors: '1 = bad, 10 = good' means something different to every reviewer")
    if not rubric.get("blockers"):
        problems.append("no blockers: a polite data leak can still pass")
    w = sum(s["weight"] for s in rubric.get("dimensions", {}).values()) if rubric.get("dimensions") else 1
    if abs(w - 1) > 1e-9:
        problems.append(f"weights add up to {w}, not 1")
    return problems


def main() -> None:
    vague = load_json(HERE / "data" / "rubric_vague.json")
    support = load_json(HERE / "data" / "rubric_support.json")
    medical = load_json(HERE / "data" / "rubric_medical_summary.json")
    responses = load_jsonl(HERE / "data" / "support_responses.jsonl")

    print("=" * 78 + "\nIS THE RUBRIC USABLE?\n" + "=" * 78)
    for r in (vague, support, medical):
        problems = validate(r)
        print(f"  {r['name']}: " + ("OK" if not problems else ""))
        for p in problems:
            print(f"    - {p}")

    print("\n" + "=" * 78 + f"\nANCHORS ({support['name']})\n" + "=" * 78)
    for k in sorted(support["anchors"], key=int, reverse=True):
        print(f"  {k:>2}  {support['anchors'][k]}")

    print("\n" + "=" * 78 + "\nSCORING: DIMENSIONS, WEIGHTS, BLOCKERS\n" + "=" * 78)
    dims = list(support["dimensions"])
    print("  weights: " + ", ".join(f"{d} {s['weight']:.0%}" for d, s in support["dimensions"].items()))
    print(f"\n  {'id':7} {'avg':>4} {'weighted':>8} {'final':>6}  verdict / summary")
    current = [r for r in responses if r["rubric_version"] == support["name"]]
    for resp in current:
        raw, final, verdict = score(resp, support)
        avg = sum(resp["scores"][d] for d in dims) / len(dims)
        print(f"  {resp['id']:7} {avg:4.1f} {raw:8.1f} {final:6.1f}  {verdict}\n{'':30}{resp['summary']}")
    leak = next(r for r in current if "personal_data_leak" in r["blockers"])
    raw = score(leak, support)[0]
    print(f"\n  {leak['id']} scores {leak['scores']['tone']} on tone and a weighted {raw:.1f}: "
          "without blockers it would pass.")
    print("  It leaks another customer's address. A blocker overrides every score:")
    print("  the answer does not pass just because it is polite.")

    print("\n" + "=" * 78 + "\nSPECIFICITY: ONE GENERIC RUBRIC IS CONVENIENT AND USUALLY WRONG\n" + "=" * 78)
    print("  The same idea of 'quality', weighted for two products:")
    print(f"    support answer:  " + ", ".join(f"{d} {s['weight']:.0%}" for d, s in support["dimensions"].items()))
    print(f"    medical summary: " + ", ".join(f"{d} {s['weight']:.0%}" for d, s in medical["dimensions"].items()))
    print("  In a medical summary, style is worth 5% and a missed red flag is a blocker.")

    print("\n" + "=" * 78 + "\nVERSIONING\n" + "=" * 78)
    versions = sorted({r["rubric_version"] for r in responses})
    if len(versions) > 1:
        old = [r["id"] for r in responses if r["rubric_version"] != support["name"]]
        print(f"  This batch mixes {', '.join(versions)}. Left out of the comparison: {', '.join(old)}.")
        print("  v1 had no safety dimension and no blockers, so its scores mean something else.")
    for line in support.get("changelog", []):
        print(f"  {line}")
    print("  Disagreements, production failures and confusing examples go back into the rubric,")
    print("  but between experiments, never in the middle of one.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
