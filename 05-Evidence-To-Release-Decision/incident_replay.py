"""
incident_replay.py: without logs, failures turn into arguments.

Run:  python incident_replay.py

"The model answered wrong." "Works for me." This script plays out that exchange with a
local, fake support agent, then shows the way out:

  1. The customer's run fails. The engineer's run on a clean machine works.
  2. With an answer-only log, nobody can explain why.
  3. With a full context log, another engineer replays the run and sees the same class
     of failure, and the log shows which field explains it.
  4. Test with a clean state, then with a dirty one: memory, a stale tool cache,
     an earlier failed attempt.

Reproducibility here does not mean generating an identical answer. It means recording
enough context to explain the failure.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).parent
OUTPUT = HERE / "output"

SYSTEM_PROMPT_VERSION = "support-prompt-v3"
MODEL = {"name": "local-fake-agent", "version": "2026-10", "temperature": 0.2, "top_p": 0.9, "seed": 42}
QUESTION = "Can I still return the boots I bought 45 days ago?"

CURRENT_POLICY = {"doc_id": "returns-policy", "version": "2026-10-01",
                  "text": "Shoes can be returned within 30 days of purchase."}
STALE_POLICY = {"doc_id": "returns-policy", "version": "2025-11-01",
                "text": "Holiday rule: shoes bought in November and December can be returned within 60 days."}


def clean_state() -> Dict:
    return {"memory": [], "tool_cache": {}, "feature_flags": {"use_tool_cache": True}}


def dirty_state(stale_cache: bool = True, failed_attempt: bool = True) -> Dict:
    state = clean_state()
    if stale_cache:
        state["tool_cache"]["get_policy"] = {"result": STALE_POLICY, "cached_at": "2025-12-03T10:12:00Z"}
    if failed_attempt:
        state["memory"].append("Earlier attempt failed: policy tool timed out, agent apologised.")
    return state


# --- The agent ------------------------------------------------------------------

def get_policy(state: Dict, trace: List[Dict]) -> Dict:
    cached = state["tool_cache"].get("get_policy")
    if cached and state["feature_flags"].get("use_tool_cache"):
        trace.append({"tool": "get_policy", "cache_hit": True, "cached_at": cached["cached_at"],
                      "result_version": cached["result"]["version"]})
        return cached["result"]
    trace.append({"tool": "get_policy", "cache_hit": False, "result_version": CURRENT_POLICY["version"]})
    state["tool_cache"]["get_policy"] = {"result": CURRENT_POLICY, "cached_at": "2026-10-20T09:00:00Z"}
    return CURRENT_POLICY


def run_agent(question: str, state: Dict) -> Tuple[str, List[Dict], Dict]:
    """Returns (answer, tool trace, retrieved policy document)."""
    trace: List[Dict] = []
    policy = get_policy(state, trace)
    window = int(re.search(r"(\d+) days", policy["text"]).group(1))
    days = int(re.search(r"(\d+) days", question).group(1))
    apology = "Sorry again for the trouble earlier. " if state["memory"] else ""
    if days <= window:
        answer = f"{apology}Yes, you can return them: our window is {window} days."
    else:
        answer = f"{apology}Our window is {window} days, so {days} days is too late."
    return answer, trace, policy


def judge(answer: str) -> Tuple[int, str]:
    if "30 days" in answer and "too late" in answer:
        return 9, "Correct policy (30 days) and correct verdict."
    return 1, "Wrong policy: the current return window is 30 days."


# --- Two kinds of logs ----------------------------------------------------------

def answer_only_log(answer: str) -> Dict:
    return {"timestamp": "2026-10-20T09:14:03Z", "answer": answer}


def full_log(question: str, state_before: Dict, answer: str, trace: List[Dict], policy: Dict) -> Dict:
    score, reason = judge(answer)
    return {
        "timestamp": datetime(2026, 10, 20, 9, 14, 3, tzinfo=timezone.utc).isoformat(),
        "user_input": question,
        "system_prompt_version": SYSTEM_PROMPT_VERSION,
        "developer_prompt_version": "returns-flow-v2",
        "model": MODEL,
        "retrieved_documents": [{"doc_id": policy["doc_id"], "version": policy["version"]}],
        "tool_calls": trace,
        "state": {"memory": state_before["memory"], "tool_cache": state_before["tool_cache"]},
        "feature_flags": state_before["feature_flags"],
        "config": {"policy_tool_timeout_s": 3, "cache_ttl_days": 365},
        "output": answer,
        "judge": {"score": score, "reason": reason},
    }


def replay(log: Dict) -> Tuple[str, List[Dict]]:
    """Another engineer rebuilds the run from the log alone."""
    state = {"memory": copy.deepcopy(log["state"]["memory"]),
             "tool_cache": copy.deepcopy(log["state"]["tool_cache"]),
             "feature_flags": copy.deepcopy(log["feature_flags"])}
    answer, trace, _ = run_agent(log["user_input"], state)
    return answer, trace


def explain(log: Dict) -> List[str]:
    """Which logged fields explain the failure?"""
    reasons = []
    for call in log["tool_calls"]:
        if call.get("cache_hit") and call["result_version"] != CURRENT_POLICY["version"]:
            reasons.append(f"tool_calls: {call['tool']} came from cache (cached_at {call['cached_at']}), "
                           f"policy version {call['result_version']} instead of {CURRENT_POLICY['version']}")
    if log["state"]["memory"]:
        reasons.append(f"state.memory: {log['state']['memory'][0]}")
    return reasons


def header(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main() -> None:
    header("1. THE ARGUMENT")
    customer_state = dirty_state()
    state_before = copy.deepcopy(customer_state)
    customer_answer, trace, policy = run_agent(QUESTION, customer_state)
    print(f"Customer:  {QUESTION}")
    print(f"Agent (customer's session): {customer_answer}")
    print(f"  judge: {judge(customer_answer)[0]}/10, {judge(customer_answer)[1]}")
    engineer_answer, _, _ = run_agent(QUESTION, clean_state())
    print(f"Agent (engineer, clean machine): {engineer_answer}")
    print(f"  judge: {judge(engineer_answer)[0]}/10")
    print("\n\"The model answered wrong.\" \"Works for me.\" Two stories, no facts.")

    header("2. ANSWER-ONLY LOG")
    print(json.dumps(answer_only_log(customer_answer), indent=2))
    print("It confirms the wrong answer. It cannot say why.")

    header("3. FULL CONTEXT LOG")
    log = full_log(QUESTION, state_before, customer_answer, trace, policy)
    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / "incident_full_log.json"
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {path.relative_to(HERE)}")
    replayed, _ = replay(json.loads(path.read_text(encoding="utf-8")))
    print(f"Another engineer replays it from the log alone: {replayed}")
    same_class = judge(replayed)[0] == judge(customer_answer)[0]
    print(f"Same class of failure reproduced: {'yes' if same_class else 'no'}")
    print("What explains it:")
    for reason in explain(log):
        print(f"  - {reason}")
    print("The prompt shows what instructions the model got. The retrieved documents show what")
    print("evidence it saw. The tool results show that it relied on stale data.")

    header("4. TEST WITH A CLEAN STATE, THEN WITH A DIRTY ONE")
    matrix = [
        ("clean state", clean_state()),
        ("earlier failed attempt in memory", dirty_state(stale_cache=False, failed_attempt=True)),
        ("stale policy in the tool cache", dirty_state(stale_cache=True, failed_attempt=False)),
        ("both", dirty_state()),
    ]
    for name, state in matrix:
        answer, _, _ = run_agent(QUESTION, state)
        score, _ = judge(answer)
        print(f"  [{'PASS' if score >= 7 else 'FAIL'}] {name:34} {answer}")
    print("\nThe lab (clean state) never sees this bug. Real users, with their memory and caches, do.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
