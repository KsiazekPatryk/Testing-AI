"""
check_my_comparison.py: the exercise from the post.

"Pick one comparison in front of you: two prompts, two models, two policies. Write down:
   - which test you will use and why,
   - which assumption the test rests on (e.g. independent cases, pairing),
   - which product decision the result should support,
   - what minimum effect would matter to you.
 Then also write down what this test cannot tell you. That last list often turns out
 to be the most valuable."

Run:  python exercise/check_my_comparison.py
      python exercise/check_my_comparison.py path/to/your_comparison.json

The script checks the four answers, computes whether your sample can see your minimum effect
(power), and proposes items for the "cannot tell" list that your plan leaves open.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from stats_tools import (n_paired_means, n_per_group_proportions, p_any_false_alarm,  # noqa: E402
                         power_paired_means, power_proportions, smallest_detectable_paired)

DEFAULT_FILE = HERE / "my_comparison.json"
PAIRED_TESTS = ("paired", "mcnemar", "wilcoxon", "sign test", "permutation", "bootstrap")


def check_test(spec: Dict) -> Tuple[str, str]:
    t = spec.get("test") or {}
    name, why = (t.get("name") or "").lower(), t.get("why")
    if not name:
        return "MISSING", "No test chosen yet."
    if not why:
        return "WEAK", f"'{name}', but not why. Choose the test from how the data was produced, not from habit."
    paired = (spec.get("sample") or {}).get("paired")
    if paired is True and not any(p in name for p in PAIRED_TESTS):
        return "WEAK", f"The cases are paired, but '{name}' treats them as independent."
    if paired is False and any(p in name for p in PAIRED_TESTS):
        return "WEAK", f"Different cases per version, but '{name}' assumes pairs."
    return "OK", f"{name}, because {why}."


def check_text(spec: Dict, key: str, missing: str) -> Tuple[str, str]:
    v = spec.get(key)
    return ("OK", v + ".") if v else ("MISSING", missing)


def check_effect(spec: Dict) -> Tuple[str, str, Dict]:
    m = spec.get("minimum_effect") or {}
    n = (spec.get("sample") or {}).get("independent_cases")
    if m.get("value") is None:
        return "MISSING", "No minimum effect. Without it, any significant difference looks like a win.", {}
    if not n:
        return "OK", f"{m.get('metric')}: {m['value']}. Add the sample size to check the power.", {}
    if m.get("kind") == "rate" and m.get("current_rate") is not None:
        p1 = m["current_rate"]
        p2 = p1 * (1 - m["value"]) if m["value"] < 1 else p1 - m["value"]
        power = power_proportions(p1, p2, n)
        need = n_per_group_proportions(p1, p2)
        info = {"power": power, "need": need}
        target = f"{p1:.1%} -> {p2:.1%}"
    elif m.get("sd_of_differences"):
        sd = m["sd_of_differences"]
        power = power_paired_means(m["value"], sd, n)
        need = n_paired_means(m["value"], sd)
        info = {"power": power, "need": need, "detectable": smallest_detectable_paired(sd, n)}
        target = f"{m['metric']} {m['value']:+g}"
    else:
        return "OK", f"{m.get('metric')}: {m['value']}. Add the sd (or the current rate) to check the power.", {}
    if power < 0.8:
        extra = f" It reliably sees about {info['detectable']:.2f} or more." if "detectable" in info else ""
        return "TOO WEAK", (f"{target} with {n} cases: {power:.0%} power.{extra} "
                            f"You need about {need:,} cases."), info
    return "OK", f"{target} with {n} cases: {power:.0%} power.", info


def cannot_tell(spec: Dict, effect_info: Dict) -> List[str]:
    out = ["whether the change is worth its cost and latency (the test only compares the metric)",
           "how it behaves on users and situations that are not in the sample"]
    n = (spec.get("sample") or {}).get("independent_cases")
    if n:
        out.append(f"anything about failures rarer than about 1 in {max(1, n // 3)} "
                   f"(with {n} cases, zero failures still allows up to {3 / n:.0%})")
    if effect_info.get("power", 1) < 0.8:
        out.append("'no significant difference' would NOT mean 'no difference': the sample is too small")
    if not spec.get("high_risk_slices_checked"):
        out.append("whether any high-risk slice got worse (none planned)")
    k = spec.get("other_comparisons_checked") or 0
    if k:
        out.append(f"whether a lucky result among the {k + 1} comparisons is real "
                   f"(chance of at least one false alarm: {p_any_false_alarm(k + 1):.0%})")
    runs = (spec.get("sample") or {}).get("runs_per_case")
    if runs == 1:
        out.append("how stable each answer is: one run per case is an anecdote")
    return out


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"The comparison: \"{spec.get('comparison', path.name)}\"\n")
    eff = check_effect(spec)
    rows = [
        ("Which test and why?", check_test(spec)),
        ("Which assumption does it rest on?",
         check_text(spec, "assumption", "No assumption written. Every test assumes something about the data.")),
        ("Which product decision should it support?",
         check_text(spec, "decision", "No decision. Then nobody knows what result would change anything.")),
        ("Which minimum effect matters?", eff[:2]),
    ]
    for q, (verdict, why) in rows:
        print(f"  [{verdict:8}] {q}\n             {why}")

    print("\nWhat this test CANNOT tell you")
    own = spec.get("cannot_tell") or []
    print("  your list:" + ("" if own else " (empty)"))
    for item in own:
        print(f"    - {item}")
    print("  also consider:")
    for item in cannot_tell(spec, eff[2]):
        print(f"    - {item}")

    print()
    open_items = [q for q, (v, _) in rows if v != "OK"]
    if open_items:
        print(f"{len(open_items)} of 4 not ready: " + "; ".join(open_items))
        print("Fix those before running the evaluation. The 'cannot tell' list goes into the report as it is.")
    else:
        print("The plan is ready. Put the 'cannot tell' list in the report, next to the result.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
