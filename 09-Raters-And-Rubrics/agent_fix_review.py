"""
agent_fix_review.py: green tests, a nice diff, and hidden risk.

Run:  python agent_fix_review.py

An agent was asked to fix a failing tenant isolation test. Two patches, both make the test pass.
  patch-A moves the authorization check from the service layer into one controller route
  patch-B fixes the check where it lives, in the shared service, and adds tests

Rubric 1: "Do the tests pass?"
Rubric 2: the post's rubric, scored dimension by dimension, with a blocker.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

from agreement import load_json

HERE = Path(__file__).parent


def tests_only(p: Dict) -> str:
    return "PASS" if p["tests_pass"] else "FAIL"


def dimensions(p: Dict) -> List[Tuple[str, bool, str]]:
    return [
        ("functional correctness", p["tests_pass"] and p["related_tests_added"],
         "the test passes" + (" and related tests were added" if p["related_tests_added"] else ", no related tests added")),
        ("security boundary kept", p["authorization_location"] == "service_layer",
         f"check lives in: {p['authorization_location'].replace('_', ' ')}"),
        ("blast radius", not p["unrelated_changes"] and p["other_entry_points_still_protected"],
         "other routes, jobs and exports still protected" if p["other_entry_points_still_protected"]
         else "other routes, background jobs and exports lost the check"),
        ("evidence", p["analyzed_existing_auth_patterns"],
         "looked at the existing authorization pattern first" if p["analyzed_existing_auth_patterns"]
         else "no sign it looked at how authorization is done elsewhere"),
        ("maintainability", p["explains_boundary"],
         "explains why the boundary is where it is" if p["explains_boundary"]
         else "in six months nobody will know why the check moved"),
    ]


def blocker(p: Dict) -> str:
    if p["authorization_location"] != "service_layer" or not p["other_entry_points_still_protected"]:
        return "weakens tenant isolation"
    return ""


def main() -> None:
    spec = load_json(HERE / "data" / "agent_patches.json")
    print(f"Task: {spec['task']}\nContext: {spec['context']}\n")
    print("=" * 78 + "\nRUBRIC 1: DO THE TESTS PASS?\n" + "=" * 78)
    for p in spec["patches"]:
        print(f"  {p['id']}: {tests_only(p)}   ({p['diff_lines']} lines changed)   {p['summary']}")
    print("  Both green. patch-A is the smaller, cleaner diff. A reviewer in a hurry merges it.")

    print("\n" + "=" * 78 + "\nRUBRIC 2: DIMENSIONS AND A BLOCKER\n" + "=" * 78)
    for p in spec["patches"]:
        print(f"\n  {p['id']}")
        for name, ok, why in dimensions(p):
            print(f"    [{'ok' if ok else '--'}] {name:24} {why}")
        b = blocker(p)
        verdict = f"BLOCKED: {b}" if b else "ACCEPT"
        print(f"    blocker: {b or 'none'}\n    verdict: {verdict}")
    print("\n  Any patch that weakens isolation fails, however clean the code looks.")
    print("  The rubric turns 'green tests, nice diff' into a decision about product quality.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
