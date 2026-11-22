"""
audit_my_eval_suite.py: the exercise from the post.

"Treat your evaluation suite like a product and check:
   - Who owns it?
   - Are the data, labels, rubric and judge versioned?
   - Which cases are already out of date?
   - Could the cases have leaked into training data, or been used for tuning again and again?
   - Does the metric match how users experience the product?
   - Can the result change the release decision?
 If the answer to the last question is 'no', you have decoration, not an evaluation."

Run:  python exercise/audit_my_eval_suite.py
      python exercise/audit_my_eval_suite.py path/to/your_eval_suite.json

Fill in exercise/my_eval_suite.json (or a copy) with your own answers.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import List, Tuple

HERE = Path(__file__).parent
DEFAULT_FILE = HERE / "my_eval_suite.json"
VERSIONED = ("dataset", "labels", "rubric", "judge")


def audit(spec) -> List[Tuple[str, str, str]]:
    """Returns (question, OK / GAP, finding) for the six questions."""
    out = []
    owner = (spec.get("1_owner") or "").strip()
    out.append(("Who owns it?", "OK" if owner else "GAP", owner or "nobody: when it breaks, nobody fixes it"))

    v = spec.get("2_versioned") or {}
    missing = [k for k in VERSIONED if not v.get(k)]
    out.append(("Data, labels, rubric and judge versioned?", "GAP" if missing else "OK",
                f"not versioned: {', '.join(missing)}" if missing else "all four"))

    today = date.fromisoformat(spec["audit_date"])
    limit = spec.get("max_days_without_review", 180)
    groups = spec.get("3_case_groups") or []
    stale = [(g, (today - date.fromisoformat(g["last_reviewed"])).days) for g in groups]
    stale = [(g, d) for g, d in stale if d > limit]
    n_stale = sum(g["cases"] for g, _ in stale)
    n_all = sum(g["cases"] for g in groups) or 1
    out.append(("Which cases are out of date?", "GAP" if stale else "OK",
                "; ".join(f"{g['group']} ({g['cases']} cases, {d} days since review)" for g, d in stale)
                + (f" -> {n_stale}/{n_all} cases ({n_stale / n_all:.0%})" if stale else "")
                or f"all groups reviewed within {limit} days"))

    lk = spec.get("4_leakage") or {}
    risks = []
    if lk.get("cases_are_public"):
        risks.append("the cases are public, a model may have trained on them")
    if (lk.get("times_used_to_tune_prompts_or_models") or 0) > 0 and not lk.get("untouched_holdout_exists"):
        risks.append(f"used {lk['times_used_to_tune_prompts_or_models']} times for tuning, with no untouched holdout")
    out.append(("Leaked, or tuned on again and again?", "GAP" if risks else "OK", "; ".join(risks) or "no known exposure"))

    mu = spec.get("5_metric_vs_users") or {}
    out.append(("Does the metric match what users experience?", "OK" if mu.get("same_thing") else "GAP",
                f"metric: {mu.get('metric')}; users experience: {mu.get('what_users_experience')}"))

    rel = spec.get("6_can_change_release") or {}
    last = rel.get("last_time_it_changed_a_decision")
    if rel.get("answer") and last:
        out.append(("Can the result change the release decision?", "OK", f"yes, last time: {last}"))
    elif rel.get("answer"):
        out.append(("Can the result change the release decision?", "GAP",
                    "'yes' in theory, but it never has: name the threshold that would stop a release"))
    else:
        out.append(("Can the result change the release decision?", "GAP", "no"))
    return out


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"Audit of: {spec.get('suite', path.name)}  ({spec['audit_date']})\n")
    results = audit(spec)
    for i, (q, status, finding) in enumerate(results, 1):
        print(f"  {i}. {q:46} {status}")
        print(f"     {finding}")
    gaps = sum(s == "GAP" for _, s, _ in results)
    rel = spec.get("6_can_change_release") or {}
    print()
    if not rel.get("answer"):
        print("Verdict: the result cannot change the release decision. You have decoration, not an evaluation.")
        print("Start there: agree which result would stop a release, before fixing anything else.")
    elif gaps:
        print(f"Verdict: an evaluation with {gaps} gap(s). Fix them in the order above; each one is a way")
        print("the number can mislead the decision it is supposed to inform.")
    else:
        print("Verdict: the suite is run like a product. Re-run this audit when the product or the users change.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
