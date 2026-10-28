"""
check_my_win.py: the exercise from the post.

"Take the last comparison of two versions that your team called a win, and answer three questions:
   1. Were the hypothesis and the metric written down before the test, or chosen after seeing the results?
   2. Were the cases paired, and did the test take that into account?
   3. How many independent cases (not runs) stood behind the result?
 If you can't answer any of them, that 'win' is still a hypothesis."

Run:  python exercise/check_my_win.py
      python exercise/check_my_win.py path/to/your_win.json

The example file describes a typical announced win. With raw results attached, the script
also recomputes the comparison the right way: per independent case, paired if the cases
were paired.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from stats_tests import fmt_p, load_jsonl, paired_t, welch_t  # noqa: E402

DEFAULT_FILE = HERE / "my_win.json"
PAIRED_TESTS = ("paired", "mcnemar", "wilcoxon", "sign test", "permutation", "bootstrap")


def q1(a: Dict) -> Tuple[str, str]:
    written, seen = a.get("hypothesis_written_at"), a.get("results_first_seen_at")
    if not written or not seen:
        return "UNKNOWN", "Nobody can say when the hypothesis was written relative to the results."
    if a.get("metric_chosen_after_seeing_results") or written > seen:
        return "NO", (f"Hypothesis written {written}, results first seen {seen}"
                      + (", metric picked after the results" if a.get("metric_chosen_after_seeing_results") else "")
                      + ". This is the setup for p-hacking and after-the-fact stories.")
    return "YES", f"Written {written}, before the results ({seen})."


def q2(a: Dict) -> Tuple[str, str]:
    same, test = a.get("same_cases_through_both_versions"), (a.get("test_used") or "").lower()
    if same is None or not test:
        return "UNKNOWN", "Unknown whether the cases were paired or which test was used."
    paired_test = any(t in test for t in PAIRED_TESTS)
    if same and not paired_test:
        return "NO", f"The cases were paired, but the test ({test}) treated them as independent."
    if not same and paired_test:
        return "NO", f"Different cases per version, but a paired test ({test}) was used."
    return "YES", f"{'Paired' if same else 'Independent'} cases, analyzed with {test}."


def q3(a: Dict, recomputed: Optional[int]) -> Tuple[str, str]:
    cases, total = a.get("independent_cases"), a.get("total_results")
    if not cases:
        if recomputed:
            return "NO", (f"Nobody counted them before announcing. The raw data shows {recomputed} independent "
                          f"cases behind {total or 'all the'} results: the evidence is {recomputed}, not {total}.")
        return "UNKNOWN", f"{total or 'An unknown number of'} results, but nobody counted the independent cases."
    if total and total > cases:
        return "YES", f"{cases} independent cases behind {total} results. The evidence is {cases}, not {total}."
    return "YES", f"{cases} independent cases."


def recompute(spec: Dict, base: Path) -> Optional[Dict]:
    r = spec.get("results")
    if not r or not r.get("file"):
        return None
    rows = load_jsonl((base / r["file"]).resolve())
    per_case: Dict[str, Dict[str, List[float]]] = {}
    for row in rows:
        per_case.setdefault(str(row[r["case_field"]]), {}).setdefault(row[r["version_field"]], []).append(
            float(row[r["score_field"]]))
    old_all = [x for v in per_case.values() for x in v.get(r["old"], [])]
    new_all = [x for v in per_case.values() for x in v.get(r["new"], [])]
    both = [v for v in per_case.values() if r["old"] in v and r["new"] in v]
    out = {"cases": len(per_case), "results": len(rows), "naive": welch_t(old_all, new_all)}
    if len(both) == len(per_case):
        out["right"] = paired_t([mean(v[r["old"]]) for v in both], [mean(v[r["new"]]) for v in both])
        out["right_label"] = f"paired t-test on {len(both)} per-case means"
    else:
        out["right"] = welch_t([mean(v[r["old"]]) for v in per_case.values() if r["old"] in v],
                               [mean(v[r["new"]]) for v in per_case.values() if r["new"] in v])
        out["right_label"] = "Welch t-test on per-case means"
    return out


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    rec = recompute(spec, path.parent)
    print(f"The claimed win: \"{spec['claim']}\"\n")

    answers = [
        ("1. Hypothesis and metric written before the test?", q1(spec.get("q1_written_before_test", {}))),
        ("2. Cases paired, and the test took that into account?", q2(spec.get("q2_pairing", {}))),
        ("3. How many independent cases (not runs)?", q3(spec.get("q3_independent_cases", {}),
                                                        rec["cases"] if rec else None)),
    ]
    for question, (verdict, why) in answers:
        print(f"  [{verdict:7}] {question}\n            {why}")

    if rec:
        n, r = rec["naive"], rec["right"]
        print("\nRecomputed from the raw results:")
        print(f"  as announced (every run independent, {rec['results']} results): "
              f"diff {n['diff']:+.3f}, p = {fmt_p(n['p'])}")
        print(f"  the right way ({rec['right_label']}): diff {r['diff']:+.3f}, p = {fmt_p(r['p'])}, "
              f"95% CI {r['ci_low']:+.3f} to {r['ci_high']:+.3f}")
        if r["ci_low"] <= 0 <= r["ci_high"]:
            print("  The interval crosses zero: at the level of independent cases, the data does not settle it.")

    weak = [q for q, (v, _) in answers if v != "YES"]
    print()
    if weak:
        print(f"{len(weak)} of 3 questions could not be answered with a clear yes.")
        print("This 'win' is, for now, a hypothesis. Write it down properly and test it again:")
        print("  hypothesis and metric first, a test that matches how the data was produced,")
        print("  and uncertainty computed over independent cases.")
    else:
        print("All three answered. The win has a solid basis; now check the tails and the release gate.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
