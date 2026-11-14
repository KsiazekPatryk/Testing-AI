"""
copy_the_idea.py: copy the idea of the measurement, not the score.

Run:  python copy_the_idea.py

Public evaluations are reference points and lessons in measurement design, not release gates.
Each teaches a pattern. Then you build the evaluation your system actually deserves:
  1. search: relevance labels, freshness, no duplicates, and position matters
  2. support chatbot: Arena-style pairwise preference, next to policy, tool and escalation checks
  3. medical image app and home robot: the right answer in a quiz is not enough
"""

from __future__ import annotations

import sys
from typing import Dict, List

from evals import mean, ndcg, reciprocal_rank

PATTERNS = [
    ("multiple-choice accuracy", "bounded knowledge"),
    ("unit tests", "behavior you can execute"),
    ("patch validation", "work in a repository"),
    ("pairwise preference", "subjective answer quality"),
    ("rubrics", "fuzzy human judgment"),
    ("ranking metrics", "ordered evidence"),
    ("multi-metric suites", "trade-offs"),
    ("red-team scenarios", "the tail of risk"),
]


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def search() -> None:
    header("1. SEARCH: 'waterproof hiking boots women size 39'")
    # relevance 0-3, published year, and a duplicate flag, for the top 10 of two rankers
    a = [(3, 2026, False), (2, 2026, False), (2, 2025, False), (1, 2026, False), (1, 2024, False),
         (0, 2026, False), (1, 2025, False), (0, 2023, False), (0, 2025, False), (0, 2026, False)]
    b = [(1, 2026, False), (2, 2019, False), (2, 2019, True), (1, 2026, False), (1, 2024, False),
         (0, 2026, False), (1, 2025, False), (0, 2023, False), (3, 2026, False), (0, 2026, False)]
    print(f"  {'ranker':8} {'relevant in top 10':>19} {'NDCG@10':>8} {'MRR (perfect hit)':>18} {'stale (<2024)':>14} {'duplicates':>11}")
    for name, res in (("A", a), ("B", b)):
        gains = [0 if d else r for r, _, d in res]          # a duplicate adds nothing
        print(f"  {name:8} {sum(r > 0 for r, _, _ in res):>19} {ndcg(gains):>8.2f} "
              f"{reciprocal_rank([r == 3 for r, _, _ in res]):>18.2f} {sum(y < 2024 for _, y, _ in res):>14} "
              f"{sum(d for _, _, d in res):>11}")
    print("  B even has more 'relevant' results in its top 10. But it puts the perfect answer at rank 9,")
    print("  shows 2019 listings near the top and the same product twice. A count of relevant results")
    print("  cannot see any of it; position-aware metrics, freshness and duplicate checks can.")


def support() -> None:
    header("2. SUPPORT CHATBOT: PAIRWISE PREFERENCE + POLICY CHECKS")
    # 200 conversations judged pairwise by people, and checked against the returns policy
    models: Dict[str, Dict] = {
        "model-friendly": {"wins": 128, "policy_violations": 18, "missed_escalations": 7, "tool_errors": 3},
        "model-careful": {"wins": 72, "policy_violations": 2, "missed_escalations": 1, "tool_errors": 2},
    }
    n = 200
    print(f"  {'model':16} {'preferred':>10} {'policy violations':>18} {'missed escalations':>19} {'tool errors':>12}")
    for m, s in models.items():
        print(f"  {m:16} {s['wins'] / n:>10.0%} {s['policy_violations']:>18} {s['missed_escalations']:>19} {s['tool_errors']:>12}")
    gate = {"policy_violations": 5, "missed_escalations": 2}
    for m, s in models.items():
        fails = [k for k, lim in gate.items() if s[k] > lim]
        print(f"  release gate for {m}: " + ("PASS" if not fails else "FAIL (" + ", ".join(fails) + ")"))
    print("  The answer the crowd prefers can still break the returns policy. Preference measures taste;")
    print("  the gate measures what the business promised.")


def act_vs_talk() -> None:
    header("3. THE RIGHT ANSWER IN A QUIZ IS NOT ENOUGH")
    quiz = [True] * 20
    trials = [True] * 17 + [False] * 3
    print(f"  home robot, safety quiz ('may you put a glass near the table edge?'): {mean(quiz):.0%} correct")
    print(f"  home robot, 20 real kitchen trials:                                    {mean(trials):.0%} without knocking anything over")
    print("  A robot that explains the rules perfectly but knocks over a glass is not safe.")
    print("\n  medical image app: a correct multiple-choice answer is not the evaluation. It needs:")
    for item in ("image quality checks (blur, lighting, framing) before any answer",
                 "an uncertainty signal the user can see",
                 "a safe fallback: 'see a doctor' when the image or the model is unsure"):
        print(f"    - {item}")


def main() -> None:
    header("EACH PUBLIC EVALUATION TEACHES A PATTERN")
    for p, use in PATTERNS:
        print(f"  {p:26} for {use}")
    search()
    support()
    act_vs_talk()
    print("\n  Some teams ignore public evals ('not our product'), others treat a leaderboard place as proof of")
    print("  product quality. Both miss the point: borrow the measurement idea, build your own evaluation.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
