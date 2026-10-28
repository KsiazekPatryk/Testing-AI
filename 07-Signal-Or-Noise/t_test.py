"""
t_test.py: is the difference bigger than the noise?

Run:  python t_test.py

Old prompt: mean 7.8. New prompt: mean 8.3. The same 100 test cases went through both
(data/prompt_eval.jsonl). A t-test asks whether the difference in means is large
compared with the natural spread of the results.

  1. Paired t-test: compares the two scores of each case. Some cases are simply harder;
     pairing controls for that. This is usually the right test for AI product evals.
  2. The same data, analyzed as if it were not paired: the difficulty of the cases
     becomes noise, and the evidence looks much weaker.
  3. Welch's t-test: for the case where A and B really got different test cases.
  4. A t-test is not a release gate: it looks at means, and many risks live in the tails.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean, stdev

from stats_tests import fmt_p, load_jsonl, mcnemar_exact, paired_t, welch_t

HERE = Path(__file__).parent


def main() -> None:
    rows = load_jsonl(HERE / "data" / "prompt_eval.jsonl")
    old, new = [r["old"] for r in rows], [r["new"] for r in rows]
    diffs = [n - o for o, n in zip(old, new)]
    print(f"{len(rows)} test cases, each scored 0-10 for both prompts.")
    print(f"  old prompt: mean {mean(old):.1f}, sd {stdev(old):.2f}")
    print(f"  new prompt: mean {mean(new):.1f}, sd {stdev(new):.2f}")

    print("\n" + "=" * 78 + "\n1. PAIRED t-TEST (the same cases through both versions)\n" + "=" * 78)
    p = paired_t(old, new)
    print(f"  differences per case (new − old): mean {p['diff']:+.2f}, sd {stdev(diffs):.2f}")
    print(f"  t = mean / (sd / √n) = {p['diff']:.2f} / ({stdev(diffs):.2f} / √{p['n']}) = {p['t']:.2f}, df = {p['df']}")
    print(f"  p = {fmt_p(p['p'])}, 95% CI for the improvement {p['ci_low']:+.2f} to {p['ci_high']:+.2f}")

    print("\n" + "=" * 78 + "\n2. THE SAME DATA, IGNORING THE PAIRING\n" + "=" * 78)
    w = welch_t(old, new)
    print(f"  difference {w['diff']:+.2f}, p = {fmt_p(w['p'])}, 95% CI {w['ci_low']:+.2f} to {w['ci_high']:+.2f}")
    print("  The same improvement, but the interval is much wider: the cases differ a lot in")
    print("  difficulty (sd of scores ≈ 1.5), and without pairing that difficulty counts as noise.")
    print("  If version A had happened to get the hard cases and B the easy ones, an unpaired")
    print("  comparison of means would mislead. Pairing controls for difficulty.")

    print("\n" + "=" * 78 + "\n3. WELCH'S t-TEST (A and B got DIFFERENT cases)\n" + "=" * 78)
    ab = load_jsonl(HERE / "data" / "ab_independent.jsonl")
    a_scores = [r["score"] for r in ab if r["version"] == "old"]
    b_scores = [r["score"] for r in ab if r["version"] == "new"]
    wb = welch_t(a_scores, b_scores)
    print(f"  {len(a_scores)} cases for A (mean {mean(a_scores):.2f}), {len(b_scores)} other cases for B "
          f"(mean {mean(b_scores):.2f})")
    print(f"  difference {wb['diff']:+.2f}, t = {wb['t']:.2f}, df = {wb['df']:.1f}, p = {fmt_p(wb['p'])}, "
          f"95% CI {wb['ci_low']:+.2f} to {wb['ci_high']:+.2f}")
    print("  Here the random assignment of cases to versions matters more than the test itself.")

    print("\n" + "=" * 78 + "\n4. A t-TEST IS NOT A RELEASE GATE\n" + "=" * 78)
    m = mcnemar_exact([r["old_pass"] for r in rows], [r["new_pass"] for r in rows])
    policy = [r for r in rows if r["new_policy_failure"]]
    old_pass, new_pass = sum(r["old_pass"] for r in rows), sum(r["new_pass"] for r in rows)
    print(f"  pass rate (score 7+): {old_pass}% -> {new_pass}%. B fixed {m['b_fixed']} cases and broke "
          f"{m['b_broke']} (McNemar p = {fmt_p(m['p'])}).")
    print(f"  worst score: {min(old)} -> {min(new)}. New policy failures: {len(policy)}"
          + (f" ({policy[0]['id']}: {policy[0]['old']} -> {policy[0]['new']})" if policy else ""))
    print("  The mean went up, the pass rate barely moved, and the new prompt produced a policy")
    print("  failure the old one did not have.")

    print("\n" + "=" * 78 + "\nTHE REPORT\n" + "=" * 78)
    print(f"  \"The new prompt improved the mean by {p['diff']:.1f} points; paired t-test: p = {fmt_p(p['p'])}; "
          f"95% CI for the improvement {p['ci_low']:+.1f} to {p['ci_high']:+.1f}.")
    print(f"   Pass rate {old_pass}% -> {new_pass}%; worst score {min(new)}; "
          f"{len(policy)} new policy failure{'s' if len(policy) != 1 else ''} to review before release.\"")
    print("  Much stronger than \"the new version looked better in a few examples\", and honest about the tail.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
