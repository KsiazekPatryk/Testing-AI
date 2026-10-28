"""
null_hypothesis.py: start with the boring assumption, and write it down before the test.

Run:  python null_hypothesis.py
      python null_hypothesis.py --slices 40 --seed 3

H0: the new version is not meaningfully different from the old one.
H1: it is different, or better in the way we care about.
You never prove H0. Either the evidence is strong enough to reject it, or it is too weak.

Part 1 prints the preregistration (preregistration.json): comparison, population, metric,
sample, test and decision threshold, written before anyone saw the results.

Part 2 shows why that matters. Two versions that are truly identical are compared on
20 slices (languages, topics, metrics). Keep slicing until something looks significant,
and something usually will: that is p-hacking.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from stats_tests import fmt_p, welch_t

HERE = Path(__file__).parent
SLICE_NAMES = ["English", "Polish", "Spanish", "German", "billing", "returns", "shipping", "sizing",
               "new customers", "VIP customers", "mobile", "desktop", "morning", "evening",
               "short questions", "long questions", "with typos", "without typos", "weekday", "weekend"]


def print_preregistration() -> None:
    spec = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    print("=" * 78)
    print(f"PREREGISTRATION (written {spec['written_at']}, before the evaluation)")
    print("=" * 78)
    for key in ("comparison", "population", "null_hypothesis", "alternative", "metric", "sample",
                "test", "decision_threshold"):
        print(f"  {key.replace('_', ' ') + ':':20} {spec[key]}")
    print(f"  {'secondary metrics:':20} {', '.join(spec['secondary_metrics'])}")
    print("\nA good null hypothesis names the comparison, the population, the metric and the decision.")


def p_hacking(slices: int, seed: int) -> None:
    rng = random.Random(seed)
    print("\n" + "=" * 78)
    print(f"P-HACKING: {slices} slices, two versions that are truly IDENTICAL")
    print("=" * 78)
    hits = []
    for i in range(slices):
        name = SLICE_NAMES[i % len(SLICE_NAMES)] + ("" if i < len(SLICE_NAMES) else f" #{i // len(SLICE_NAMES) + 1}")
        old = [rng.gauss(7.8, 1.5) for _ in range(30)]
        new = [rng.gauss(7.8, 1.5) for _ in range(30)]       # same distribution: no real difference
        res = welch_t(old, new)
        flag = "  <- \"significant\"!" if res["p"] < 0.05 else ""
        if flag:
            hits.append((name, res))
        print(f"  {name:22} diff {res['diff']:+.2f}   p = {fmt_p(res['p'])}{flag}")
    print(f"\n{len(hits)} of {slices} slices look significant, although nothing changed anywhere.")
    print(f"At p < 0.05, about 1 in 20 comparisons of identical versions looks significant by chance.")
    if hits:
        name, res = hits[0]
        print(f"\nThe after-the-fact story writes itself: \"the new prompt works especially well for "
              f"{name}\"")
        print(f"(p = {fmt_p(res['p'])}). It is noise. The preregistered test was the overall one, and that is")
        print("the only one that counts as evidence. Surprises are leads for the NEXT test, labeled as such.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Null hypothesis, preregistration and p-hacking.")
    ap.add_argument("--slices", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    print_preregistration()
    p_hacking(a.slices, a.seed)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
