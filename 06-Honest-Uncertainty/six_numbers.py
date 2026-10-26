"""
six_numbers.py: six numbers worth having in every report.

Run:  python six_numbers.py

Each number answers a different question about the product:
  mean           how good is the average run?
  median         what is the typical result?
  minimum        how bad can it get?
  failure rate   how often do we cross the line?
  std deviation  how spread out are the results?
  percentiles    what happens to the unlucky users? (P95: 95% were better than this)

Two datasets: answer scores of a support assistant, and how late grocery deliveries were.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean

from stats import group, load_jsonl, percentile, six_numbers

HERE = Path(__file__).parent


def warm_up() -> None:
    print("Warm-up: the examples from the post")
    for label, values in (("8, 9, 7, 8, 8", [8, 9, 7, 8, 8]), ("2, 8, 8, 9, 9", [2, 8, 8, 9, 9]),
                          ("8, 8, 8, 8", [8, 8, 8, 8]), ("10, 10, 4, 8", [10, 10, 4, 8])):
        s = six_numbers(values, [v < 5 for v in values])
        print(f"  {label:14} mean {s['mean']:.1f}  median {s['median']:.1f}  min {s['min']:>2}  "
              f"std dev {s['std_dev']:.1f}")
    print("  Same mean, different products: the spread and the minimum tell them apart.\n")


def scores_report() -> None:
    rows = load_jsonl(HERE / "data" / "scores.jsonl")
    s = six_numbers([r["score"] for r in rows], [r["failed"] for r in rows])
    print("=" * 78)
    print(f"ANSWER SCORES ({s['n']} answers, 0-10, a score below 5 is a failure)")
    print("=" * 78)
    print(f"  mean {s['mean']:.1f} | median {s['median']:.1f} | min {s['min']} | "
          f"failure rate {s['failure_rate']:.0%} | std dev {s['std_dev']:.1f} | P5 {percentile([r['score'] for r in rows], 5):.0f}")
    slices = {k: mean(r["score"] for r in v) for k, v in group(rows, "slice").items()}
    worst = min(slices, key=slices.get)
    print("\n  by slice: " + ", ".join(f"{k} {v:.1f}" for k, v in sorted(slices.items(), key=lambda x: -x[1])))
    print("\n  A weak report:   \"Average quality score: {:.1f}.\"".format(s["mean"]))
    print(f"  A strong report: \"Mean {s['mean']:.1f}, median {s['median']:.1f}, worst score {s['min']}, "
          f"failure rate {s['failure_rate']:.0%},\n                    lowest-scoring slice: {worst} ({slices[worst]:.1f}).\"")
    print("  (For scores, the low tail is what matters, so look at P5 rather than P95.)\n")


def delays_report() -> None:
    rows = load_jsonl(HERE / "data" / "delivery_delays.jsonl")
    values = [r["delay_min"] for r in rows]
    s = six_numbers(values, [v > 30 for v in values])
    print("=" * 78)
    print(f"\"MY GROCERIES ARE LATE AGAIN. IS THAT NORMAL?\"  ({s['n']} deliveries, minutes late)")
    print("=" * 78)
    print(f"  mean    {s['mean']:5.1f} min   the system looks fine")
    print(f"  median  {s['median']:5.1f} min   most customers wait only this long")
    print(f"  P95     {s['p95']:5.1f} min   one customer in twenty waits longer than this")
    print(f"  over 30 minutes late: {s['failure_rate']:.0%} of deliveries, std dev {s['std_dev']:.1f} min")
    print(f"\n  {'neighborhood':18} {'orders':>6} {'mean':>6} {'median':>7} {'P95':>6} {'share of all late minutes':>27}")
    total = sum(values)
    by_hood = group(rows, "neighborhood")
    for hood, items in sorted(by_hood.items(), key=lambda x: -sum(r["delay_min"] for r in x[1])):
        v = [r["delay_min"] for r in items]
        print(f"  {hood:18} {len(v):>6} {mean(v):>6.1f} {percentile(v, 50):>7.1f} {percentile(v, 95):>6.1f} "
              f"{sum(v) / total:>26.0%}")
    print("\n  Different truths. The average makes the system look good.")
    print("  The tail explains why angry customers take screenshots.\n")


def main() -> None:
    warm_up()
    scores_report()
    delays_report()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
