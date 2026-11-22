"""
correct_but_ugly.py: correct but ugly is a failure too.

Run:  python correct_but_ugly.py

An output can be factually right and still look cheap, awkward or untrustworthy. Users judge their
trust in AI by the surface: wording, rhythm, layout, typography. That holds for texts, summaries,
slides, charts, dashboards, emails and agent reports. Aesthetic judgment is subjective, but it can
be organized:

  1. every output here is correct: the fact check passes for all of them
  2. negative examples, made checkable: generic, salesy, overconfident, alarming, too dense
  3. fit to the context: the same text in a consumer reply and in a medical report
  4. anchors: what 10, 7, 4 and 1 mean, and the ceiling the negative examples put on a score
  5. accessibility: a dashboard with the right numbers that fails contrast and screen readers
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from metrickit import contrast_ratio, load_json

HERE = Path(__file__).parent
CEILING = {"generic": 4, "salesy": 4, "too_dense": 7, "too_many_exclamations": 7, "overconfident": 1,
           "alarming": 1, "no_hedge": 4}


def header(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def lint(text: str, rubric: Dict) -> Dict[str, List[str]]:
    """Which negative examples does the text contain? Returns {category: [evidence]}."""
    low = text.lower()
    found = {}
    for cat, phrases in rubric["negative_examples"].items():
        hits = [p for p in phrases if p in low]
        if hits:
            found[cat] = hits
    longest = max(len(s.split()) for s in sentences(text))
    if longest > rubric["too_dense"]["max_words_per_sentence"]:
        found["too_dense"] = [f"{longest} words in one sentence"]
    return found


def judge_in_context(text: str, ctx_name: str, rubric: Dict) -> Tuple[List[str], int]:
    """Problems of the text in a given context, and the highest anchor it can still get."""
    ctx = rubric["contexts"][ctx_name]
    flags = lint(text, rubric)
    problems = [c for c in flags if c in ctx["forbidden"] or c == "too_dense"]
    if text.count("!") > ctx["max_exclamations"]:
        problems.append("too_many_exclamations")
    if ctx.get("needs_hedge") and not any(h in text.lower() for h in ctx["hedges"]):
        problems.append("no_hedge")
    return problems, min([CEILING[p] for p in problems] or [10])


def main() -> None:
    rubric = load_json(HERE / "data" / "style_rubric.json")
    outs = load_json(HERE / "data" / "style_outputs.json")
    texts = outs["texts"]

    header("1. EVERY OUTPUT HERE IS CORRECT")
    for name, t in texts.items():
        ok = all(f in t["text"] for f in t["facts"])
        print(f"  {name:15} [{t['context']:8}] facts {', '.join(t['facts']):34} {'PASS' if ok else 'FAIL'}")
    print("  A correctness check stops here, and calls all seven equally good.")

    header("2. NEGATIVE EXAMPLES, MADE CHECKABLE")
    for name, t in texts.items():
        flags = lint(t["text"], rubric)
        shown = "; ".join(f"{c}: {', '.join(v)}" for c, v in flags.items()) or "-"
        print(f"  {name:15} {shown}")
    print("\n  Without negative examples a rubric rewards the average. Naming them (generic, salesy,")
    print("  overconfident, too dense) gives raters and judges something concrete to fail.")

    header("3. FIT TO THE CONTEXT")
    print("  The highest score each text can still get (- = no ceiling, raters decide):")
    print(f"  {'':15} {'as a consumer reply':>20} {'as a medical report':>20}")
    for name, t in texts.items():
        cells = []
        for ctx in ("consumer", "medical"):
            _, ceiling = judge_in_context(t["text"], ctx, rubric)
            cells.append("-" if ceiling == 10 else str(ceiling))
        print(f"  {name:15} {cells[0]:>20} {cells[1]:>20}")
    for ctx in ("consumer", "medical", "finance_dashboard"):
        print(f"  - {ctx}: {rubric['contexts'][ctx]['about']}")
    print("\n  ldl_warm is fine for a consumer and wrong for a medical report: one exclamation mark.")
    print("  ldl_alarming and ldl_soothing state the same numbers. One causes panic, the other suggests")
    print("  more certainty than the model has. In health topics, style must do neither.")

    header("4. ANCHORS, AND THE CEILING THAT NEGATIVE EXAMPLES SET")
    for score, meaning in rubric["anchors"].items():
        print(f"  {score:>2}  {meaning}")
    print(f"  Dimensions to name for text: {', '.join(rubric['dimensions']['text'])}")
    print(f"  Dimensions to name for graphics: {', '.join(rubric['dimensions']['graphics'])}")
    print("\n  A checker cannot give a 10: that needs a person who knows the brand and the reader.")
    print("  It can stop a 4 from being rated a 7. Each text in its own context:")
    for name, t in texts.items():
        problems, ceiling = judge_in_context(t["text"], t["context"], rubric)
        cap = "no ceiling, raters decide" if ceiling == 10 else f"at most {ceiling}"
        print(f"    {name:15} {t['context']:9} {cap:26} {', '.join(problems)}")

    header("5. ACCESSIBILITY: TASTE DOES NOT OVERRIDE USABILITY")
    ctx = rubric["contexts"]["finance_dashboard"]
    for name, d in outs["dashboards"].items():
        issues = []
        for role, colour in d["text"].items():
            r = contrast_ratio(colour, d["background"])
            if r < ctx["min_text_contrast"]:
                issues.append(f"{role} text contrast {r:.1f}:1 (needs {ctx['min_text_contrast']}:1)")
        if len(d["series_colours"]) > ctx["max_series_colours"]:
            issues.append(f"{len(d['series_colours'])} series colours (readable: up to {ctx['max_series_colours']})")
        levels = [int(h[1]) for h in d["headings"]]
        skips = [f"h{a}->h{b}" for a, b in zip(levels, levels[1:]) if b > a + 1]
        if skips:
            issues.append(f"heading levels skipped for screen readers: {', '.join(skips)}")
        no_alt = [c["id"] for c in d["charts"] if not c["alt_text"]]
        if no_alt:
            issues.append(f"charts without alt text: {', '.join(no_alt)}")
        print(f"  {name}: numbers correct: {d['numbers_correct']}; "
              f"{'accessible' if not issues else str(len(issues)) + ' problem(s)'}")
        for i in issues:
            print(f"    - {i}")
    print("\n  An output that fails contrast, readability or screen-reader structure is not high quality,")
    print("  however modern it looks.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
