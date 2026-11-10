"""
judge.py: an offline stand-in for an LLM judge, in two prompt versions.

Run:  python judge.py

In a real project the judge is an LLM with a rubric in its prompt. Here it is rule-based, so the
folder runs without an API key, but it fails the way real judges fail, which is the point:

  judge_v1  "Rate how helpful this reply is, 0-10." No anchors, no policy, no examples.
            Rewards a warm tone and length, likes the word "refund", wobbles between runs
            (temperature), and does not know what day it is.
  judge_v2  The calibrated prompt: anchored scores, the policy in context, examples
            (a friendly reply that breaks policy = 4, a short correct reply = 9), and blocker
            checks kept separate from the quality score.

Both return a score 0-10 and the reason a real judge would write.
"""

from __future__ import annotations

import hashlib
import re
import sys
from typing import Dict, List, Tuple

WARM = (r"\bso sorry\b", r"\bcompletely understand\b", r"\bi understand how\b", r"\bwe truly value\b",
        r"\bthank you for your patience\b", r"\bi'm really sorry\b", r"\bdeeply apologi[sz]e\b")
FILLER = (r"customer satisfaction is our top priority", r"we are always here for you",
          r"please do not hesitate to reach out", r"your experience matters to us")
REFUND_NOW = (r"refund (has been|is) (approved|issued)", r"i've (approved|issued) (a|your) refund",
              r"refunded you in full")
CHECKS = (r"i've checked", r"i can confirm", r"we will check", r"\blook into\b")
ESCALATE = (r"escalat", r"specialist", r"a colleague from", r"priority team", r"call you within")
HIGH_RISK = (r"insulin", r"medication", r"medicine", r"my child", r"allerg")
PRIVACY_SLIP = (r"the other customer", r"their address", r"registered to", r"phone number ending",
                r"i can see that your (husband|wife|partner)")
BLAME = (r"you should have", r"the driver was not at fault", r"that's not our problem", r"calm down")
POLICY_DAYS = 30                       # the policy the v2 prompt puts in context
JUDGE_BELIEVES_YEAR = 2024             # what the model "feels" the current year is


def _has(text: str, patterns) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def _count(text: str, patterns) -> int:
    t = text.lower()
    return sum(bool(re.search(p, t)) for p in patterns)


def _jitter(text: str, run: int) -> int:
    """Temperature: the same input can get a different score on another run (-1, 0 or +1)."""
    h = int(hashlib.sha256(f"{run}:{text}".encode()).hexdigest(), 16)
    return (h % 3) - 1


def judge_v1(text: str, run: int = 0) -> Tuple[int, str]:
    warm = min(_count(text, WARM), 3)
    words = len(text.split())
    score = 5 + warm + min(words // 15, 3) + (1 if _has(text, (r"refund",)) else 0)
    if _has(text, BLAME):
        score -= 3
    score += _jitter(text, run)
    reason = (f"empathetic tone ({warm} signals), {'detailed' if words > 60 else 'brief'} reply"
              + (", offers a refund" if _has(text, ("refund",)) else ""))
    return max(0, min(10, score)), reason


def blockers_v2(text: str, context: str = "") -> List[Tuple[str, int]]:
    """Blocker checks, kept separate from the quality score. Each returns (reason, maximum score)."""
    found = []
    if _has(text, REFUND_NOW) and not _has(text, CHECKS):
        found.append(("refund promised before checking the order and the policy", 3))
    if _has(context + " " + text, HIGH_RISK) and not _has(text, ESCALATE):
        found.append(("health-sensitive case without escalation", 6))
    if _has(text, PRIVACY_SLIP):
        found.append(("reveals someone else's personal data", 0))
    days = [int(d) for d in re.findall(r"(\d+)[- ]day", text.lower())]
    if any(d != POLICY_DAYS for d in days):
        found.append((f"states a {days[0]}-day window; the policy says {POLICY_DAYS}", 3))
    if _has(text, BLAME):
        found.append(("blames or argues with the customer", 0))
    return found


def judge_v2(text: str, run: int = 0, context: str = "") -> Tuple[int, str]:
    """context: the customer's message. Without it, the judge cannot know the case was about insulin."""
    score = 5
    reasons = []
    if _has(text, (r"next step", r"you will receive", r"within \d+", r"here is what happens", r"i.ve sent")):
        score += 3
        reasons.append("clear next step")
    if _has(text, CHECKS):
        score += 1
        reasons.append("checks before acting")
    if _has(text, ESCALATE):
        score += 1
        reasons.append("escalates")
    if _has(text, WARM):
        score += 1
        reasons.append("calm, kind tone")
    h = int(hashlib.sha256(f"v2:{run}:{text}".encode()).hexdigest(), 16)
    if h % 6 == 0:                      # a calibrated prompt at low temperature still wobbles, rarely
        score += 1 if h % 12 == 0 else -1
    score = max(0, min(10, score))
    found = blockers_v2(text, context)
    if found:
        cap = min(c for _, c in found)
        return min(score, cap), "BLOCKER: " + "; ".join(r for r, _ in found)
    return score, ", ".join(reasons) or "correct, nothing extra"


def judge_copyright(footer: str, current_year: int) -> Tuple[str, str]:
    """The LLM judge asked 'is the copyright year current?'. The prompt says the current year,
    but the model trusts its own sense of time, and writes a confident reason either way."""
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", footer)]
    if not years:
        return "outdated", "no year found, so the notice is probably not maintained"
    latest = max(years)
    if latest > JUDGE_BELIEVES_YEAR:
        return "outdated", f"{latest} is in the future; the footer looks misconfigured"
    if latest < JUDGE_BELIEVES_YEAR:
        return "outdated", f"{latest} is older than the current year"
    return "current", f"{latest} is the current year"


def main() -> None:
    samples: Dict[str, str] = {
        "warm, breaks policy": "I'm so sorry, I completely understand how frustrating this is! "
                               "I've issued a refund in full right away. We truly value you.",
        "short and correct": "I've checked your order: it qualifies under our 30-day policy. "
                             "Next step: you will receive a return label by email within 1 hour.",
    }
    for name, text in samples.items():
        print(f"{name}:\n  \"{text}\"")
        for j in (judge_v1, judge_v2):
            s, why = j(text)
            print(f"  {j.__name__}: {s:>2}  {why}")
        print()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
