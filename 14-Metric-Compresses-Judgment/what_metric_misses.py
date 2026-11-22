"""
what_metric_misses.py: what the number leaves out, and what else could explain it.

Run:  python what_metric_misses.py

Part A, the lesson from Zillow Offers. Zillow used models to buy, value, renovate and resell homes.
In 2021 it announced it was closing that business, pointing to too much volatility and unpredictable
results. Model accuracy is not the product's result: market moves, renovation costs, liquidity and
correlated errors matter too. The data here is simulated, not Zillow's: two valuation models with the
SAME accuracy (4.0% mean absolute error), run as a home-flipping business over 8 quarters while the
market turns.

Part B, a metric needs a measurement model, not just a chart. "Satisfaction" measured as time spent
on the results page before a click. The chart has a spike at the end of the scale, because every long
time above an arbitrary cap went into one bucket. And a long time has obvious other causes: a slow
page, a switched tab, an email answered in between.

  1. same accuracy, different business: average profit, worst quarter, losing homes
  2. how fast can you stop? the same model, stopped after one bad quarter or after two
  3. the dwell-time chart and its spike at "60+"
  4. what else could explain a long dwell time?
  5. ask a model to attack your metric (a prompt you can paste)
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from metrickit import load_jsonl, mean

HERE = Path(__file__).parent
MARGIN = 0.90          # the business offers 90% of the model's resale estimate
RENOVATION = 0.04      # planned renovation cost, share of the home's value
HOLDING = 0.006        # holding cost per month on the market (interest, taxes, upkeep)
SATISFIED_S = 20       # the dashboard's definition: 20 s or more on the page = satisfied


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def profit(home: Dict, model: str) -> float:
    v = home["resale_value"]
    paid = v * (1 + home[f"err_{model}"]) * MARGIN
    renovation = v * RENOVATION * (1 + home["renovation_overrun"])
    holding = v * HOLDING * home["months_to_sell"]
    return v - paid - renovation - holding


def by_quarter(homes: List[Dict], model: str) -> Dict[int, float]:
    out = defaultdict(float)
    for h in homes:
        out[h["quarter"]] += profit(h, model)
    return dict(sorted(out.items()))


def part_a(homes: List[Dict]) -> None:
    header("1. SAME ACCURACY, DIFFERENT BUSINESS")
    print(f"  {len(homes)} homes over 8 quarters. Market move per quarter: "
          + " ".join(f"{m:+.0%}" for m in sorted({(h['quarter'], h['market_move']) for h in homes})
                     for m in [m[1]]))
    print(f"\n  {'model':12} {'MAPE':>6} {'total profit':>14} {'worst quarter':>15} {'losing homes':>13} {'worst 5% of homes':>18}")
    for model in ("independent", "momentum"):
        mape = mean([abs(h[f"err_{model}"]) for h in homes])
        q = by_quarter(homes, model)
        ps = sorted(profit(h, model) for h in homes)
        tail = mean(ps[: len(ps) // 20])
        print(f"  {model:12} {mape:6.1%} {sum(q.values()) / 1e6:12.2f} M {min(q.values()) / 1e6:13.2f} M"
              f" {sum(p < 0 for p in ps):>8}/{len(ps)} {tail / 1e3:15.1f} k")
    print("\n  profit per quarter (M):  " + " ".join(f"{'Q' + str(k):>6}" for k in range(1, 9)))
    for model in ("independent", "momentum"):
        print(f"  {model:24} " + " ".join(f"{v / 1e6:6.2f}" for v in by_quarter(homes, model).values()))
    print("\n  Identical accuracy on the model's own metric. The momentum model's errors move together:")
    print("  when the market turns it overvalues every home at once, and the losses arrive in one place.")
    print("  Accuracy did not see renovation overruns, slower sales in a falling market, or correlation.")

    header("2. HOW FAST CAN YOU STOP?")
    q = by_quarter(homes, "momentum")
    first_bad = next(k for k, v in q.items() if v < 0)
    print(f"  momentum model: first losing quarter is Q{first_bad}. Homes keep being bought until someone stops it.")
    for lag in (1, 2, 3):
        last = first_bad + lag - 1
        kept = sum(v for k, v in q.items() if k <= last)
        print(f"    buying stops {lag} quarter(s) after the first loss (last purchases in Q{last}): total {kept / 1e6:6.2f} M")
    print("  The same model ends in profit or in a loss depending on how fast the business can stop.")
    print("  That speed is a property of the product, and no accuracy metric reports it.")


def part_b(sessions: List[Dict]) -> None:
    header("3. THE DWELL-TIME CHART: A SPIKE AT THE END OF THE SCALE")
    buckets = Counter()
    for s in sessions:
        d = s["dwell_logged"]
        buckets["60+" if d == "60+" else f"{(d // 10) * 10:>2}-{(d // 10) * 10 + 9}"] += 1
    for k in sorted(buckets, key=lambda b: (b == "60+", b)):
        print(f"  {k:>6} s  {buckets[k]:5}  {'#' * (buckets[k] // 12)}")
    print("  The last bar is not a peak of happy users. It is everything at or above an arbitrary 60 s")
    print("  cap, from one minute to fifteen, poured into one bucket.")

    header("4. WHAT ELSE COULD EXPLAIN A LONG DWELL TIME?")
    long_ = [s for s in sessions if s["dwell_s_true"] >= SATISFIED_S]
    causes = Counter(s["true_cause"] for s in long_)
    print(f"  The dashboard counts {len(long_)} of {len(sessions)} sessions ({len(long_) / len(sessions):.0%}) as 'satisfied' (>= {SATISFIED_S} s).")
    print("  This simulated data also holds the true reason, which production never gives you")
    print("  (a diary study or a small observed sample can give it for a sample):")
    for c, n in causes.most_common():
        print(f"    {c:22} {n:5}  {n / len(long_):5.0%}")
    cleaned = [s for s in long_ if s["page_load_ms"] < 3000 and s["tab_hidden_ms"] < 5000]
    still_wrong = sum(s["true_cause"] != "read_and_satisfied" for s in cleaned)
    print(f"\n  Instrumenting the obvious alternatives (page load >= 3 s, tab hidden >= 5 s) removes "
          f"{len(long_) - len(cleaned)} sessions.")
    print(f"  Of the {len(cleaned)} left, {still_wrong} are still not satisfaction (an email in another window"
          " leaves no trace).")
    print("  Before trusting the number, ask what else could explain it, and measure the alternatives")
    print("  you can. The rest belongs in the report as a known limit of the metric.")

    header("5. ASK A MODEL TO ATTACK YOUR METRIC")
    print("  Paste this into any LLM together with your metric's definition and one chart:\n")
    print("    You are a skeptical reviewer. Here is a metric we use to decide releases: <definition>.")
    print("    1. List the ways this number could go up while users are worse off.")
    print("    2. List the alternative explanations for the pattern in this chart.")
    print("    3. Which failures does the metric not see at all?")
    print("    4. What single piece of evidence would most undermine our conclusion?")
    print("\n  Treat the answer as a list of hypotheses to check, not as findings.")


def main() -> None:
    part_a(load_jsonl(HERE / "data" / "home_flips.jsonl"))
    part_b(load_jsonl(HERE / "data" / "dwell_times.jsonl"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
