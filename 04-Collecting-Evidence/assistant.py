"""
assistant.py: a local, fake customer support assistant for a shoe store.

No API key, no internet. It behaves like a real LLM-based assistant in the ways
that matter for this example:
  * the wording changes between runs (temperature and seed),
  * the facts come from rules that have realistic, hidden bugs.

Store policy: shoes can be returned within 30 days of purchase. No documented exceptions.

Bugs planted on purpose (the metamorphic tests should find them):
  1. Any mention of a "gift" triggers an outdated holiday rule: "gifts can be exchanged
     within 90 days". Adding an irrelevant detail changes the facts.
  2. Questions in Spanish hit a wrong locale rule: "14-day right of withdrawal".
     Translating the question changes the business rule.
  3. Intent detection is keyword-based. A typo such as "retrun" or a new word such as
     "refund" sends the customer to a generic answer with no policy at all.
  4. It knows nothing about the new holiday return extension (live traffic shows that).

Want to plug in a real model? Replace the body of `answer()` so it calls your API and
returns a Reply. Everything else (relations, golden set, live samples) keeps working.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

RETURN_WINDOW_DAYS = 30
MODEL_ID = "local-fake-support-assistant-v4"


@dataclass
class Reply:
    text: str
    meta: Dict[str, object] = field(default_factory=dict)


# --- Language and intent ----------------------------------------------------

POLISH_HINTS = ("zwróc", "zwrot", "odesł", "dni", "tygod", "miesi", "czy mogę")
SPANISH_HINTS = ("devolver", "devoluc", "días", "dias", "zapatos", "puedo")
RETURN_WORDS = ("return", "send back", "send them back", "exchange",  # English
                "zwróc", "zwrot", "odesł",                            # Polish
                "devolver", "devoluc")                                # Spanish
PRICING_WORDS = ("price", "pricing")


def detect_language(text: str) -> str:
    t = text.lower()
    if any(h in t for h in SPANISH_HINTS):
        return "es"
    if any(h in t for h in POLISH_HINTS):
        return "pl"
    return "en"


def detect_intent(text: str) -> str:
    t = text.lower()
    if any(w in t for w in PRICING_WORDS):
        return "pricing"
    if any(w in t for w in RETURN_WORDS):
        return "return"
    return "other"


# --- Reading "how long ago" from the question --------------------------------

UNIT_DAYS = [
    (r"(\d+)\s*(?:days?|dni|dniach|dzień|días|dias)\b", 1),
    (r"(\d+)\s*(?:weeks?|tygodni|tygodnie|semanas)\b", 7),
    (r"(\d+)\s*(?:months?|miesięcy|miesiące|meses)\b", 30),
]
PHRASES = [
    (r"(?:a\s+)?month and a half", 45),
    (r"półtora miesiąca", 45),
    (r"six weeks", 42),
    (r"two months", 60),
    (r"a week", 7),
]


def parse_days(text: str) -> Optional[int]:
    t = text.lower()
    for pattern, days in PHRASES:
        if re.search(pattern, t):
            return days
    for pattern, multiplier in UNIT_DAYS:
        m = re.search(pattern, t)
        if m:
            return int(m.group(1)) * multiplier
    return None


# --- Wording variants (the "non-deterministic" part) ------------------------
# Every template mentions the return window first, so a fact checker can read it.

OUTSIDE = [
    "Our return window is {w} days, so a purchase from {d} days ago is outside it.",
    "Returns are possible for {w} days after purchase. At {d} days, it's too late for a standard return.",
    "Our return window is {w} days, and {d} days is past it, I'm afraid.",
]
INSIDE = [
    "Yes, you're still within the {w}-day return window.",
    "You can return them: our window is {w} days and you're at day {d}.",
]
ASK = [
    "Returns are accepted within {w} days of purchase. When did you buy them?",
    "We accept returns for {w} days after purchase. Could you tell me the purchase date?",
]
GENERIC = [
    "Thanks for reaching out! Orders over $50 ship for free. Anything else I can help with?",
    "Happy to help! You can track your order from the link in your confirmation email.",
]
GIFT_BUG = [
    "Gifts can be exchanged within 90 days of purchase, so you're still in time.",
    "Good news: gifts have a 90-day exchange window, so you're still within it.",
]
SPANISH_BUG_OUTSIDE = ["EU customers have a 14-day right of withdrawal, so {d} days is too late."]
SPANISH_BUG_INSIDE = ["EU customers have a 14-day right of withdrawal, so you're still within it."]
PRICING = [
    "According to the official pricing page (checked 2026-10-01), prices may have changed. "
    "Please check the current page before relying on any number.",
]


def _pick(options: List[str], rng: random.Random, temperature: float) -> str:
    return options[0] if temperature <= 0.05 else rng.choice(options)


def answer(question: str, *, seed: Optional[int] = None, temperature: float = 0.7) -> Reply:
    rng = random.Random(seed)
    lang = detect_language(question)
    intent = detect_intent(question)
    days = parse_days(question)
    lowered = question.lower()
    # Risk is computed from the request content only, never from the customer's name.
    risk = "high" if (days or 0) > 180 or "chargeback" in lowered else "normal"
    meta = {"model": MODEL_ID, "language": lang, "intent": intent, "days": days, "risk": risk}

    if intent == "pricing":
        meta["branch"] = "pricing"
        return Reply(_pick(PRICING, rng, temperature), meta)
    if intent != "return":
        meta["branch"] = "generic"
        return Reply(_pick(GENERIC, rng, temperature), meta)
    if "gift" in lowered:                       # bug 1
        meta["branch"] = "gift_rule_outdated"
        return Reply(_pick(GIFT_BUG, rng, temperature), meta)
    if lang == "es":                            # bug 2
        meta["branch"] = "eu_locale_rule"
        options = SPANISH_BUG_INSIDE if days is not None and days <= 14 else SPANISH_BUG_OUTSIDE
        return Reply(_pick(options, rng, temperature).format(d=days or "?"), meta)
    if days is None:
        meta["branch"] = "ask_for_date"
        return Reply(_pick(ASK, rng, temperature).format(w=RETURN_WINDOW_DAYS), meta)

    meta["branch"] = "policy"
    options = OUTSIDE if days > RETURN_WINDOW_DAYS else INSIDE
    return Reply(_pick(options, rng, temperature).format(w=RETURN_WINDOW_DAYS, d=days), meta)


# --- Reading facts back out of an answer -------------------------------------

def extract_facts(text: str) -> Dict[str, object]:
    """The facts a relation compares. Wording may change; these must not."""
    t = text.lower()
    m = re.search(r"(\d+)[- ]day", t)
    window = int(m.group(1)) if m else None
    if re.search(r"outside|too late|past it|no longer", t):
        verdict = "outside"
    elif re.search(r"still within|still in time|you can return|within it", t):
        verdict = "inside"
    else:
        verdict = "unknown"
    return {"window_days": window, "verdict": verdict}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Can I return my shoes after 45 days?"
    for s in (1, 2, 3):
        r = answer(q, seed=s)
        print(f"seed={s}: {r.text}\n        facts={extract_facts(r.text)} branch={r.meta['branch']}")
