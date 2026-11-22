"""
exams_need_testing.py: even tests need testing. Certificates for testers.

Run:  python exams_need_testing.py

Language models are getting better at certification-style exam questions for testers. That does
not make an AI a certified tester. It means that exams which reward knowing the terminology, the
syllabus and the question format are no longer enough to describe expert knowledge of testing AI.
The human value moves towards defining risk, building a rubric, choosing a sample, interpreting
uncertainty, questioning benchmarks and defending a release decision.

Exams are evaluations too: they have an oracle, ambiguous questions, sometimes two defensible
answers, and the questions may have leaked into training data.

  1. the model takes the exam
  2. test the exam: ambiguous items, second defensible answers, leaked items
  3. the score on the items that survive the review
  4. what the exam measures, and what testing AI needs
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from metrickit import load_json, ngrams, overlap, wilson

HERE = Path(__file__).parent
LEAK_THRESHOLD = 0.5
WHERE_TO_PRACTISE = {
    "defining risk": "04-Collecting-Evidence (risk_sampling.py)",
    "building a rubric": "09-Raters-And-Rubrics",
    "choosing a sample": "04-Collecting-Evidence, 07-Signal-Or-Noise",
    "interpreting uncertainty": "06-Honest-Uncertainty, 08-Significant-Vs-Important",
    "questioning benchmarks": "12-Benchmark-Is-Not-Product",
    "defending a release decision": "05-Evidence-To-Release-Decision, 14 (weighted_metric.py)",
}


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def item_text(q) -> str:
    return q["question"] + " " + " ".join(f"{k}) {v}" for k, v in q["options"].items())


def main() -> None:
    exam = load_json(HERE / "data" / "exam_questions.json")
    qs = exam["questions"]
    corpus = ngrams((HERE / "data" / "training_snippets.txt").read_text(encoding="utf-8"))

    header("1. THE MODEL TAKES THE EXAM")
    right = sum(q["model_answer"] == q["key"] for q in qs)
    lo, hi = wilson(right, len(qs))
    print(f"  {right}/{len(qs)} correct by the answer key = {right / len(qs):.0%}  (95% interval {lo:.0%}-{hi:.0%}),"
          f" pass mark {exam['pass_mark']:.0%}  ->  {'PASS' if right / len(qs) >= exam['pass_mark'] else 'FAIL'}")
    print("  A headline would say: 'AI passes the tester certification'. Before believing it, test the exam.")

    header("2. TEST THE EXAM")
    print(f"  {'item':5} {'skill':12} {'key':>3} {'model':>5}  {'leaked':>6}  review")
    status = {}
    for q in qs:
        leak = overlap(item_text(q), corpus)
        r = q["reviewers"]
        notes = []
        if leak >= LEAK_THRESHOLD:
            notes.append("text found in a public question bank")
        if r.get("ambiguous"):
            notes.append("ambiguous: " + r["note"])
        elif r.get("also_defensible"):
            notes.append(f"{r['also_defensible']} also defensible: " + r["note"])
        status[q["id"]] = {"leaked": leak >= LEAK_THRESHOLD, "ambiguous": bool(r.get("ambiguous")),
                           "accepted": {q["key"], r.get("also_defensible")} - {None}}
        print(f"  {q['id']:5} {q['skill']:12} {q['key']:>3} {q['model_answer']:>5}  {leak:6.0%}  {'; '.join(notes) or '-'}")
    print(f"\n  'leaked' = share of the item's 8-word sequences that also appear in the question-bank text a")
    print(f"  model could have trained on. At {LEAK_THRESHOLD:.0%} or more the item measures memory, not knowledge.")
    print("  q09 is the oracle failing: the model's answer is the better one for an LLM system, and the key")
    print("  marks it wrong.")

    header("3. THE SCORE ON THE ITEMS THAT SURVIVE THE REVIEW")
    clean = [q for q in qs if not status[q["id"]]["leaked"] and not status[q["id"]]["ambiguous"]]
    strict = sum(q["model_answer"] == q["key"] for q in clean)
    fair = sum(q["model_answer"] in status[q["id"]]["accepted"] for q in clean)
    print(f"  removed: {sum(s['leaked'] for s in status.values())} leaked, "
          f"{sum(s['ambiguous'] and not s['leaked'] for s in status.values())} ambiguous; left: {len(clean)} items "
          f"({', '.join(q['id'] for q in clean)})")
    for name, k in (("by the original key", strict), ("accepting defensible answers", fair)):
        lo, hi = wilson(k, len(clean))
        print(f"    {name:30} {k}/{len(clean)}  95% interval {lo:.0%}-{hi:.0%}")
    print("  On the items that survive, the exam is too small to say much about anyone, human or model.")

    header("4. WHAT THE EXAM MEASURES, AND WHAT TESTING AI NEEDS")
    by_skill = Counter(q["skill"] for q in qs)
    print("  The exam's items by what they reward:")
    for s, c in by_skill.most_common():
        print(f"    {s:30} {c:2} item(s)")
    print("  The skills that testing AI needs, and how many items check them:")
    for s in exam["skills_testing_ai_needs"]:
        print(f"    {s:30} {by_skill.get(s, 0):2} item(s)   practise it in: {WHERE_TO_PRACTISE[s]}")
    print("\n  An exam that rewards terminology and format can be passed by a model. The work it does not")
    print("  measure is where a tester's value has moved. Even tests need testing.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
