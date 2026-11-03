"""
generate_data.py: writes the example data in data/ (always the same content).

Run:  python generate_data.py

The data is invented, but shaped like real labeling work:
  calibration.jsonl      3 raters score the same 40 support answers, before and after calibration
  blind_review.jsonl     old vs new answers of equal quality, rated with and without blinding
  session_log.jsonl      3 rating sessions of 150 items, with gold (attention-check) items
  relevance_labels.jsonl the same answers labeled by generalists, domain experts and an LLM judge
  eval_labels.jsonl      an evaluation set whose labels may or may not carry provenance
  support_responses.jsonl answers scored per rubric dimension, with blocker flags
The rubrics and the agent patches are hand-written JSON files next to them.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"


def clamp(x: float, lo: int = 0, hi: int = 10) -> int:
    return max(lo, min(hi, int(round(x))))


def write_jsonl(name: str, rows) -> None:
    with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def calibration(rng: random.Random):
    # Before: "rate quality 1-10". Anna is lenient, Ben is strict, Chen reads "complete" his own way.
    # After: the same items, with anchors and a calibration session behind them.
    raters = {"before": {"anna": (1.6, 1.0), "ben": (-1.6, 1.0), "chen": (0.0, 2.2)},
              "after": {"anna": (0.2, 0.6), "ben": (-0.2, 0.6), "chen": (0.0, 0.7)}}
    quality = [rng.choice([2, 4, 5, 6, 7, 7, 8, 8, 9, 10]) + rng.uniform(-0.4, 0.4) for _ in range(40)]
    rows = []
    for rnd, people in raters.items():
        for rater, (bias, sd) in people.items():
            for i, q in enumerate(quality):
                rows.append({"item": f"resp-{i + 1:03d}", "round": rnd, "rater": rater,
                             "score": clamp(q + bias + rng.gauss(0, sd))})
    return rows


def blind_review(rng: random.Random):
    # Both versions have the same true quality. Unblinded: the rater sees "NEW" and the new answer is
    # always shown first. Blinded: the source is hidden and the order is random.
    rows = []
    for i in range(60):
        q_old, q_new = rng.gauss(7.0, 1.2), rng.gauss(7.0, 1.2)
        for cond in ("unblinded", "blinded"):
            new_first = True if cond == "unblinded" else rng.random() < 0.5
            for version, q in (("old", q_old), ("new", q_new)):
                first = (version == "new") == new_first
                label_bias = 0.8 if (cond == "unblinded" and version == "new") else 0.0
                score = clamp(q + label_bias + (0.4 if first else 0.0) + rng.gauss(0, 0.5))
                rows.append({"case": f"case-{i + 1:03d}", "condition": cond, "version": version,
                             "shown_first": first, "score": score})
    return rows


def sessions(rng: random.Random):
    # Every 5th item is a gold item with a known answer. Chen's session is long and heavy;
    # after item 90 he misses more gold items and starts passing everything.
    rows = []
    for rater in ("anna", "ben", "chen"):
        for pos in range(1, 151):
            tired = rater == "chen" and pos > 90
            gold = pos % 5 == 0
            truth = "pass" if rng.random() < 0.7 else "fail"
            acc = (0.55 if tired else 0.97) if gold else (0.7 if tired else 0.92)
            label = truth if rng.random() < acc else ("fail" if truth == "pass" else "pass")
            if tired and label == "fail" and rng.random() < 0.5:
                label = "pass"
            row = {"rater": rater, "position": pos, "minute": round(pos * 0.8, 1),
                   "is_gold": gold, "label": label}
            if gold:
                row["gold_label"] = truth
            rows.append(row)
    return rows


QUERIES = {
    "general": ["best way to clean a cast-iron pan", "how long to boil an egg", "cheap weekend trip ideas",
                "how to remove a wine stain", "good beginner houseplants", "how to fold a fitted sheet"],
    "medical": ["best treatment for runner's knee after a marathon", "can I take ibuprofen with blood thinners",
                "persistent headache after a fall", "is it safe to run with shin splints",
                "how much vitamin D should an adult take", "chest tightness when climbing stairs"],
    "construction": ["best waterproof work boots for a roofer in Phoenix in summer",
                     "safe ladder angle for roof access", "which harness for working on a pitched roof",
                     "how to work safely in 40 degree heat", "boots that survive hot tar",
                     "gloves for handling roofing sheets"],
    "legal": ["can my landlord keep the deposit for normal wear", "do I need a lawyer for a small claim",
              "is a verbal contract binding", "can my employer read my work email",
              "what to do after a minor car accident", "how to contest a parking fine"],
    "coding": ["fix a failing tenant isolation test", "why is my SQL query slow",
               "how to store passwords safely", "python list vs tuple",
               "how to debounce a search input", "what is a race condition"],
}

# What each kind of rater rewards, per answer style.
#  polished_popular: a glossy blog or review site; expert_grounded: guidelines, caveats, field details.
PREFERENCE = {
    #               generalist (polished, grounded)   expert (polished, grounded)
    "general":      ((7.6, 7.2), (7.3, 7.5)),
    "medical":      ((8.3, 6.4), (3.6, 8.6)),
    "construction": ((8.1, 6.6), (4.2, 8.4)),
    "legal":        ((7.9, 6.7), (4.5, 8.2)),
    "coding":       ((7.4, 7.1), (5.9, 8.0)),
}


def relevance(rng: random.Random):
    # Flat pay per query: the same four quick generalists end up labeling most medical queries.
    rows = []
    for domain, queries in QUERIES.items():
        (g_pol, g_gr), (e_pol, e_gr) = PREFERENCE[domain]
        for qi, q in enumerate(queries):
            for rep in range(2):
                for style, g_mu, e_mu in (("polished_popular", g_pol, e_pol), ("expert_grounded", g_gr, e_gr)):
                    g = clamp(rng.gauss(g_mu, 0.8))
                    labeled_by = (rng.choice(["g01", "g02", "g03", "g04"]) if rng.random() < 0.85
                                  else rng.choice(["g05", "g06", "g07", "g08", "g09", "g10"]))
                    rows.append({"query": q, "domain": domain, "variant": rep + 1, "answer_style": style,
                                 "generalist_score": g, "generalist_id": labeled_by,
                                 "expert_score": clamp(rng.gauss(e_mu, 0.8)),
                                 # A judge tuned on the generalist labels: same taste, less noise.
                                 "llm_judge_score": clamp(g_mu + rng.gauss(0, 0.4)),
                                 "llm_judge_confidence": round(min(0.99, rng.uniform(0.86, 0.97)), 2)})
    return rows


def eval_labels(rng: random.Random):
    rows = []
    for i in range(200):
        domain = rng.choice(["general", "general", "medical", "legal", "coding", "construction"])
        high_risk = domain in ("medical", "legal") or rng.random() < 0.15
        gate = high_risk and rng.random() < 0.6
        source = rng.random()
        if source < 0.45:
            who, kind, exp = rng.choice(["g01", "g02", "g03", "g04"]), "generalist", "none"
        elif source < 0.65:
            who, kind, exp = rng.choice(["qa-ola", "qa-piotr"]), "qa_reviewer", "support QA, 2 years"
        elif source < 0.80:
            who, kind = rng.choice(["dr-nowak", "adv-lis", "eng-kowal"]), "expert"
            exp = {"dr-nowak": "physiotherapist", "adv-lis": "lawyer", "eng-kowal": "senior engineer"}[who]
        else:
            who, kind, exp = "llm-judge-v3", "llm", "none"
        n = rng.choice([1, 1, 1, 2, 3])
        row = {"label_id": f"lbl-{i + 1:04d}", "item": f"item-{i + 1:04d}", "domain": domain,
               "high_risk": high_risk, "used_in_release_gate": gate,
               "label": rng.choice(["pass", "pass", "pass", "fail"]),
               "created_by": who, "rater_type": kind, "expertise": exp,
               "guideline_version": rng.choice(["support-rubric-v2", "support-rubric-v2", "support-rubric-v1"]),
               "n_raters": n, "agreement": None if n == 1 else round(rng.choice([0.5, 0.67, 1.0, 1.0]), 2)}
        # Real datasets lose metadata: imports, old spreadsheets, "someone labeled these last year".
        if rng.random() < 0.22:
            for k in ("created_by", "rater_type", "expertise", "guideline_version"):
                row[k] = None
        rows.append(row)
    return rows


def support_responses():
    # Dimension scores already given by a rater following the rubric anchors (0-10).
    def r(rid, text, version, scores, blockers=()):
        return {"id": rid, "summary": text, "rubric_version": version, "scores": scores,
                "blockers": list(blockers)}
    dims = ("policy_correctness", "completeness", "tone", "actionability", "safety")
    rows = [
        r("sup-01", "Correct refund window, clear steps, friendly", "support-rubric-v2", dict(zip(dims, (10, 9, 9, 9, 10)))),
        r("sup-02", "Correct policy, misses the receipt requirement", "support-rubric-v2", dict(zip(dims, (9, 6, 9, 7, 10)))),
        r("sup-03", "Warm and detailed, but invents a 60-day refund window", "support-rubric-v2",
          dict(zip(dims, (1, 9, 10, 8, 9))), ["invented_policy"]),
        r("sup-04", "Very polite, pastes another customer's address and order", "support-rubric-v2",
          dict(zip(dims, (9, 9, 10, 9, 2))), ["personal_data_leak"]),
        r("sup-05", "Curt, but correct and complete", "support-rubric-v2", dict(zip(dims, (10, 9, 4, 9, 10)))),
        r("sup-06", "Vague: 'please check our policy page'", "support-rubric-v2", dict(zip(dims, (7, 3, 8, 2, 10)))),
        r("sup-07", "Correct, but tells the customer to unplug a gas appliance themselves", "support-rubric-v2",
          dict(zip(dims, (8, 8, 9, 8, 1))), ["unsafe_advice"]),
        r("sup-08", "Scored last month under v1 of the rubric", "support-rubric-v1", dict(zip(dims, (8, 8, 8, 8, 9)))),
    ]
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    rng = random.Random(8)
    write_jsonl("calibration.jsonl", calibration(rng))
    write_jsonl("blind_review.jsonl", blind_review(rng))
    write_jsonl("session_log.jsonl", sessions(random.Random(2)))
    write_jsonl("relevance_labels.jsonl", relevance(rng))
    write_jsonl("eval_labels.jsonl", eval_labels(rng))
    write_jsonl("support_responses.jsonl", support_responses())
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
