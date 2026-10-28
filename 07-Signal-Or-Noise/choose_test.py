"""
choose_test.py: pick the test from how the data was produced, not from habit.

Run:  python choose_test.py                                # the whole table, each test run on example data
      python choose_test.py --paired yes --outcome pass_fail
      python choose_test.py --paired no --outcome ordinal

  same cases, numeric score        -> paired t-test on the differences
  different cases, numeric score   -> Welch's t-test (random assignment matters more than the test)
  same cases, pass/fail            -> McNemar (only the cases where A and B differ count)
  category counts                  -> chi-square (Fisher's exact test for small counts)
  ordinal scores, e.g. a 0-10 rubric -> Wilcoxon (paired) or Mann-Whitney (independent)
  skewed or unusual distributions  -> bootstrap or a permutation test (resample the right unit)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

from stats_tests import (bootstrap_ci, chi_square, fisher_exact, fmt_p, load_jsonl, mann_whitney,
                         mcnemar_exact, paired_t, permutation_paired, welch_t, wilcoxon_signed_rank)

HERE = Path(__file__).parent

GUIDE = [
    ("yes", "score", "Paired t-test on the differences", "Watch outliers and the shape of the differences."),
    ("no", "score", "Welch's t-test", "Random assignment of cases matters more than the test."),
    ("yes", "pass_fail", "McNemar's test", "Only the cases where A and B disagree count."),
    ("any", "categories", "Chi-square (Fisher's exact test for small counts)", "Don't turn categories into a mean."),
    ("yes", "ordinal", "Wilcoxon signed-rank", "6 -> 7 is not the same distance as 8 -> 9."),
    ("no", "ordinal", "Mann-Whitney U", "6 -> 7 is not the same distance as 8 -> 9."),
    ("any", "skewed", "Bootstrap or permutation test", "Resample the right unit (the prompt, not the run)."),
]


def recommend(paired: str, outcome: str) -> None:
    for p, o, test, note in GUIDE:
        if o == outcome and p in (paired, "any"):
            print(f"Recommended: {test}\n  {note}")
            return
    print("No match. Outcomes: score, pass_fail, categories, ordinal, skewed.")


def run_examples() -> None:
    rows = load_jsonl(HERE / "data" / "prompt_eval.jsonl")
    old, new = [r["old"] for r in rows], [r["new"] for r in rows]
    ab = load_jsonl(HERE / "data" / "ab_independent.jsonl")
    a_ind = [r["score"] for r in ab if r["version"] == "old"]
    b_ind = [r["score"] for r in ab if r["version"] == "new"]
    policy = json.loads((HERE / "data" / "escalation_policy.json").read_text(encoding="utf-8"))

    print(f"{'data':42} {'test':28} result")
    print("─" * 100)
    p = paired_t(old, new)
    print(f"{'same 100 cases, numeric score':42} {'paired t-test':28} diff {p['diff']:+.2f}, p = {fmt_p(p['p'])}")
    w = welch_t(a_ind, b_ind)
    print(f"{'80 + 80 different cases, numeric score':42} {'Welch t-test':28} diff {w['diff']:+.2f}, p = {fmt_p(w['p'])}")
    m = mcnemar_exact([r["old_pass"] for r in rows], [r["new_pass"] for r in rows])
    print(f"{'same 100 cases, pass/fail (score 7+)':42} {'McNemar':28} B fixed {m['b_fixed']}, broke "
          f"{m['b_broke']}, p = {fmt_p(m['p'])}")
    c = chi_square([policy["old_policy"], policy["new_policy"]])
    print(f"{'outcome counts, 2 policies x 3 outcomes':42} {'chi-square':28} χ² = {c['chi2']:.2f}, df {c['df']}, "
          f"p = {fmt_p(c['p'])}")
    small = [[1, 9], [6, 4]]
    print(f"{'rare failures, 10 cases per version':42} {'Fisher exact':28} 1/10 vs 6/10 failed, "
          f"p = {fmt_p(fisher_exact(small))}")
    wx = wilcoxon_signed_rank(old, new)
    print(f"{'same 100 cases, 0-10 rubric (ordinal)':42} {'Wilcoxon signed-rank':28} "
          f"{wx['n_nonzero']} non-zero pairs, p = {fmt_p(wx['p'])}")
    mw = mann_whitney(a_ind, b_ind)
    print(f"{'different cases, 0-10 rubric (ordinal)':42} {'Mann-Whitney U':28} P(B > A) = "
          f"{mw['prob_b_higher']:.2f}, p = {fmt_p(mw['p'])}")
    perm = permutation_paired(old, new, seed=1)
    lo, hi = bootstrap_ci([n - o for o, n in zip(old, new)], seed=1)
    print(f"{'same 100 cases, no assumptions':42} {'permutation (sign flips)':28} p = {fmt_p(perm)}")
    print(f"{'':42} {'bootstrap of differences':28} 95% CI {lo:+.2f} to {hi:+.2f} "
          f"(mean {mean(n - o for o, n in zip(old, new)):+.2f})")

    print("\nThe same 100 cases answer different questions with different tests: the mean improved")
    print("(t, Wilcoxon, permutation and bootstrap agree), while the pass rate did not move (McNemar).")
    print("Report the raw counts and percentages with every p-value, not the p-value alone.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Which statistical test fits your data?")
    ap.add_argument("--paired", choices=["yes", "no"])
    ap.add_argument("--outcome", choices=["score", "pass_fail", "categories", "ordinal", "skewed"])
    a = ap.parse_args()
    if a.paired or a.outcome:
        recommend(a.paired or "yes", a.outcome or "score")
        return
    print("Which test? Start from how the data was produced.\n")
    print(f"{'same cases?':12} {'outcome':12} {'test':50} watch out")
    print("─" * 112)
    for p, o, test, note in GUIDE:
        print(f"{p:12} {o:12} {test:50} {note}")
    print("\nEach test, run on the example data in data/:\n")
    run_examples()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
