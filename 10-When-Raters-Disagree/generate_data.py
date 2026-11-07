"""
generate_data.py: writes the example data in data/ (always the same content).

Run:  python generate_data.py

  reviews.jsonl        100 chatbot answers (FAQ, tone, safety), 3 reviewers, guideline v1 and v2,
                       an expert arbitration label, and what happened later (complaint or not)
  preferences.jsonl    300 users compare a concise and a detailed answer (and a minimal vs explicit patch)
  label_log.jsonl      12 labeling accounts, 200 items each, with timestamps; some accounts share answers
The search result sets, the spoiled-milk case and the ibuprofen pages are hand-written JSON files.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(__file__).parent / "data"
LABELS = ("acceptable", "needs_fix", "risky")


def write_jsonl(name: str, rows) -> None:
    with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def other(label: str, rng: random.Random) -> str:
    return rng.choice([x for x in LABELS if x != label])


def reviews(rng: random.Random):
    """Truth comes from an expert arbitration. Reviewers differ in where and how they miss it.

    ola:   careful, the reference reviewer
    piotr: strict, moves 'acceptable' to 'needs_fix'
    kasia: misses policy details: in safety items she often calls risky answers acceptable
    Guideline v2 splits the vague 'quality' label into tone and safety, with anchor examples.
    """
    plan = ["faq"] * 50 + ["tone"] * 25 + ["safety"] * 25
    truth_mix = {"faq": (0.80, 0.15, 0.05), "tone": (0.50, 0.40, 0.10), "safety": (0.40, 0.20, 0.40)}
    accuracy = {"v1": {"faq": 0.95, "tone": 0.68, "safety": 0.70}, "v2": {"faq": 0.96, "tone": 0.88, "safety": 0.90}}
    score_of = {"acceptable": 8.0, "needs_fix": 5.5, "risky": 2.5}
    rows = []
    for i, cat in enumerate(plan):
        truth = rng.choices(LABELS, truth_mix[cat])[0]
        complaint = rng.random() < {"acceptable": 0.03, "needs_fix": 0.15, "risky": 0.45}[truth]
        for rnd in ("v1", "v2"):
            labels, scores = {}, {}
            for rater in ("ola", "piotr", "kasia"):
                acc = accuracy[rnd][cat]
                lab = truth if rng.random() < acc else other(truth, rng)
                if rater == "piotr" and lab == "acceptable" and rng.random() < 0.25:
                    lab = "needs_fix"
                if rater == "kasia" and cat == "safety" and truth == "risky" and rnd == "v1" and rng.random() < 0.45:
                    lab = "acceptable"
                base = score_of[lab] + rng.gauss(0, 0.8)
                if rater == "piotr":
                    base -= 1.2
                if rater == "kasia":
                    base = 5.5 + (base - 5.5) * 0.35          # sticks to the middle of the scale
                labels[rater] = lab
                score = max(0, min(10, round(base)))
                scores[rater] = None if rng.random() < 0.08 else score   # some ratings are missing
            rows.append({"item": f"out-{i + 1:03d}", "category": cat, "guideline": rnd,
                         "labels": labels, "scores": scores,
                         "expert_label": truth, "later_complaint": complaint})
    return rows


def preferences(rng: random.Random):
    """Two healthy preference groups. Nobody is wrong; the average hides both."""
    rows = []
    for i in range(300):
        group = "wants_short" if rng.random() < 0.55 else "wants_depth"
        concise = 4.5 if group == "wants_short" else 2.6
        detailed = 2.4 if group == "wants_short" else 4.6
        dev = rng.random() < 0.4
        rows.append({"user": f"u{i + 1:03d}", "task": "coding" if dev else "support",
                     "rating_concise": max(1, min(5, round(rng.gauss(concise, 0.6)))),
                     "rating_detailed": max(1, min(5, round(rng.gauss(detailed, 0.6)))),
                     "both_acceptable_to_policy": True})
    return rows


def label_log(rng: random.Random):
    """12 accounts. Four of them (acc-09..acc-12) copy one answer sheet, submitted seconds apart."""
    truth = [rng.choice(["safe", "risky"]) for _ in range(200)]
    start = datetime(2026, 11, 2, 9, 0, 0)
    shared = [rng.choice(["safe", "risky"]) if rng.random() < 0.85 else t for t in truth]   # fast, careless
    rows = []
    for a in range(1, 13):
        acc = f"acc-{a:02d}"
        ring = a >= 9
        t = start + timedelta(minutes=rng.randint(0, 120))
        for i, gold in enumerate(truth):
            if ring:
                t_item = start + timedelta(seconds=i * 9 + rng.randint(0, 4))
                lab = shared[i]
            else:
                t += timedelta(seconds=rng.randint(25, 90))
                t_item = t
                lab = gold if rng.random() < 0.88 else ("risky" if gold == "safe" else "safe")
            rows.append({"account": acc, "item": f"q-{i + 1:03d}", "label": lab, "gold": gold,
                         "submitted_at": t_item.isoformat()})
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    write_jsonl("reviews.jsonl", reviews(random.Random(10)))
    write_jsonl("preferences.jsonl", preferences(random.Random(10)))
    write_jsonl("label_log.jsonl", label_log(random.Random(10)))
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
