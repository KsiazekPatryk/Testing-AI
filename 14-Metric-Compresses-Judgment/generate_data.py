"""
generate_data.py: writes the generated example data in data/ (always the same content).

Run:  python generate_data.py

  home_flips.jsonl     320 homes bought and resold over 8 quarters, valued by two models with the
                       same accuracy: one with independent errors, one whose errors move together
  dwell_times.jsonl    2,000 search sessions: time on the results page before a click, what the
                       logger records (capped at 60 s), page load time, hidden-tab time, and the true
                       reason for the long wait (known here, never known in production)
  quality_history.json evaluation pass rates per release for your team and for the market leader
  style_ratings.jsonl  absolute 1-10 style ratings from one long rating session, in rating order
  style_pairs.jsonl    pairwise preferences ("which one fits the reader better?") from the same rater
  style_slices.jsonl   style ratings and editing time for outputs from the demo set and from wider slices
The metric spec, the candidates, the allergy case, the style rubric, the peer group, the exam
questions and the exercise are hand-written JSON files.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"

MARKET = [0.02, 0.02, 0.03, 0.03, 0.00, -0.06, -0.08, -0.04]   # quarterly price moves: the market turns


def home_flips(rng: random.Random):
    """Two valuation models, same mean absolute error (4.0%), different error structure.

    independent  each home's error is its own: some too high, some too low
    momentum     the model extrapolates the last quarter's trend: while the market rises it is as
                 good as the other one, and when the market turns it overvalues EVERY home at once.
                 The errors are correlated
    """
    rows = []
    for q, move in enumerate(MARKET):
        prev = MARKET[q - 1] if q else move
        for h in range(40):
            value = round(rng.uniform(250_000, 450_000), -3)
            rows.append({"quarter": q + 1, "home": f"H{q + 1}-{h + 1:02d}", "resale_value": value,
                         "market_move": move,
                         "err_independent": rng.gauss(0, 1),
                         "err_momentum": 3.0 * max(0.0, prev - move) / 0.04 + rng.gauss(0, 0.35),
                         "renovation_overrun": max(0.0, rng.gauss(0.10, 0.15)),
                         "months_to_sell": max(1, round(rng.gauss(3 + max(0, -move) * 60, 1)))})
    for key in ("err_independent", "err_momentum"):            # scale both to the same 4.0% MAPE
        scale = 0.04 / (sum(abs(r[key]) for r in rows) / len(rows))
        for r in rows:
            r[key] = round(r[key] * scale, 5)
    return rows


def dwell_times(rng: random.Random):
    causes = (["read_and_satisfied"] * 55 + ["quick_bounce"] * 20 + ["slow_page"] * 10
              + ["switched_tab"] * 10 + ["answered_email"] * 5)
    rows = []
    for i in range(2000):
        cause = rng.choice(causes)
        load_ms = int(rng.uniform(300, 1200))
        hidden_ms = 0
        if cause == "read_and_satisfied":
            dwell = rng.lognormvariate(math.log(28), 0.45)
        elif cause == "quick_bounce":
            dwell = rng.uniform(2, 9)
        elif cause == "slow_page":
            load_ms = int(rng.uniform(4000, 15000))
            dwell = load_ms / 1000 + rng.uniform(5, 30)
        elif cause == "switched_tab":
            hidden_ms = int(rng.uniform(40, 600) * 1000)
            dwell = hidden_ms / 1000 + rng.uniform(3, 20)
        else:
            hidden_ms = int(rng.uniform(90, 900) * 1000) if rng.random() < 0.5 else 0  # email in another window
            dwell = rng.uniform(90, 900)
        rows.append({"session": f"s-{i + 1:04d}", "dwell_s_true": round(dwell, 1),
                     "dwell_logged": "60+" if dwell >= 60 else int(dwell),
                     "page_load_ms": load_ms, "tab_hidden_ms": hidden_ms, "true_cause": cause})
    return rows


def quality_history():
    """Pass rates on a fixed evaluation set (n cases per release). Both follow a saturating curve
    q(t) = cap - (cap - q0) * exp(-k t); you see the early, almost linear part, the leader sees the flat part."""
    def curve(cap, q0, k, start, n):
        return [round(cap - (cap - q0) * math.exp(-k * (start + t)), 4) for t in range(n)]
    effort = [2, 2, 3, 3, 4, 5, 7, 9, 12, 16, 21, 28]
    n = 400
    out = {"n_cases": n, "acceptable_failure_upper_bound": 0.12,
            "yours": {"releases": [f"r{i + 1}" for i in range(8)], "true_rate": curve(0.93, 0.55, 0.16, 0, 8)},
            "leader": {"releases": [f"r{i + 1}" for i in range(12)], "true_rate": curve(0.93, 0.55, 0.16, 12, 12),
                       "person_weeks": effort},
            "segments_last_release": {
                "returns": [0.81, 0.90], "shipping": [0.88, 0.85], "billing": [0.86, 0.82],
                "account": [0.90, 0.90], "product_questions": [0.84, 0.85]},
            "segment_cases": 150}
    for who, seed in (("yours", 36), ("leader", 14)):          # measured: binomial noise around the true rate
        r = random.Random(seed)
        out[who]["passed"] = [sum(r.random() < p for _ in range(n)) for p in out[who]["true_rate"]]
    return out


def style_ratings(rng: random.Random):
    """One rater, 60 outputs in a long session. The outputs are equally good on average, but the
    rater's absolute scale drifts down as the session goes on. Pairwise preferences do not drift."""
    rows = []
    for i in range(60):
        quality = rng.gauss(7.0, 1.0)
        drift = -2.0 * i / 59                                  # tired, stricter, anchored on the last item
        rows.append({"order": i + 1, "output": f"o-{i + 1:02d}", "latent_quality": round(quality, 2),
                     "absolute_score": max(1, min(10, round(quality + drift + rng.gauss(0, 0.6))))})
    pairs = []
    for i in range(40):
        a, b = rng.sample(rows, 2)
        diff = a["latent_quality"] - b["latent_quality"]
        p_a = 1 / (1 + math.exp(-2.5 * diff))
        pairs.append({"order": i + 1, "a": a["output"], "b": b["output"],
                      "preferred": a["output"] if rng.random() < p_a else b["output"],
                      "better_by_latent": a["output"] if diff > 0 else b["output"]})
    return rows, pairs


