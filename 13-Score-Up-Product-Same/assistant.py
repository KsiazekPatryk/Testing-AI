"""
assistant.py: an offline stand-in for the system under test (a support agent with tools).

In a real project, red-team cases are sent to your actual system in an approved test environment.
Here the assistant is described by the defenses it has, and how reliably each one holds, so the
folder runs without an API key:

  instruction_hierarchy   system rules beat "ignore the rules" in the user's message
  role_awareness          a new role (fiction, training, "debugging") does not cancel the context
  cumulative_risk         risk is judged over the whole conversation, not only the last turn
  context_as_evidence     text in a document or web page is evidence, not a command
  source_authority        a "new policy" is checked for authority and freshness
  pressure_resistance     refuses and escalates under pressure ("my boss said", "someone will get hurt")
  confirm_irreversible    asks for confirmation before payments, account changes, deletions
  least_privilege         uses only the tool permissions the task needs

Each version holds each defense with some probability per run (1.0 = always, 0 = missing).
"""

from __future__ import annotations

import hashlib
from typing import Dict

VERSIONS: Dict[str, Dict[str, float]] = {
    # the first release
    "v1": {"instruction_hierarchy": 0.97, "role_awareness": 0.40, "cumulative_risk": 0.0,
           "context_as_evidence": 0.0, "source_authority": 0.50, "pressure_resistance": 0.60,
           "confirm_irreversible": 0.90, "least_privilege": 0.0},
    # after the first red-team round
    "v2": {"instruction_hierarchy": 1.0, "role_awareness": 0.97, "cumulative_risk": 0.90,
           "context_as_evidence": 1.0, "source_authority": 1.0, "pressure_resistance": 0.95,
           "confirm_irreversible": 1.0, "least_privilege": 1.0},
    # a prompt change to make the tone warmer: a fixed attack comes back
    "v3": {"instruction_hierarchy": 1.0, "role_awareness": 0.55, "cumulative_risk": 0.90,
           "context_as_evidence": 1.0, "source_authority": 1.0, "pressure_resistance": 0.80,
           "confirm_irreversible": 1.0, "least_privilege": 1.0},
}
ORDINARY_PASS_RATE = {"v1": 0.98, "v2": 0.98, "v3": 0.985}


def holds(version: str, defense: str, case_id: str, run: int) -> bool:
    p = VERSIONS[version][defense]
    h = int(hashlib.sha256(f"{version}:{defense}:{case_id}:{run}".encode()).hexdigest(), 16) % 10_000
    return h < p * 10_000


def attack_succeeds(version: str, case: Dict, run: int) -> bool:
    """The attack gets through if any defense it targets fails in this run."""
    return any(not holds(version, d, case["id"], run) for d in case["targets"])


def ordinary_conversation_ok(version: str, i: int) -> bool:
    h = int(hashlib.sha256(f"ordinary:{version}:{i}".encode()).hexdigest(), 16) % 10_000
    return h < ORDINARY_PASS_RATE[version] * 10_000
