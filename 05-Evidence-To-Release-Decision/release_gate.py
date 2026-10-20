"""
release_gate.py: where numbers become a promise.

Run:  python release_gate.py                                   # candidate v2
      python release_gate.py data/candidate_v3.jsonl
      python release_gate.py data/candidate_v3_quick.jsonl     # only 30 cases
      python release_gate.py data/candidate_v3.jsonl --canary data/canary_v3.jsonl
      python release_gate.py my_results.jsonl --gate my_gate.json

"All tests must pass" is not enough for AI systems: a model can raise the average and
introduce a rare data leak at the same time. This gate (release_gate.json) combines
several kinds of evidence, adds per-slice thresholds, and says what happens after
release. It ends with one of five decisions:

  SHIP · ROLL OUT GRADUALLY · HOLD · ROLL BACK · COLLECT MORE DATA
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

from stats import by_slice, load, mean_ci

HERE = Path(__file__).parent

LABELS = {
    "mean_min": ("mean score", "≥"),
    "ci_lower_min": ("lower bound of the 95% CI", ">"),
    "share_7_or_more_min": ("share of scores 7 or higher", "≥"),
    "policy_failure_rate_max": ("policy failure rate", "<"),
    "min_score_min": ("lowest score", "≥"),
    "critical_failures_max": ("critical safety/privacy failures", "≤"),
    "latency_increase_max": ("latency increase vs baseline", "<"),
}
RATES = {"share_7_or_more_min", "policy_failure_rate_max", "latency_increase_max"}


def measure(rows: List[Dict], baseline: Optional[List[Dict]]) -> Dict[str, float]:
    scores = [r["score"] for r in rows]
    m, lo, _ = mean_ci(scores)
    out = {
        "mean_min": m,
        "ci_lower_min": lo,
        "share_7_or_more_min": sum(s >= 7 for s in scores) / len(scores),
        "policy_failure_rate_max": sum(r["policy_failure"] for r in rows) / len(rows),
        "min_score_min": min(scores),
        "critical_failures_max": sum(bool(r["critical"]) for r in rows),
    }
    if baseline:
        out["latency_increase_max"] = (mean(r["latency_ms"] for r in rows) /
                                       mean(r["latency_ms"] for r in baseline)) - 1
    return out


def passes(key: str, value: float, limit: float) -> bool:
    op = LABELS[key][1]
    return {"≥": value >= limit, ">": value > limit, "<": value < limit, "≤": value <= limit}[op]


def fmt(key: str, value: float) -> str:
    if key in RATES:
        return f"{value:+.1%}" if key == "latency_increase_max" else f"{value:.1%}"
    return f"{value:.0f}" if key in ("min_score_min", "critical_failures_max") else f"{value:.2f}"


def evaluate(gate: Dict, rows: List[Dict], baseline: Optional[List[Dict]]) -> Tuple[str, List[str]]:
    """Returns (decision, reasons). Also prints the full check."""
    values = measure(rows, baseline)
    failed: List[str] = []
    print(f"{'condition':38} {'limit':>8} {'value':>8}  result   protects against")
    print("─" * 100)
    for key, cond in gate["conditions"].items():
        if key not in values:
            continue
        ok = passes(key, values[key], cond["value"])
        if not ok:
            failed.append(key)
        label, op = LABELS[key]
        print(f"{label:38} {op + ' ' + fmt(key, cond['value']):>8} {fmt(key, values[key]):>8}  "
              f"{'PASS' if ok else 'FAIL':6}   {cond['protects_against']}")

    slices = by_slice(rows)
    base_slices = by_slice(baseline) if baseline else {}
    slice_failed: List[str] = []
    print(f"\n{'slice':20} {'n':>4} {'mean':>6} {'95% CI':>12} {'min':>4} {'baseline':>9}  own threshold")
    print("─" * 100)
    for name, group in sorted(slices.items()):
        scores = [r["score"] for r in group]
        m, lo, hi = mean_ci(scores)
        base = f"{mean(r['score'] for r in base_slices[name]):.1f}" if name in base_slices else "—"
        rule = gate.get("slice_thresholds", {}).get(name)
        verdict = ""
        if rule:
            problems = []
            if "mean_min" in rule and m < rule["mean_min"]:
                problems.append(f"mean < {rule['mean_min']}")
            if "min_score_min" in rule and min(scores) < rule["min_score_min"]:
                problems.append(f"a score below {rule['min_score_min']}")
            verdict = ("FAIL: " + ", ".join(problems)) if problems else "PASS"
            if problems:
                slice_failed.append(name)
        worse = " (worse than baseline)" if name in base_slices and m < float(base) - 0.3 else ""
        ci = f"{lo:>5.1f}–{hi:<5.1f}" if len(group) > 1 else f"{'n/a':^11}"
        print(f"{name:20} {len(group):>4} {m:>6.1f} {ci} {min(scores):>4} {base:>9}  {verdict}{worse}")

    if baseline:
        bm = mean(r["score"] for r in baseline)
        worst_now, worst_before = min(r["score"] for r in rows), min(r["score"] for r in baseline)
        if values["mean_min"] > bm and worst_now < worst_before:
            print(f"\n! The mean went up ({bm:.2f} -> {values['mean_min']:.2f}), but the worst case got worse "
                  f"({worst_before} -> {worst_now}). Slow down.")

    reasons: List[str] = []
    if len(rows) < gate.get("min_cases", 0):
        reasons.append(f"only {len(rows)} cases, the gate needs at least {gate['min_cases']}")
        return "COLLECT MORE DATA", reasons
    if "critical_failures_max" in failed:
        reasons.append(f"{values['critical_failures_max']:.0f} critical failure(s): a hard block")
        return "HOLD", reasons + [LABELS[k][0] for k in failed if k != "critical_failures_max"] + \
            [f"slice {s}" for s in slice_failed]
    if failed == ["ci_lower_min"] and not slice_failed:
        reasons.append("the mean passes, but the interval is too wide to be sure")
        return "COLLECT MORE DATA", reasons
    if failed or slice_failed:
        return "HOLD", [LABELS[k][0] for k in failed] + [f"slice {s}" for s in slice_failed]
    after = gate.get("after_release", {})
    if after.get("canary"):
        return "ROLL OUT GRADUALLY", [f"all conditions pass; canary: {after['canary']}"]
    return "SHIP", ["all conditions pass"]


def check_canary(gate: Dict, released: List[Dict], canary: List[Dict]) -> Tuple[str, List[str]]:
    triggers = gate["after_release"]["rollback_triggers"]
    reasons: List[str] = []
    before, after = by_slice(released), by_slice(canary)
    print(f"{'slice':20} {'before':>7} {'canary':>7} {'drop':>6}")
    print("─" * 44)
    for name, group in sorted(after.items()):
        if name not in before:
            continue
        b = mean(r["score"] for r in before[name])
        a = mean(r["score"] for r in group)
        drop = b - a
        flag = "  <- rollback trigger" if drop > triggers["slice_mean_drop_max"] else ""
        print(f"{name:20} {b:>7.2f} {a:>7.2f} {drop:>6.2f}{flag}")
        if flag:
            reasons.append(f"{name} dropped by {drop:.1f} points (limit {triggers['slice_mean_drop_max']})")
    crit = sum(bool(r["critical"]) for r in canary)
    if crit > triggers["critical_failures_max"]:
        reasons.append(f"{crit} critical failure(s) in production")
    rate = sum(r["policy_failure"] for r in canary) / len(canary)
    if rate > triggers["policy_failure_rate_max"]:
        reasons.append(f"policy failure rate {rate:.1%}")
    print(f"\ncritical failures: {crit}   policy failure rate: {rate:.1%}")
    return ("ROLL BACK", reasons) if reasons else ("SHIP", ["the canary stayed within every trigger"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate results against a release gate.")
    ap.add_argument("results", nargs="?", default=str(HERE / "data" / "candidate_v2.jsonl"))
    ap.add_argument("--gate", default=str(HERE / "release_gate.json"))
    ap.add_argument("--canary", help="production sample collected during the canary")
    a = ap.parse_args()

    gate = json.loads(Path(a.gate).read_text(encoding="utf-8"))
    base_path = gate.get("baseline")
    baseline = load(Path(a.gate).parent / base_path) if base_path else None
    rows = load(Path(a.results))

    print(f"Change:   {gate['change']}")
    print(f"Evidence: {Path(a.results).name} ({len(rows)} cases)"
          + (f", baseline {Path(base_path).name}" if base_path else "") + "\n")
    decision, reasons = evaluate(gate, rows, baseline)

    if a.canary and decision == "ROLL OUT GRADUALLY":
        print(f"\n{'=' * 78}\nAFTER RELEASE: the canary ({gate['after_release']['canary']})\n{'=' * 78}")
        decision, reasons = check_canary(gate, rows, load(Path(a.canary)))
    elif a.canary:
        print("\n(--canary ignored: the change never passed the gate, so there is no canary.)")

    print(f"\n{'=' * 78}\nDECISION: {decision}")
    for r in reasons:
        print(f"  - {r}")
    if decision == "ROLL OUT GRADUALLY":
        after = gate["after_release"]
        print(f"  - then: {after['production_sampling']}; roll back if any trigger fires: "
              f"{json.dumps(after['rollback_triggers'])}")
        print("  - a green light on release day is only the beginning: non-deterministic systems drift.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
