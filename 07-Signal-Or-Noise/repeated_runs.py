"""
repeated_runs.py: 2,000 results are not 2,000 pieces of evidence.

Run:  python repeated_runs.py

100 test prompts, each run 20 times per version (data/repeated_runs.jsonl). That is 2,000
results per version, but not 2,000 independent pieces of information: the 20 answers to
the same prompt share its wording, difficulty and context.

Repeats are valuable (they measure the spread within a prompt), but they do not turn
100 independent cases into 2,000. Summarize repeats at the prompt level first, then
compute uncertainty. If significance disappears at the prompt level, the original result
counted related observations as independent.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List

from stats_tests import bootstrap_ci, fmt_p, load_jsonl, paired_t, welch_t

HERE = Path(__file__).parent


def main() -> None:
    rows = load_jsonl(HERE / "data" / "repeated_runs.jsonl")
    by_prompt: Dict[str, Dict[str, List[float]]] = {}
    for r in rows:
        by_prompt.setdefault(r["prompt"], {"old": [], "new": []})[r["version"]].append(r["score"])
    runs = len(next(iter(by_prompt.values()))["old"])
    old_all = [r["score"] for r in rows if r["version"] == "old"]
    new_all = [r["score"] for r in rows if r["version"] == "new"]
    print(f"{len(by_prompt)} prompts x {runs} runs = {len(old_all)} results per version.\n")

    print("=" * 78 + "\nWRONG: treat every run as an independent case\n" + "=" * 78)
    w = welch_t(old_all, new_all)
    print(f"  n = {len(old_all)} + {len(new_all)}, difference {w['diff']:+.3f}, p = {fmt_p(w['p'])}, "
          f"95% CI {w['ci_low']:+.3f} to {w['ci_high']:+.3f}")
    print("  Looks like a clear, significant win.")

    print("\n" + "=" * 78 + "\nRIGHT: summarize each prompt first, then compare the prompts\n" + "=" * 78)
    old_m = [mean(v["old"]) for v in by_prompt.values()]
    new_m = [mean(v["new"]) for v in by_prompt.values()]
    p = paired_t(old_m, new_m)
    print(f"  n = {p['n']} prompts (paired), difference {p['diff']:+.3f}, p = {fmt_p(p['p'])}, "
          f"95% CI {p['ci_low']:+.3f} to {p['ci_high']:+.3f}")
    diffs = [n - o for o, n in zip(old_m, new_m)]
    lo, hi = bootstrap_ci(diffs, seed=1)
    print(f"  bootstrap over prompts (the right unit): 95% CI {lo:+.3f} to {hi:+.3f}")
    better = sum(d > 0 for d in diffs)
    print(f"  the new version is better on {better} of {len(diffs)} prompts and worse on {len(diffs) - better}")

    run_sd = mean((stdev(v["old"]) + stdev(v["new"])) / 2 for v in by_prompt.values())
    noise_per_prompt = (2 * run_sd ** 2 / runs) ** 0.5
    print("\n" + "=" * 78 + "\nWHY\n" + "=" * 78)
    print(f"  how much one prompt's difference wobbles between runs (sd of a 20-run mean diff): ≈ {noise_per_prompt:.2f}")
    print(f"  how much the new version's effect differs from prompt to prompt (sd):          ≈ {stdev(diffs):.2f}")
    print("  The second number dominates: whether the new version helps depends mostly on WHICH")
    print("  prompt it gets. 20 runs pin down one prompt's result well, but they are still one prompt.")
    print("  The evidence about the version is 100 prompts, not 2,000 runs.")
    if w["p"] < 0.05 <= p["p"]:
        print(f"\n  Significance disappeared at the prompt level (p {fmt_p(w['p'])} -> {fmt_p(p['p'])}).")
        print("  The original result counted related observations as independent.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
