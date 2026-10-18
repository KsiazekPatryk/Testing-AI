"""
check_my_questions.py: the exercise from the post.

"Take three questions your system answers and prepare two metamorphic transformations
 for each: a paraphrase and a version with typos. If any of them changes the facts in
 the answer, you have your first candidate for the golden set."

Run:  python exercise/check_my_questions.py
      python exercise/check_my_questions.py path/to/your_questions.json

Two ways to use it:
  1. As is: the local assistant answers every variant (no API key needed).
  2. With your own system: paste its answers into "answers" in the JSON file
     ({"original": "...", "paraphrase": "...", "typos": "..."}). The script then
     checks your answers instead of calling the local assistant.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from assistant import answer  # noqa: E402
from transformations import add_typos  # noqa: E402

DEFAULT_FILE = HERE / "my_questions.json"


def facts_present(text: str, patterns: List[str]) -> Dict[str, bool]:
    return {p: bool(re.search(p, text, flags=re.IGNORECASE)) for p in patterns}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    seed = spec.get("typo_seed", 1)
    candidates = []
    broken_total = 0

    for q in spec["questions"]:
        variants = {
            "original": q["question"],
            "paraphrase": q["paraphrase"],
            "typos": q.get("typos") or add_typos(q["question"], seed=seed),
        }
        pasted = q.get("answers") or {}
        mode = "your system's answers" if pasted else "local assistant"
        print(f"\n{'=' * 78}\n{q['id']}   (answers from: {mode})")
        print(f"Facts every answer must keep: {', '.join('/' + f + '/' for f in q['facts'])}")
        results = {}
        for name, text in variants.items():
            reply = pasted.get(name) if pasted else answer(text, seed=seed + len(results)).text
            if reply is None:
                print(f"  [skip] {name}: no answer pasted")
                continue
            present = facts_present(reply, q["facts"])
            results[name] = present
            missing = [f for f, ok in present.items() if not ok]
            status = "OK  " if not missing else "LOST"
            print(f"  [{status}] {name:10} {text}")
            print(f"         answer: {reply}")
            if missing:
                print(f"         missing facts: {', '.join('/' + m + '/' for m in missing)}")
                if name != "original":
                    broken_total += 1
                    candidates.append({"id": f"{q['id']}::{name}", "question": text,
                                       "facts": q["facts"], "answer": reply,
                                       "why": f"{name} lost: {', '.join(missing)}"})
        if "original" in results and not all(results["original"].values()):
            print("  ! The original answer already misses a fact. Fix that before testing relations.")

    print(f"\n{'=' * 78}")
    if not candidates:
        print("All transformations kept the facts. Try harder ones: another language, an irrelevant")
        print("detail, a different customer name, or more typos (change typo_seed).")
        return
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "exercise_golden_candidates.json"
    out.write_text(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{broken_total} transformation(s) changed the facts. You have your first golden set candidates:")
    for c in candidates:
        print(f"  - {c['id']}: {c['question']}")
    print(f"Saved to {out.relative_to(ROOT)}. Add the important ones to your golden set.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