def style_slices(rng: random.Random):
    """Style rating (1-10, median of two raters) and the minutes a person needed to make the output
    ready to send, per slice. The demo slice is what the team shows in meetings."""
    spec = {"demo (short, English)": (8.6, 0.6, 2, 2),
            "long documents (10+ pages)": (6.1, 1.1, 18, 8),
            "Polish": (6.6, 1.0, 12, 6),
            "dense data (tables, numbers)": (5.4, 1.2, 22, 9),
            "health topics": (6.9, 0.9, 14, 6)}
    rows = []
    for name, (mu, sd, edit_mu, edit_sd) in spec.items():
        for i in range(40):
            rows.append({"slice": name, "item": f"{name[:4]}-{i + 1:02d}",
                         "style_score": max(1, min(10, round(rng.gauss(mu, sd)))),
                         "edit_minutes": max(0, round(rng.gauss(edit_mu, edit_sd))),
                         "manual_minutes": 35, "needed_full_rewrite": rng.random() < (0.02 if mu > 8 else 0.25)})
    return rows


def write_jsonl(name, rows):
    with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    write_jsonl("home_flips.jsonl", home_flips(random.Random(14)))
    write_jsonl("dwell_times.jsonl", dwell_times(random.Random(14)))
    (DATA / "quality_history.json").write_text(json.dumps(quality_history(), indent=1) + "\n", encoding="utf-8")
    ratings, pairs = style_ratings(random.Random(14))
    write_jsonl("style_ratings.jsonl", ratings)
    write_jsonl("style_pairs.jsonl", pairs)
    write_jsonl("style_slices.jsonl", style_slices(random.Random(14)))
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
