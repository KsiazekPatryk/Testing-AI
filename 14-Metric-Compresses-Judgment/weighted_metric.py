"""
weighted_metric.py: a quality metric compresses judgment, it does not replace it.

Run:  python weighted_metric.py

When there are too many observations to read, you need a metric that is explicit, repeatable and
lets you compare versions. Usually that is a weighted sum of 0-1 criterion scores. The number is a
summary of what the team values, not an objective truth. Two rules keep it honest:

  - the weights are set BEFORE anyone sees the results;
  - blockers sit OUTSIDE the average: a serious failure stops the release even when the rest is good.

  1. the metric from the post: a shop chatbot, six criteria, a weighted score of 0.84
  2. weights before results: the same two candidates, a different winner if you pick weights afterwards
  3. the blocker example: allergy, nut snacks, an order that ships in 12 minutes
  4. why the blocker cannot be one more criterion in the average
  5. what the number does not say
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

from metrickit import contributions, fingerprint, load_json, weighted_score

HERE = Path(__file__).parent


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def blocker_checks(reply: Dict, right_tools: List[str]) -> List[Tuple[str, str]]:
    """Read the trace, not the text. Returns (check, PASS / FAIL / n/a) for the high-risk-order blocker."""
    trace = reply["trace"]
    tools = [s for s in trace if s["step"] == "tool"]
    recognized = any(s["step"] == "classify" and s.get("risk") for s in trace)
    looked_up = any(t["name"] == "get_order" for t in tools)
    right_tool = any(t["name"] in right_tools for t in tools)
    failed = [i for i, s in enumerate(trace) if s["step"] == "tool" and s["status"] != "ok"]
    if failed:
        escalated = any(s["step"] == "escalate" and s.get("priority") == "urgent" for s in trace[failed[0]:])
        esc = "PASS" if escalated else "FAIL"
    else:
        esc = "n/a"
    last_action = max([i for i, s in enumerate(trace) if s["step"] in ("tool", "escalate")
                       and s.get("name") != "get_order"] or [-1])
    reread = any(s["step"] == "tool" and s["name"] == "get_order" for s in trace[last_action + 1:]) if last_action >= 0 else False
    told = any(s["step"] == "reply" and s.get("states_final_order") for s in trace)
    ok = lambda b: "PASS" if b else "FAIL"  # noqa: E731
    return [("recognized_risk", ok(recognized)), ("checked_order_status", ok(looked_up)),
            ("used_right_tool", ok(right_tool)), ("escalated_when_tool_failed", esc),
            ("confirmed_final_state", ok(reread and told))]


def show_metric(spec: Dict, scores: Dict[str, float]) -> float:
    contrib = contributions(scores, spec["weights"])
    print(f"  {'criterion':14} {'weight':>6}  {'score':>5}  {'points':>6}")
    for k, w in spec["weights"].items():
        print(f"  {k:14} {w:6.2f}  {scores[k]:5.2f}  {contrib[k]:6.3f}")
    total = sum(contrib.values())
    print(f"  {'':14} {sum(spec['weights'].values()):6.2f}  {'':5}  {total:6.3f}   <- weighted score")
    return total


def main() -> None:
    spec = load_json(HERE / "data" / "metric_spec.json")
    cand = load_json(HERE / "data" / "candidates.json")
    case = load_json(HERE / "data" / "allergy_case.json")

    header("1. THE METRIC: A SHOP CHATBOT, SIX CRITERIA")
    total = show_metric(spec, cand["candidates"]["A"])
    print(f"\n  Candidate A scores {total:.2f}. The number is a summary of what the team values (here:")
    print("  correctness above everything, tone at a tenth), not an objective truth about quality.")

    header("2. WEIGHTS ARE SET BEFORE ANYONE SEES THE RESULTS")
    fp = fingerprint(spec["weights"])
    frozen_ok = fp == spec["frozen_fingerprint"] and spec["frozen_at"] < cand["run_at"]
    print(f"  weights frozen on {spec['frozen_at']}, fingerprint {spec['frozen_fingerprint']}; results run on {cand['run_at']}")
    print(f"  fingerprint of the weights used now: {fp}  ->  {'unchanged since freezing' if frozen_ok else 'CHANGED after freezing'}")
    late = cand["proposed_after_results"]
    rows = [("frozen weights", spec["weights"]), (f"proposed {late['proposed_at']}", late["weights"])]
    print(f"\n  {'weights':22} {'A':>6} {'B':>6}  winner")
    for name, w in rows:
        a, b = (weighted_score(cand["candidates"][c], w) for c in ("A", "B"))
        print(f"  {name:22} {a:6.3f} {b:6.3f}  {'A' if a > b else 'B'}")
    print("\n  Same answers, same scores, a different winner. If you can pick the winner by picking")
    print("  the weights, pick the weights first. The proposal from the day after the run is a")
    print("  legitimate discussion for the NEXT metric version, not a reason to re-score this decision.")

    header("3. THE BLOCKER: ALLERGY, NUT SNACKS, SHIPS IN 12 MINUTES")
    print(f"  Customer: {case['customer']}")
    print(f"  Order {case['order']['id']} ships in {case['order']['ships_in_minutes']} minutes.\n")
    results = {}
    for name, reply in case["replies"].items():
        ws = weighted_score(reply["criterion_scores"], spec["weights"])
        checks = blocker_checks(reply, case["right_tools"])
        nuts = "nut snack mix" in reply["final_order_items"]
        results[name] = (ws, checks)
        print(f"  [{name}, candidate {reply['system']}] \"{reply['text'][:88]}...\"")
        print(f"    helpfulness judge: {reply['helpfulness_judge_0_10']}/10   weighted score: {ws:.2f}"
              f"   nuts still in the order: {'YES' if nuts else 'no'}")
        print("    " + "   ".join(f"{c} {r}" for c, r in checks))
        print()
    print("  A general 'helpfulness' grade is too soft here: it prefers the warm reply (8 vs 6).")
    print("  The metric has to check what the system DID: recognize the risk, look up the order, use")
    print("  the right tool, escalate when the tool failed, and confirm the final state.")
    print("  An empathetic reply that leaves the nuts in the order must not get a high score.")

    header("4. WHY THE BLOCKER CANNOT BE ONE MORE CRITERION IN THE AVERAGE")
    ws, checks = results["warm"]
    passed = sum(r != "FAIL" for _, r in checks) / len(checks)
    blended = 0.9 * ws + 0.1 * passed
    print(f"  Put the blocker checks into the average with weight 0.10 (the rest scaled to 0.90):")
    print(f"  warm reply: 0.90 x {ws:.2f} + 0.10 x {passed:.2f} = {blended:.2f}   threshold {spec['release_threshold']:.2f}"
          f"  ->  {'passes' if blended >= spec['release_threshold'] else 'fails'}")
    print("  Averaged in, the nuts-in-the-order failure is a rounding error. Kept outside:")
    print()
    print(f"  release gate (threshold {spec['release_threshold']:.2f}, blocker high_risk_order):")
    for name, reply in case["replies"].items():
        c = reply["system"]
        score_c = weighted_score(cand["candidates"][c], spec["weights"])
        failed = [k for k, r in results[name][1] if r == "FAIL"]
        verdict = "BLOCKED" if failed else ("GO" if score_c >= spec["release_threshold"] else "NO-GO")
        print(f"    candidate {c}: weighted {score_c:.2f}, failed blocker checks: {len(failed)}  ->  {verdict}")
    print("  The candidate with the higher average is the one that leaves the nuts in the order.")

    header("5. WHAT THE NUMBER DOES NOT SAY")
    for q in ("What does a mistake cost, and who pays for it?",
              "What does the worst case look like, not the average case?",
              "Which operational limits does the metric ignore (time, staff, stock, money)?",
              "Are the errors independent, or do they all fail together?",
              "How fast can we stop the system or roll it back when the number was wrong?"):
        print(f"  - {q}")
    print("  The next script (what_metric_misses.py) shows two of these on real-looking data.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
