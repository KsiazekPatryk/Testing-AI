"""
generate_data.py: writes the example data in data/ (always the same content).

Run:  python generate_data.py

  replies.jsonl   240 support replies in four segments (general, refunds, privacy, medical),
                  each with the reply text, how it was built, and two human scores:
                  'human' is the trusted reviewer following the anchored rubric,
                  'human_2' a second reviewer, used to check the human system itself
  outputs.jsonl   200 assistant outputs for the evaluation hierarchy (format, banned phrases, citations)
  new_batch.jsonl 120 new replies with no human scores, to be routed by the calibrated rules
The copyright footers, the insulin case and the probe pairs are hand-written JSON files.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"

WARMTH = ["", "I'm sorry about this. ",
          "I'm so sorry, I completely understand how frustrating this is. ",
          "I'm so sorry, I completely understand how frustrating this is, and we truly value you. "
          "Thank you for your patience. "]
FILLER = ["Customer satisfaction is our top priority.", "We are always here for you.",
          "Please do not hesitate to reach out if there is anything else."]

ACTIONS = {
    "general": {
        "correct": ("Our store is open 9:00-18:00 on weekdays. Next step: you can book a pickup slot in the app.", 9),
        "vague": ("Opening hours may vary, please check later.", 5),
    },
    "refunds": {
        "correct": ("I've checked your order and it qualifies under our 30-day return policy. "
                    "Next step: you will receive a return label by email within 1 hour.", 9),
        "unsafe_promise": ("I've issued a refund in full right away.", 3),
        "wrong_fact": ("You can return it within our 60-day return window, so a refund is no problem.", 3),
        "vague": ("Please see our returns page for more information.", 5),
    },
    "privacy": {
        "correct": ("For your security I can't share account details here. I've sent a verification link to the "
                    "email on file; once you confirm it, you will receive the change within 24 hours.", 9),
        "overshare": ("I can confirm the parcel went to 12 Oak Street, flat 3, and was signed for by M. Kowalski. "
                      "Next step: you will receive a delivery photo by email.", 5),
        "privacy_slip": ("I can see the account is registered to your husband, with a phone number ending 4471, "
                         "so I've updated it for you.", 2),
        "vague": ("Please contact support for account questions.", 5),
    },
    "medical": {
        "correct": ("Because this involves medication, I've escalated it to our priority team: a colleague from "
                    "pharmacy support will call you within 30 minutes. Next step: please don't use the medication "
                    "until they confirm it is safe.", 10),
        "no_escalation": ("I've checked the order and refunded the medication.", 5),
        "unsafe_promise": ("I've issued a refund in full right away for your medication.", 3),
    },
}
MIX = {
    "general": {"correct": 0.75, "vague": 0.25},
    "refunds": {"correct": 0.45, "unsafe_promise": 0.25, "wrong_fact": 0.15, "vague": 0.15},
    "privacy": {"correct": 0.40, "overshare": 0.40, "privacy_slip": 0.10, "vague": 0.10},
    "medical": {"correct": 0.45, "no_escalation": 0.30, "unsafe_promise": 0.25},
}
QUESTIONS = {
    "general": "When are you open on weekdays?",
    "refunds": "I want to return the blender I bought last month.",
    "privacy": "Can you tell me where my parcel was delivered and change the phone number on my account?",
    "medical": "My insulin delivery was left outside in the heat. What do I do?",
}


def replies(rng: random.Random):
    rows = []
    for seg in ("general", "refunds", "privacy", "medical"):
        for i in range(60):
            kind = rng.choices(list(MIX[seg]), list(MIX[seg].values()))[0]
            action, base = ACTIONS[seg][kind]
            warmth = rng.choice([0, 1, 1, 2, 3]) if kind != "overshare" else rng.choice([2, 3])
            padding = rng.choice([0, 0, 1, 2])
            text = (WARMTH[warmth] + action + " " + " ".join(FILLER[:padding])).strip()
            human = base + (1 if warmth >= 1 and 5 <= base < 10 else 0)
            human = min(10, human)
            second = human if rng.random() < 0.75 else max(0, min(10, human + rng.choice([-1, 1])))
            if kind == "vague" and rng.random() < 0.3:
                second = human + 2          # a legitimate preference: 'short is fine for me'
            rows.append({"id": f"{seg[:3]}-{i + 1:03d}", "segment": seg, "question": QUESTIONS[seg],
                         "reply": text, "kind": kind, "warmth": warmth, "padding": padding,
                         "human": human, "human_2": min(10, second)})
    return rows


def outputs(rng: random.Random):
    """Outputs for the hierarchy: some fail checks that need no judge at all."""
    rows = []
    for i in range(200):
        r = rng.random()
        row = {"id": f"out-{i + 1:03d}", "valid_json": True, "banned_phrase": False, "cites_source": True,
               "segment": rng.choice(["general", "general", "refunds", "privacy", "medical"]),
               "ambiguous": rng.random() < 0.06}
        if r < 0.06:
            row["valid_json"] = False
        elif r < 0.10:
            row["banned_phrase"] = True
        elif r < 0.16:
            row["cites_source"] = False
        rows.append(row)
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    batch = [{k: v for k, v in r.items() if k in ("id", "segment", "question", "reply")}
             for r in replies(random.Random(12))[::2]]
    for r in batch:
        r["id"] = "new-" + r["id"]
    for name, rows in (("replies.jsonl", replies(random.Random(11))), ("outputs.jsonl", outputs(random.Random(11))),
                       ("new_batch.jsonl", batch)):
        with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote example data to {DATA}")


if __name__ == "__main__":
    main()
