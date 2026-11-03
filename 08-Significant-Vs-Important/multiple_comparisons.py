"""
multiple_comparisons.py: roll the die a hundred times, remember the best roll.

Run:  python multiple_comparisons.py
      python multiple_comparisons.py --comparisons 20

If you look at enough variants, slices and metrics, something will look impressive by chance.
  1. the arithmetic: 1 - 0.95^m
  2. the agent search: 200 configurations of a flaky-test-fixing agent, one hits 91% vs 84% in production
  3. the five questions to ask before celebrating, answered from the data
  4. a dashboard with many slices: report how many comparisons you checked (Holm, Benjamini-Hochberg)
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from statistics import mean, pstdev

from stats_tools import (benjamini_hochberg, holm, load_json, load_jsonl, p_any_false_alarm, p_str,
                         two_proportions)

HERE = Path(__file__).parent


def header(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def arithmetic(m: int) -> None:
    header("1. THE ARITHMETIC")
    print("  Each comparison has a 5% chance of a false alarm. At least one false discovery in m comparisons:")
    for k in sorted({1, 5, 10, 20, 50, 100, 200, m}):
        x = p_any_false_alarm(k)
        print(f"    m = {k:>3}: 1 - 0.95^{k:<3} = " + ("> 99.9%" if x > 0.999 else f"{x:6.1%}"))


def agent_search() -> None:
    rows = load_jsonl(HERE / "data" / "agent_search.jsonl")
    confirm = load_json(HERE / "data" / "agent_confirm.json")
    prod = next(r for r in rows if r["production"])
    cands = [r for r in rows if not r["production"]]
    best = max(cands, key=lambda r: r["passed"])
    n = prod["tasks"]

    header(f"2. THE AGENT SEARCH: {len(cands)} CONFIGURATIONS TRIED ON THE SAME {n} DEV TASKS")
    rates = [r["passed"] / n for r in cands]
    print(f"  production ({prod['config']}): {prod['passed'] / n:.0%}")
    print(f"  the {len(cands)} candidates: median {sorted(rates)[len(rates) // 2]:.0%}, "
          f"spread (sd) {pstdev(rates):.1%}, best {max(rates):.0%}")
    print(f"  winner {best['config']}: {best['prompt']}, {best['model']}, tools={best['tools']}, "
          f"{best['judge_rubric']}: {best['passed'] / n:.0%}")
    res = two_proportions(prod["passed"], n, best["passed"], n)
    print(f"  Winner vs production on its own: {(res['p2'] - res['p1']) * 100:+.0f} points, {p_str(res['p'])}.")
    print(f"  But it was picked as the best of {len(cands)}. The true rates of these configurations hardly")
    print(f"  differ (sd {pstdev([r['honest_rate'] for r in cands]):.1%}); the best of {len(cands)} draws is lucky by construction.")

    header("3. BEFORE YOU CELEBRATE SEVEN POINTS")
    print(f"  a) Chosen before the test, or found after {len(cands) - 1} other attempts?")
    print(f"     Found. It is an exploration result, not a confirmed one.")
    fresh = confirm["fresh_tasks"]
    w, p = confirm["winner"]["fresh_runs_passed"], confirm["production"]["fresh_runs_passed"]
    print(f"  b) Does it win on a fresh set the team did not use for choosing? ({fresh} new tasks)")
    print(f"     winner {w[0] / fresh:.0%}, production {p[0] / fresh:.0%}.")
    e_b, e_p = best["easy_passed"] / best["easy_tasks"], prod["easy_passed"] / prod["easy_tasks"]
    h_b, h_p = best["hard_passed"] / best["hard_tasks"], prod["hard_passed"] / prod["hard_tasks"]
    print(f"  c) Same gain for every task type? easy {e_p:.0%} -> {e_b:.0%}, hard {h_p:.0%} -> {h_b:.0%}.")
    weak = best["passes_that_weakened_a_test"]
    print(f"  d) Does it 'fix' flaky tests by weakening or deleting them? {weak} of its {best['passed']} passes did")
    print(f"     (it was allowed to edit test files: tools={best['tools']}).")
    print(f"  e) Does it still win when the evaluation is repeated? {len(w)} runs on the fresh set:")
    print(f"     winner     {', '.join(f'{x / fresh:.0%}' for x in w)}  (mean {mean(w) / fresh:.1%})")
    print(f"     production {', '.join(f'{x / fresh:.0%}' for x in p)}  (mean {mean(p) / fresh:.1%})")
    print("  The seven points came from the search, not from the configuration.")
    print("  Exploration is useful. Label it as exploration, and confirm a find on a held-out set.")


def dashboard(seed: int = 3) -> None:
    header("4. A DASHBOARD WITH 40 SLICES")
    rng = random.Random(seed)
    names = [f"{lang}/{chan}" for lang in ("pl", "en", "de", "uk", "cs") for chan in
             ("web", "app", "email", "chat", "voice", "b2b", "vip", "new_users")]
    planned = {"pl/vip": 0.06, "en/vip": 0.06}            # two slices with a real effect, planned up front
    pvals = []
    for name in names:
        n = 600
        a = sum(rng.random() < 0.80 for _ in range(n))
        b = sum(rng.random() < 0.80 + planned.get(name, 0.0) for _ in range(n))
        pvals.append(two_proportions(a, n, b, n)["p"])
    raw = [n for n, p in zip(names, pvals) if p < 0.05]
    h = [n for n, k in zip(names, holm(pvals)) if k]
    bh = [n for n, k in zip(names, benjamini_hochberg(pvals)) if k]
    print(f"  40 slices compared. Only two were planned and have a real effect: {', '.join(planned)}.")
    print(f"  p < 0.05 without correction ({len(raw)}): {', '.join(raw)}")
    print(f"  Holm, controls the chance of ANY false alarm ({len(h)}): {', '.join(h) or 'none'}")
    print(f"  Benjamini-Hochberg, controls the SHARE of false alarms ({len(bh)}): {', '.join(bh) or 'none'}")
    print("  With a correction, the false alarms drop out. Some real effects can drop out too,")
    print("  which is why planned slices are tested on their own and the rest is called exploration.")
    print("  On the dashboard, write: '40 slices checked, 2 planned; the rest is exploration.'")


def main() -> None:
    ap = argparse.ArgumentParser(description="Multiple comparisons: the best of many is lucky.")
    ap.add_argument("--comparisons", type=int, default=100)
    a = ap.parse_args()
    arithmetic(a.comparisons)
    agent_search()
    dashboard()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
