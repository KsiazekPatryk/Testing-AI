"""
two_significances.py: statistical significance vs practical significance.

Run:  python two_significances.py

  statistical significance: is the difference probably bigger than random noise?
  practical significance:   does the difference matter to users, the business, or the risk profile?

Three examples from the post, each judged against minimum_effect.json, which was written
BEFORE the results:
  1. significant but not important: 8.10 -> 8.12 on a huge sample, with more latency and cost
  2. important but not (yet) significant: policy failures 6% -> 2% on a small sample
  3. a tiny global change, a big change in one slice: search ranking and the child passport query
"""

from __future__ import annotations

import sys
from pathlib import Path

from stats_tools import fisher_exact, load_json, p_str, pp, two_means, two_proportions

HERE = Path(__file__).parent


def header(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def verdict(statistical: bool, practical: bool) -> str:
    return {(True, True): "significant AND important",
            (True, False): "significant, NOT important",
            (False, True): "possibly important, NOT significant: needs more data",
            (False, False): "neither"}[(statistical, practical)]


def main() -> None:
    mde = load_json(HERE / "minimum_effect.json")
    cases = load_json(HERE / "data" / "significance_cases.json")
    print("Minimum meaningful effect, written on " + mde["written_at"] + " (before the results):")
    for k, v in mde["minimum_meaningful_effect"].items():
        print(f"  {k}: {v}")

    a = cases["assistant_score"]
    r = two_means(a["n_per_version"], a["old_mean"], a["sd"], a["n_per_version"], a["new_mean"], a["sd"])
    header("1. SIGNIFICANT, BUT DOES IT MATTER? " + a["description"])
    print(f"  {a['old_mean']:.2f} -> {a['new_mean']:.2f} on {a['n_per_version']:,} conversations per version")
    print(f"  difference {r['diff']:+.2f}, 95% CI {r['ci_low']:+.3f} to {r['ci_high']:+.3f}, {p_str(r['p'])}")
    lat, cost = a["guardrails"]["p95_latency_ms"], a["guardrails"]["cost_per_1000_conversations_usd"]
    print(f"  p95 latency {lat[0]} -> {lat[1]} ms ({lat[1] / lat[0] - 1:+.0%}), "
          f"cost per 1000 conversations ${cost[0]:.2f} -> ${cost[1]:.2f} ({cost[1] / cost[0] - 1:+.0%})")
    print(f"  The whole interval is below the +0.3 that matters, and both guardrails (+10%) are broken.")
    print(f"  -> {verdict(r['p'] < 0.05, r['ci_high'] >= 0.3)}. A team can reasonably decide not to ship it.")

    f = cases["policy_failures"]
    n = f["n_per_version"]
    res = two_proportions(f["old_failures"], n, f["new_failures"], n)
    p_exact = fisher_exact(f["old_failures"], n - f["old_failures"], f["new_failures"], n - f["new_failures"])
    header("2. IMPORTANT, BUT NOISY. " + f["description"])
    print(f"  {f['old_failures']}/{n} -> {f['new_failures']}/{n}: {res['p1']:.0%} -> {res['p2']:.0%}, "
          f"a {1 - res['p2'] / res['p1']:.0%} relative drop")
    print(f"  difference {pp(res['diff'])}, 95% CI {pp(res['ci_low'])} to {pp(res['ci_high'])}, "
          f"Fisher's exact {p_str(p_exact)}")
    print("  The point estimate is far beyond the '20% fewer failures' that matters, but the interval")
    print("  also includes 'slightly worse'. Not 'no effect': not enough data to tell.")
    print(f"  -> {verdict(p_exact < 0.05, True)}. See power_analysis.py for how many cases it needs.")

    s = cases["search_ranking"]
    r = two_means(s["n_per_version"], s["old_mean"], s["sd"], s["n_per_version"], s["new_mean"], s["sd"])
    sl = s["slice"]
    header("3. A SLICE CAN MATTER MORE THAN THE AVERAGE. " + s["description"])
    print(f"  all queries: {s['old_mean']:.2f} -> {s['new_mean']:.2f} relevance on {s['n_per_version']:,} queries, "
          f"{p_str(r['p'])}. Invisible to users.")
    off = two_proportions(sl["official_source_in_top_3"][0], sl["queries"], sl["official_source_in_top_3"][1], sl["queries"])
    scam = two_proportions(sl["scam_page_in_top_3"][0], sl["queries"], sl["scam_page_in_top_3"][1], sl["queries"])
    print(f"  slice \"{sl['name']}\" ({sl['queries']} queries):")
    print(f"    official source in the top 3: {off['p1']:.0%} -> {off['p2']:.0%}")
    print(f"    scam page in the top 3:       {scam['p1']:.0%} -> {scam['p2']:.0%}")
    print("  Large practical value, while the global number barely moved. The reverse also happens:")
    print("  the average goes up while this slice gets worse. Then the release is a bad trade.")

    header("THE TAKEAWAY")
    print("  Define the minimum meaningful effect BEFORE the test. Then a result is judged twice:")
    print("    is it bigger than the noise?  (statistics)")
    print("    is it bigger than what matters, without breaking a guardrail or a high-risk slice?  (product)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
