"""
search.py: a tiny help-center search, used for the ranking relation.

Relation to test: adding a weaker candidate to the index must not push the best
article out of first place.

Planted bug: the score is a raw count of matching words, with no length
normalization. A keyword-stuffed page can beat the real policy article.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).parent


def load_articles() -> List[Dict[str, str]]:
    return json.loads((HERE / "help_center.json").read_text(encoding="utf-8"))["articles"]


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score(query: str, article: Dict[str, str]) -> int:
    terms = set(_words(query))
    body = _words(article["title"] + " " + article["body"])
    return sum(1 for w in body if w in terms)


def rank(query: str, articles: List[Dict[str, str]]) -> List[Tuple[str, int]]:
    scored = [(a["id"], score(query, a)) for a in articles]
    return sorted(scored, key=lambda x: (-x[1], x[0]))


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "return shoes after 30 days"
    for doc_id, s in rank(q, load_articles()):
        print(f"{s:>3}  {doc_id}")
