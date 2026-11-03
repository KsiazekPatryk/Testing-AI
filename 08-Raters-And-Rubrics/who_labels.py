"""
who_labels.py: whoever labels the data defines what "quality" means.

Run:  python who_labels.py
      python who_labels.py --domain construction

60 queries in 5 domains, two answers each:
  polished_popular  a glossy blog or review site
  expert_grounded   clinical guidelines with caveats, field details, the actual law
Each answer is scored by a generalist rater, by a domain expert, and by an LLM judge that was
tuned on the generalist labels.

The script shows:
  1. which answer "wins" depends on who scores it, and in which domain
  2. flat pay per query: the same few people decide the medical queries
  3. the LLM judge copies the generalists, with more confidence and less visible disagreement
  4. tiered labeling: who should label what
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

from agreement import load_jsonl, mean

HERE = Path(__file__).parent
DOMAINS = ("general", "medical", "construction", "legal", "coding")


def preference(rows: List[Dict], who: str) -> float:
    """Mean score of expert_grounded minus polished_popular. Positive = prefers grounded answers."""
    g = [r[who] for r in rows if r["answer_style"] == "expert_grounded"]
    p = [r[who] for r in rows if r["answer_style"] == "polished_popular"]
    return mean(g) - mean(p)


def winner(x: float) -> str:
    return "grounded" if x > 0.5 else "polished" if x < -0.5 else "tie"


def by_domain(rows: List[Dict]) -> None:
    print("=" * 78 + "\nWHICH ANSWER WINS? DEPENDS ON WHO SCORES IT\n" + "=" * 78)
    print("  grounded - polished, mean score (positive: the grounded answer wins)\n")
    print(f"  {'domain':13} {'generalist':>14} {'expert':>14} {'LLM judge':>14}")
    for d in DOMAINS:
        sub = [r for r in rows if r["domain"] == d]
        cells = [preference(sub, w) for w in ("generalist_score", "expert_score", "llm_judge_score")]
        print(f"  {d:13} " + " ".join(f"{c:+5.1f} {winner(c):>8}" for c in cells))
    print("\n  In 'general', everyone agrees. Where expertise matters, the generalist and the expert")
    print("  pick opposite answers. Each is right on their own dimension, but only one matches the decision.")


def example(rows: List[Dict], domain: str) -> None:
    sub = [r for r in rows if r["domain"] == domain]
    q = sub[0]["query"]
    print("\n" + "=" * 78 + f"\nONE QUERY: \"{q}\"\n" + "=" * 78)
    for r in (x for x in sub if x["query"] == q and x["variant"] == 1):
        print(f"  {r['answer_style']:17} generalist {r['generalist_score']:2}   expert {r['expert_score']:2}   "
              f"LLM judge {r['llm_judge_score']:2}")
    notes = {
        "medical": "A physiotherapist prefers clinical guidelines with caveats; a safety reviewer punishes anything that sounds like a diagnosis.",
        "construction": "A roofer looks at grip, heat, ankle support, and whether the boot survives hot tar.",
        "legal": "A lawyer checks whether the answer matches the actual rule and says when to get advice.",
        "coding": "A senior engineer checks whether the fix keeps the security boundary, not whether the diff is short.",
        "general": "Here a generalist is the right instrument.",
    }
    print(f"  {notes[domain]}")


def workload(rows: List[Dict]) -> None:
    print("\n" + "=" * 78 + "\nFLAT PAY PER QUERY: WHO ACTUALLY DECIDED THE MEDICAL LABELS?\n" + "=" * 78)
    med = Counter(r["generalist_id"] for r in rows if r["domain"] == "medical")
    total = sum(med.values())
    top = med.most_common(4)
    share = sum(c for _, c in top) / total
    print(f"  {total} medical labels, {len(med)} different people.")
    print("  " + ", ".join(f"{who}: {c}" for who, c in top) + f"  -> {share:.0%} from four people")
    print("  The fastest raters take the most queries, including the ones they are least qualified for.")
    print("  The product ends up tuned to their idea of relevance.")


def judge(rows: List[Dict]) -> None:
    print("\n" + "=" * 78 + "\nTHE LLM JUDGE INHERITS THE BLIND SPOT\n" + "=" * 78)
    hi = [r for r in rows if r["domain"] in ("medical", "construction", "legal")]
    agree_gen = mean([abs(r["llm_judge_score"] - r["generalist_score"]) <= 1 for r in hi])
    agree_exp = mean([abs(r["llm_judge_score"] - r["expert_score"]) <= 1 for r in hi])
    conf = mean([r["llm_judge_confidence"] for r in hi])
    print(f"  Expert domains, {len(hi)} answers. The judge is within 1 point of:")
    print(f"    the generalist: {agree_gen:.0%}    the expert: {agree_exp:.0%}")
    print(f"  Its average confidence: {conf:.2f}. Its labels have no visible disagreement at all:")
    print("  one confident score per answer, instead of three people who argue.")
    print("  Cheap labels became expensive errors: scaled, confident, and wrong in the same direction.")


def tiers() -> None:
    print("\n" + "=" * 78 + "\nTIERED LABELING\n" + "=" * 78)
    rows = [
        ("obvious, low risk", "one trained generalist"),
        ("ambiguous", "three raters with overlap, arbitration rules decided up front"),
        ("high risk, or defines a release gate", "a domain expert"),
        ("large scale", "an LLM judge, only after it agrees with experts on a calibration set"),
    ]
    for case, who in rows:
        print(f"  {case:38} -> {who}")
    print("\n  The key question is not 'how do we get labels cheaply?'")
    print("  but 'what product behavior will these labels reward?'")


def main() -> None:
    ap = argparse.ArgumentParser(description="Whoever labels the data defines quality.")
    ap.add_argument("--domain", choices=DOMAINS, default="medical", help="domain for the single example")
    a = ap.parse_args()
    rows = load_jsonl(HERE / "data" / "relevance_labels.jsonl")
    by_domain(rows)
    example(rows, a.domain)
    workload(rows)
    judge(rows)
    tiers()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
