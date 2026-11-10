"""
calibration.py: does the judge score the way your best reviewer would?

Run:  python calibration.py

A trusted reviewer scored 240 support replies with the same anchored rubric the judge uses.
  1. where judge and human agree, where they differ, and whether the differences form a pattern
  2. the four fixes, cheapest first:
       a. examples in the judge prompt (judge_v1 -> judge_v2)
       b. a better rubric: blocker checks kept separate from the quality score
       c. a per-segment correction, learned on one half of the data and checked on the other
       d. routing rules
The result of calibration is not one "judge accuracy" number. It is a set of routing rules,
written to output/routing_rules.json and used by routing.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

from judge import blockers_v2, judge_v1, judge_v2
from metrics import cohen_kappa, load_jsonl, mean, mean_diff, pass_agreement, within

HERE = Path(__file__).parent
SEGMENTS = ("general", "refunds", "privacy", "medical")
HIGH_RISK = {"medical"}
PASS = 7


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def table(rows: List[Dict], key: str) -> None:
    print(f"  {'segment':9} {'n':>4} {'judge - human':>14} {'within 1 pt':>12} {'pass/fail agree':>16}")
    for seg in SEGMENTS + ("all",):
        sub = rows if seg == "all" else [r for r in rows if r["segment"] == seg]
        h = [r["human"] for r in sub]
        j = [r[key] for r in sub]
        print(f"  {seg:9} {len(sub):>4} {mean_diff(h, j):>+14.2f} {within(h, j):>12.0%} {pass_agreement(h, j, PASS):>16.0%}")


def correction(train: List[Dict], min_n: int = 5) -> Dict[str, Dict[int, float]]:
    """Per segment and judge score: how far the human's mean sits from the judge, on the calibration half.
    Only clear patterns (enough cases, at least 1 point) become corrections."""
    out: Dict[str, Dict[int, float]] = {}
    for seg in SEGMENTS:
        out[seg] = {}
        for score in range(11):
            sub = [r for r in train if r["segment"] == seg and r["v2"] == score]
            if len(sub) >= min_n:
                off = mean([r["human"] - r["v2"] for r in sub])
                if abs(off) >= 1.0:
                    out[seg][score] = round(off, 1)
    return out


def corrected(r: Dict, corr: Dict[str, Dict[int, float]]) -> float:
    return max(0.0, min(10.0, r["v2"] + corr[r["segment"]].get(r["v2"], 0.0)))


def main() -> None:
    rows = load_jsonl(HERE / "data" / "replies.jsonl")
    for r in rows:
        r["v1"] = judge_v1(r["reply"])[0]
        r["v2"] = judge_v2(r["reply"], context=r["question"])[0]

    header("1. JUDGE v2 vs THE TRUSTED REVIEWER, 240 REPLIES")
    table(rows, "v2")
    k = cohen_kappa([r["human"] >= PASS for r in rows], [r["v2"] >= PASS for r in rows])
    print(f"\n  overall: within 1 point {within([r['human'] for r in rows], [r['v2'] for r in rows]):.0%}, "
          f"pass/fail kappa {k:.2f}.")
    print("  A decent headline. Now look for patterns, not one number:")
    priv10 = [r for r in rows if r["segment"] == "privacy" and r["v2"] == 10]
    print(f"  privacy replies the judge scored 10: {len(priv10)}; the reviewer's mean for them "
          f"{mean([r['human'] for r in priv10]):.1f}")
    print("  They over-share: an address, a name. The judge reads 'I can confirm' as diligence and")
    print("  rewards the warm tone; the reviewer sees personal data handed out. Not random noise:")
    print("  a systematic, one-sided gap in one segment.")

    header("2a. EXAMPLES IN THE PROMPT: judge_v1 (bare prompt) vs judge_v2")
    print("  judge_v1:")
    table(rows, "v1")
    print("  v1 rewards warmth and length and has no policy in context. The cheapest fix is the prompt:")
    print("  anchors, the policy, and examples such as 'a friendly reply that breaks policy = 4',")
    print("  'a short, correct reply = 9'.")

    header("2b. BLOCKERS SEPARATE FROM THE QUALITY SCORE")
    flagged = [r for r in rows if blockers_v2(r["reply"], r["question"])]
    bad = [r for r in rows if r["human"] <= 4]
    tp = [r for r in flagged if r["human"] <= 4]
    print(f"  blocker checks fired on {len(flagged)} replies; the human scored {len(tp)} of them 4 or lower.")
    print(f"  of the {len(bad)} replies the human scored 4 or lower, the blockers caught {len(set(map(id, tp)))}.")
    print("  A blocker is a yes/no question with its own rule. It does not get averaged away by a warm tone.")

    header("2c. PER-SEGMENT CORRECTION, CHECKED ON HELD-OUT DATA")
    train = [r for i, r in enumerate(rows) if i % 2 == 0]
    test = [r for i, r in enumerate(rows) if i % 2 == 1]
    corr = correction(train)
    print("  learned on the calibration half (judge score -> correction):")
    for seg, m in corr.items():
        print(f"    {seg:9} " + (", ".join(f"{k} -> {k + v:.1f}" for k, v in sorted(m.items())) or "none"))
    print(f"  checked on the held-out half ({len(test)} replies):")
    for seg in SEGMENTS:
        sub = [r for r in test if r["segment"] == seg]
        before = mean([abs(r["v2"] - r["human"]) for r in sub])
        after = mean([abs(corrected(r, corr) - r["human"]) for r in sub])
        pf0 = pass_agreement([r["human"] for r in sub], [r["v2"] for r in sub], PASS)
        pf1 = pass_agreement([r["human"] for r in sub], [corrected(r, corr) for r in sub], PASS)
        print(f"    {seg:9} mean error {before:.2f} -> {after:.2f}   pass/fail agreement {pf0:.0%} -> {pf1:.0%}")
    print("  Re-check the correction after every change to the model, the prompt or the rubric.")

    header("2d. ROUTING RULES: THE OUTPUT OF CALIBRATION")
    rules = {}
    for seg in SEGMENTS:
        sub = [r for r in test if r["segment"] == seg]
        h = [r["human"] for r in sub]
        j = [corrected(r, corr) for r in sub]
        agree, close = pass_agreement(h, j, PASS), within(h, j)
        if seg in HIGH_RISK:
            rule = {"route": "human", "audit_rate": 1.0, "why": "high risk: the judge pre-sorts, a human decides"}
        elif agree >= 0.95 and close >= 0.85 and not corr[seg]:
            rule = {"route": "automatic", "audit_rate": 0.05, "why": f"pass/fail agreement {agree:.0%}, within 1 pt {close:.0%}"}
        elif agree >= 0.90:
            rule = {"route": "automatic_corrected", "audit_rate": 0.20,
                    "why": f"after correction: pass/fail agreement {agree:.0%}, within 1 pt {close:.0%}"}
        else:
            rule = {"route": "human", "audit_rate": 1.0, "why": f"pass/fail agreement only {agree:.0%}"}
        rule["correction"] = {str(k): v for k, v in corr[seg].items()}
        rule["blocker_found"] = "block the release"
        rules[seg] = rule
        print(f"  {seg:9} {rule['route']:20} audit {rule['audit_rate']:>4.0%}   {rule['why']}")
    print("  any segment: a blocker found -> blocks the release")
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    (out / "routing_rules.json").write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")
    print(f"\n  Written to {out / 'routing_rules.json'}. Apply them: python routing.py")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
