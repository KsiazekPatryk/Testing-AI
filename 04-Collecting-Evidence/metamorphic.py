"""
metamorphic.py: test relations, not answers.

Run:  python metamorphic.py
      python metamorphic.py --seed 7          # different wording, same relations
      python metamorphic.py --temperature 0   # always the most likely wording

There is no single correct answer to compare against. Instead, each case changes the
input in a controlled way (paraphrase, typos, an irrelevant detail, a different name,
a translation, an extra search candidate) and checks that the facts that matter stay
the same. The wording of the answer is allowed to change. The facts are not.

Every broken relation is saved to output/golden_set_candidates.json, ready to be
reviewed and promoted into the golden set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from assistant import answer, extract_facts
from search import load_articles, rank
from transformations import add_irrelevant_detail, add_typos, describe, swap_name

HERE = Path(__file__).parent
OUTPUT = HERE / "output"


def facts_for(question: str, seed: int, temperature: float) -> Tuple[str, Dict[str, object]]:
    reply = answer(question, seed=seed, temperature=temperature)
    facts = extract_facts(reply.text)
    facts["risk"] = reply.meta["risk"]
    return reply.text, facts


def build_variants(case: Dict) -> List[Tuple[str, str, str]]:
    """Return (label, base question, transformed question) for every variant."""
    base = case["base"]
    out = []
    for v in case["variants"]:
        kind = v["type"]
        label = describe(kind, v.get("language"))
        if kind in ("paraphrase", "typos", "translation"):
            out.append((label, base, v["text"]))
        elif kind == "typos_auto":
            for s in v["seeds"]:
                out.append((f"{label}, seed {s}", base, add_typos(base, seed=s)))
        elif kind == "irrelevant_detail":
            out.append((label, base, add_irrelevant_detail(base, v["detail"])))
        elif kind == "name_change":
            out.append((f"{label}: {v['to']}", base, swap_name(base, v["from"], v["to"])))
    return out


def run_cases(cases: List[Dict], seed: int, temperature: float) -> Tuple[int, int, List[Dict]]:
    held = total = 0
    candidates: List[Dict] = []
    for case in cases:
        relation = case["relation"]
        base_text, base_facts = facts_for(case["base"], seed, temperature)
        print(f"\n{'=' * 78}\nCase: {case['id']}   (relation: {', '.join(relation)} must not change)")
        print(f"Base question: {case['base']}")
        print(f"  answer: {base_text}")
        print(f"  facts:  {', '.join(f'{k}={base_facts[k]}' for k in relation)}\n")
        for i, (label, _, question) in enumerate(build_variants(case), 1):
            text, facts = facts_for(question, seed + i, temperature)
            changed = [k for k in relation if facts[k] != base_facts[k]]
            total += 1
            status = "FAIL" if changed else "PASS"
            held += not changed
            print(f"  [{status}] {label}")
            print(f"         question: {question}")
            print(f"         answer:   {text}")
            if changed:
                print("         changed:  " + ", ".join(f"{k}: {base_facts[k]} -> {facts[k]}" for k in changed))
                candidates.append({
                    "id": f"{case['id']}::{label}",
                    "question": question,
                    "expect": {k: base_facts[k] for k in relation if k != "risk"},
                    "why": f"Metamorphic relation broken ({label}): " +
                           ", ".join(f"{k} {base_facts[k]} -> {facts[k]}" for k in changed),
                    "source": "metamorphic.py",
                })
    return held, total, candidates


def run_ranking(spec: Dict) -> Tuple[int, int]:
    articles = load_articles()
    weak = json.loads((HERE / "help_center.json").read_text(encoding="utf-8"))["weak_candidates"]
    query = spec["query"]
    best = rank(query, articles)[0][0]
    print(f"\n{'=' * 78}\nCase: {spec['id']}\nRelation: {spec['relation']}")
    print(f"Query: {query}\nBest article without extra candidates: {best}\n")
    held = 0
    for extra in weak:
        ranking = rank(query, articles + [extra])
        top = ranking[0][0]
        ok = top == best
        held += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] Add weaker candidate: {extra['id']}")
        print(f"         new top 3: {', '.join(f'{d} ({s})' for d, s in ranking[:3])}")
        if not ok:
            print(f"         changed:  first place {best} -> {top} (raw word counts reward keyword stuffing)")
    return held, len(weak)


def main() -> None:
    ap = argparse.ArgumentParser(description="Metamorphic tests for the local support assistant.")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.7)
    a = ap.parse_args()

    spec = json.loads((HERE / "metamorphic_cases.json").read_text(encoding="utf-8"))
    held, total, candidates = run_cases(spec["cases"], a.seed, a.temperature)
    r_held, r_total = run_ranking(spec["ranking"])
    held, total = held + r_held, total + r_total

    print(f"\n{'=' * 78}\nRelations that held: {held}/{total}")
    print("The wording is allowed to differ between answers. The facts are not.")
    if candidates:
        OUTPUT.mkdir(exist_ok=True)
        path = OUTPUT / "golden_set_candidates.json"
        path.write_text(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n{len(candidates)} broken answer relations saved as golden set candidates: {path.relative_to(HERE)}")
        print("Review them, then add the ones that matter to golden_set.json, where they stay for good.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
