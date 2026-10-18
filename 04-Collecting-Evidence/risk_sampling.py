"""
risk_sampling.py: test where failure hurts the most.

Run:  python risk_sampling.py
      python risk_sampling.py --budget 2000 --true-failure-rate 0.005
      python risk_sampling.py my_features.json

Equal sampling feels fair: the same number of cases for every feature. But users
experience consequences, not the symmetry of a test plan. This script:
  1. scores each feature on five risk dimensions (features.json),
  2. splits a fixed test budget by risk instead of evenly (with a floor, so nothing is ignored),
  3. shows what each sample size can and cannot tell you about rare failures,
  4. over-represents hard slices inside a feature (blurry photos, not just clear ones),
  5. flags high-authority actions that depend on a single signal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

HERE = Path(__file__).parent
DIMENSIONS = ("detectability", "irreversibility", "regulatory")


def risk_score(f: Dict) -> float:
    """Impact x likelihood x the average of the other three dimensions (1 to 125)."""
    return f["impact"] * f["likelihood"] * mean(f[d] for d in DIMENSIONS)


def allocate(weights: List[float], budget: int, floor: int) -> List[int]:
    """Split a budget in proportion to weights. Every item gets at least `floor`.
    Uses the largest remainder method, so the parts always add up to the budget."""
    n = len(weights)
    if floor * n > budget:
        raise ValueError("budget too small for the minimum per feature")
    rest = budget - floor * n
    total = sum(weights)
    raw = [rest * w / total for w in weights]
    parts = [int(r) for r in raw]
    order = sorted(range(n), key=lambda i: raw[i] - parts[i], reverse=True)
    for i in order[: rest - sum(parts)]:
        parts[i] += 1
    return [p + floor for p in parts]


def chance_to_see(n: int, rate: float) -> float:
    """Probability of seeing at least one failure in n samples, if the true rate is `rate`."""
    return 1 - (1 - rate) ** n


def rule_of_three(n: int) -> float:
    """Zero failures in n samples: the true rate could still be up to about 3/n (95%)."""
    return 3 / n


def main() -> None:
    ap = argparse.ArgumentParser(description="Risk-based test sampling.")
    ap.add_argument("file", nargs="?", default=str(HERE / "features.json"))
    ap.add_argument("--budget", type=int)
    ap.add_argument("--true-failure-rate", type=float, default=0.01)
    a = ap.parse_args()

    spec = json.loads(Path(a.file).read_text(encoding="utf-8"))
    features = spec["features"]
    budget = a.budget or spec.get("budget", 600)
    floor = spec.get("min_per_feature", 20)
    rate = a.true_failure_rate
    pct = f"{rate * 100:g}%"

    scores = [risk_score(f) for f in features]
    uniform = allocate([1] * len(features), budget, 0)
    risk_based = allocate(scores, budget, floor)

    print(f"Test budget: {budget} samples across {len(features)} features "
          f"(at least {floor} each in the risk-based plan).")
    print(f"'see {pct}' = chance of seeing at least one failure if {pct} of answers fail.\n")
    see = f"see {pct}"
    header = f"{'feature':32} {'risk':>5} │ {'even':>5} {see:>8} │ {'risk':>5} {see:>8} {'0 fails ⇒ rate ≤':>17}"
    print(header)
    print("─" * len(header))
    order = sorted(range(len(features)), key=lambda i: -scores[i])
    for i in order:
        f = features[i]
        print(f"{f['name'][:32]:32} {scores[i]:>5.0f} │ {uniform[i]:>5} {chance_to_see(uniform[i], rate):>8.0%} │ "
              f"{risk_based[i]:>5} {chance_to_see(risk_based[i], rate):>8.0%} {rule_of_three(risk_based[i]):>17.1%}")

    print("\nHow to read it:")
    print("  - 'risk' sends samples where failures are worst, least visible and hardest to undo.")
    print("  - Low-risk features still get a floor, so they are not ignored, just not over-tested.")
    print("  - Zero failures is not zero risk: with n samples the true rate can still be up to ~3/n.")

    for i, f in enumerate(features):
        if "slices" not in f:
            continue
        names = list(f["slices"])
        weights = [s["traffic_share"] * s["difficulty"] for s in f["slices"].values()]
        parts = allocate(weights, risk_based[i], 0)
        print(f"\nHard slices inside '{f['name']}' ({risk_based[i]} samples):")
        for name, part in zip(names, parts):
            s = f["slices"][name]
            print(f"  {name:40} traffic {s['traffic_share']:>4.0%}  →  samples {part:>4} ({part / risk_based[i]:.0%})")
        print("  The hard slice is a small share of traffic, but it gets far more of the testing.")

    risky = [f["name"].split(" (")[0] for i, f in sorted(enumerate(features), key=lambda x: -scores[x[0]])
             if f["irreversibility"] >= 4][:2]
    if risky:
        print(f"\nOne sentence for the report:\n  \"We used more samples for {' and '.join(risky).lower()}, "
              "because failures there are less reversible.\"")

    weak = [f for f in features if f.get("autonomous_action") and f.get("independent_signals", 1) < 2]
    if weak:
        print("\nAuthority check (the Boeing 737 MAX lesson: too much authority for too narrow a signal):")
        for f in weak:
            print(f"  ! {f['name']}: acts on its own based on {f.get('independent_signals', 1)} signal. "
                  "Require a second, independent check before it acts,")
            print("    and test what happens when the judge is confident but wrong, or when retrieval")
            print("    returns a plausible but outdated document.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
