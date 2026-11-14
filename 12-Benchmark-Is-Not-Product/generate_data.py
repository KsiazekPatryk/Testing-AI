"""
generate_data.py: writes the example data in data/ (always the same content).

Run:  python generate_data.py

  mc_results.jsonl       a model on 1,000 multiple-choice questions in 10 subjects (MMLU-style)
  code_samples.jsonl     40 coding problems, 10 samples each, how many passed (HumanEval-style)
  arena_votes.jsonl      2,400 pairwise votes between three models (Arena-style), with answer length
                         and whether each answer was factually correct
  contamination.jsonl    150 public benchmark questions: published before training or not, and the model's
                         result on the original, a paraphrase, and a fresh question of the same kind
  training_snippets.txt  a slice of "training data" scraped from the web
  agent_runs.jsonl       60 browser-agent tasks: the expected click path, the actual path, the final state
The benchmark and product descriptions are hand-written JSON files.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"
SUBJECTS = {"high_school_math": 0.93, "economics": 0.91, "anatomy": 0.90, "world_history": 0.93,
            "computer_science": 0.92, "marketing": 0.95, "philosophy": 0.89, "professional_law": 0.58,
            "computer_security": 0.64, "clinical_knowledge": 0.86}


def write_jsonl(name: str, rows) -> None:
    with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def mc_results(rng):
    rows = []
    for subject, acc in SUBJECTS.items():
        k = round(acc * 100)
        flags = [True] * k + [False] * (100 - k)
        rng.shuffle(flags)
        rows += [{"subject": subject, "item": f"{subject}-{i + 1:03d}", "correct": c} for i, c in enumerate(flags)]
    return rows


def code_samples(rng):
    rows = []
    for i in range(40):
        difficulty = rng.random()
        p = 0.95 if difficulty < 0.4 else 0.55 if difficulty < 0.75 else 0.12
        c = sum(rng.random() < p for _ in range(10))
        rows.append({"problem": f"func-{i + 1:03d}", "n_samples": 10, "n_correct": c})
    return rows


def arena_votes(rng):
    """Three models. 'verbose' writes long, confident answers and is right less often.
    Voters prefer the longer answer much of the time, and notice errors only sometimes."""
    models = {"concise": (120, 0.90), "balanced": (220, 0.86), "verbose": (480, 0.74)}
    rows = []
    names = list(models)
    for i in range(2400):
        a, b = rng.sample(names, 2)
        la, ca = int(rng.gauss(models[a][0], 40)), rng.random() < models[a][1]
        lb, cb = int(rng.gauss(models[b][0], 40)), rng.random() < models[b][1]
        score_a = 0.35 * (la > lb) + (1.0 if ca else 0.0) * 0.6 + rng.random()
        score_b = 0.35 * (lb > la) + (1.0 if cb else 0.0) * 0.6 + rng.random()
        rows.append({"vote": i + 1, "a": a, "b": b, "winner": a if score_a >= score_b else b,
                     "length_a": la, "length_b": lb, "correct_a": ca, "correct_b": cb})
    return rows


TEMPLATES = [
    "A train leaves the station at {h} o'clock travelling at {s} kilometres per hour; how far has it gone after {t} hours",
    "Which organ in the human body produces {x} and what is its main function in the {y} system",
    "In economics, what happens to the equilibrium price of {x} when supply decreases and demand stays the same",
    "Which protocol port is used by {x} by default and why is it considered insecure on public networks",
]
FILL = {"x": ["insulin", "bile", "coffee", "telnet", "ftp", "wheat"], "y": ["digestive", "endocrine"],
        "h": ["6", "7", "9"], "s": ["60", "80", "120"], "t": ["2", "3", "4"]}


def question(rng) -> str:
    t = rng.choice(TEMPLATES)
    return t.format(**{k: rng.choice(v) for k, v in FILL.items()})


def contamination(rng):
    rows, leaked = [], []
    for i in range(150):
        q = f"Question {i + 1}: " + question(rng)
        published = rng.random() < 0.6
        seen = published and rng.random() < 0.7         # published AND scraped into training data
        orig = rng.random() < (0.97 if seen else 0.74)
        para = rng.random() < 0.74
        fresh = rng.random() < 0.72
        rows.append({"item": f"bench-{i + 1:03d}", "question": q, "published_before_training": published,
                     "correct_original": orig, "correct_paraphrase": para, "correct_fresh": fresh})
        if seen:
            leaked.append(q)
    rng.shuffle(leaked)
    filler = ["Top 10 study tips for exams this year.", "Answer key and explanations below, shared by a user.",
              "Thread: does anyone have the full set with solutions?"]
    lines = []
    for q in leaked:
        lines.append(rng.choice(filler))
        lines.append(q + "? Answer: see explanation.")
    return rows, "\n".join(lines) + "\n"


def agent_runs(rng):
    """Browser tasks graded two ways: did the agent follow the ONE expected click path,
    or did it reach the right final state?"""
    rows = []
    expected = ["open_settings", "click_privacy", "toggle_tracking_off", "save"]
    for i in range(60):
        r = rng.random()
        if r < 0.55:
            path, ok, note = expected, True, "followed the expected path"
        elif r < 0.72:
            path, ok, note = ["open_settings", "dismiss_cookie_dialog", "click_privacy", "toggle_tracking_off", "save"], \
                True, "a cookie dialog appeared and was dismissed"
        elif r < 0.85:
            path, ok, note = ["search_settings:tracking", "toggle_tracking_off", "save"], True, \
                "used the settings search: a different path to the same result"
        elif r < 0.93:
            path, ok, note = ["open_settings", "click_privacy", "toggle_tracking_off"], False, "forgot to save"
        else:
            path, ok, note = expected, False, "followed the path, but the page had changed: the toggle did nothing"
        rows.append({"task": f"web-{i + 1:03d}", "expected_path": expected, "actual_path": path,
                     "final_state_ok": ok, "note": note})
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    write_jsonl("mc_results.jsonl", mc_results(random.Random(12)))
    write_jsonl("code_samples.jsonl", code_samples(random.Random(12)))
    write_jsonl("arena_votes.jsonl", arena_votes(random.Random(12)))
    rows, snippets = contamination(random.Random(12))
    write_jsonl("contamination.jsonl", rows)
    (DATA / "training_snippets.txt").write_text(snippets, encoding="utf-8", newline="\n")
    write_jsonl("agent_runs.jsonl", agent_runs(random.Random(12)))
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
