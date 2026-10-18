"""
transformations.py: controlled changes to an input for metamorphic testing.

Each transformation keeps the meaning (and the facts) of the question the same.
If the answer's facts change, the system is fragile, however good it looked on
"clean" inputs.
"""

from __future__ import annotations

import random
import re
from typing import Optional


def add_typos(text: str, *, seed: int = 0, rate: float = 0.35) -> str:
    """Realistic typos: swap two letters, drop one, or double one.

    Digits are never touched, so the facts in the question stay the same.
    The same seed always gives the same typos, so a failure can be reproduced.
    """
    rng = random.Random(seed)

    def mangle(match: "re.Match[str]") -> str:
        word = match.group(0)
        if len(word) < 4 or rng.random() > rate:
            return word
        i = rng.randrange(1, len(word) - 2)
        kind = rng.choice(["swap", "drop", "double"])
        if kind == "swap":
            return word[:i] + word[i + 1] + word[i] + word[i + 2:]
        if kind == "drop":
            return word[:i] + word[i + 1:]
        return word[:i] + word[i] + word[i:]

    return re.sub(r"[^\W\d_]+", mangle, text)


def add_irrelevant_detail(text: str, detail: str) -> str:
    return f"{text.rstrip()} {detail.strip()}"


def swap_name(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def describe(kind: str, language: Optional[str] = None) -> str:
    labels = {
        "paraphrase": "Paraphrase",
        "typos": "Typos (hand-written)",
        "typos_auto": "Typos (generated)",
        "irrelevant_detail": "Irrelevant detail",
        "name_change": "Name change",
        "translation": "Translation",
    }
    label = labels.get(kind, kind)
    return f"{label}: {language}" if language else label


if __name__ == "__main__":
    q = "Can I return my shoes after 45 days?"
    for s in range(1, 6):
        print(f"seed={s}: {add_typos(q, seed=s)}")
