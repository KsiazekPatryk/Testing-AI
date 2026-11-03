"""
precision_recall.py: "better" depends on what a mistake costs.

Run:  python precision_recall.py
      python precision_recall.py --threshold 0.4
      python precision_recall.py --tp 40 --fp 10 --fn 20

  precision: when the system says "yes", how often is it right?   (false alarms)
  recall:    of everything it should find, how much did it catch?  (misses)
  F1:        one number, harmonic mean; punishes one high and one low
  F-beta:    choose what matters more; the weight works SQUARED (F2 weighs recall 4x, not 2x)

The bug detector from the post looks at 100 suspicious places in code. Its score turns into
yes/no only at a threshold, and moving the threshold moves the balance without changing the model.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from stats_tools import f_beta, load_jsonl, precision_recall

HERE = Path(__file__).parent
USES = {
    0.5: "false alarms are expensive: automatic PR comments, account locks, fraud accusations",
    1.0: "both kinds of error cost about the same",
    2.0: "a miss is worse than an extra review: privacy leaks, security audits, screening",
}


def header(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def counts(rows: List[Dict], threshold: float) -> Tuple[int, int, int, int]:
    tp = sum(r["is_bug"] and r["score"] >= threshold for r in rows)
    fp = sum((not r["is_bug"]) and r["score"] >= threshold for r in rows)
    fn = sum(r["is_bug"] and r["score"] < threshold for r in rows)
    tn = len(rows) - tp - fp - fn
    return tp, fp, fn, tn


def by_hand(tp: int, fp: int, fn: int, tn: int) -> None:
    header("THE POST'S EXAMPLE, COMPUTED BY HAND")
    pr = precision_recall(tp, fp, fn)
    p, r = pr["precision"], pr["recall"]
    print(f"  {tp} real bugs flagged, {fp} false alarms, {fn} real bugs missed, {tn} clean places left alone")
    print(f"  precision = {tp} / ({tp} + {fp}) = {p:.2f}")
    print(f"  recall    = {tp} / ({tp} + {fn}) = {r:.2f}")
    print(f"  F1        = 2 x {p:.2f} x {r:.2f} / ({p:.2f} + {r:.2f}) = {f_beta(p, r, 1):.2f}")
    print("\n  F1 assumes a false alarm and a miss cost the same. They rarely do:")
    for beta, use in USES.items():
        print(f"    F{beta:g} = {f_beta(p, r, beta):.2f}   recall weighted {beta * beta:g}x   {use}")
    print("\n  The different numbers are not a contradiction. They are product values, written down.")
    print(f"\n  And precision 0.95 with recall 0.30 gives F1 = {f_beta(0.95, 0.30):.2f}, F2 = {f_beta(0.95, 0.30, 2):.2f}:")
    print("  not a good system if missing cases is unacceptable.")


def thresholds(rows: List[Dict], chosen: float) -> None:
    header("THE THRESHOLD MOVES THE BALANCE, THE MODEL STAYS THE SAME")
    print(f"  {'threshold':>9} {'TP':>4} {'FP':>4} {'FN':>4} {'precision':>10} {'recall':>7} {'F0.5':>6} {'F1':>6} {'F2':>6}")
    grid = sorted({round(0.2 + 0.05 * i, 2) for i in range(13)} | {chosen})
    best: Dict[float, Tuple[float, float]] = {}
    for t in grid:
        tp, fp, fn, _ = counts(rows, t)
        pr = precision_recall(tp, fp, fn)
        fs = {b: f_beta(pr["precision"], pr["recall"], b) for b in USES}
        for b, v in fs.items():
            if v > best.get(b, (-1, 0))[0]:
                best[b] = (v, t)
        mark = "  <- chosen" if t == chosen else ""
        print(f"  {t:>9.2f} {tp:>4} {fp:>4} {fn:>4} {pr['precision']:>10.2f} {pr['recall']:>7.2f} "
              f"{fs[0.5]:>6.2f} {fs[1.0]:>6.2f} {fs[2.0]:>6.2f}{mark}")
    print("\n  The best threshold depends on which F you chose:")
    for b, (v, t) in best.items():
        print(f"    F{b:g}: threshold {t:.2f} (F{b:g} = {v:.2f})")
    print("\n  The question is not 'which model has the highest score?' but 'which mistake are we paying for?'")


def rules() -> None:
    header("THREE PRACTICAL RULES")
    print("  1. Choose the F-score BEFORE the evaluation, and write down why that weight fits the product risk.")
    print("  2. Report precision and recall next to the F-score, so one number does not hide the trade-off.")
    print("  3. Remember the threshold. Changing it moves the balance without changing the model.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Precision, recall and F-beta.")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--tp", type=int)
    ap.add_argument("--fp", type=int)
    ap.add_argument("--fn", type=int)
    ap.add_argument("--tn", type=int, default=0)
    a = ap.parse_args()
    rows = load_jsonl(HERE / "data" / "bug_findings.jsonl")
    if a.tp is not None and a.fp is not None and a.fn is not None:
        by_hand(a.tp, a.fp, a.fn, a.tn)
    else:
        by_hand(*counts(rows, a.threshold))
    thresholds(rows, a.threshold)
    rules()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
