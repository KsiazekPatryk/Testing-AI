"""
run_manifest.py: record the shape of the system under test, not just the model name.

Run:  python run_manifest.py

Every engineering change is a test surface: the prompt, the context window, retrieval, the
reranker, the model route, the tool schema, the cache, the safety filter. So every evaluation run
records the system's shape:
  model provider and version, prompt and policy pack, context building, retrieval method and index
  version, output schema, tools with their permissions, cache and limits, judge, rubric, release gate.

Two runs of "the same model" are compared below. The score moved; the manifest shows why,
and refuses a comparison where something changed that nobody wrote down.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).parent
FIELDS = ["model_provider", "model_version", "prompt_version", "policy_pack", "context_builder",
          "retrieval_method", "index_version", "reranker", "output_schema", "tools", "cache",
          "limits", "safety_filter", "judge", "rubric", "release_gate"]

RUN_1 = {
    "run": "2026-11-03", "score": 0.84,
    "model_provider": "vendor-x", "model_version": "x-large-2026-10", "prompt_version": "support-v14",
    "policy_pack": "returns-2026-09", "context_builder": "last 6 turns + order summary",
    "retrieval_method": "hybrid bm25 + embeddings", "index_version": "kb-2026-10-28", "reranker": "rr-small-v2",
    "output_schema": "reply+actions v3", "tools": {"lookup_order": "read", "issue_refund": "propose_only"},
    "cache": "semantic cache, 24h", "limits": {"max_tokens": 600, "timeout_s": 20}, "safety_filter": "sf-1.4",
    "judge": "judge-v2", "rubric": "support-rubric-v2", "release_gate": "no blockers, score >= 0.80",
    "documented_changes": {},
}
RUN_2 = dict(RUN_1, run="2026-11-12", score=0.79, index_version="kb-2026-11-10", reranker="rr-small-v3",
             cache="semantic cache, 72h", documented_changes={"index_version": "new knowledge base export"})


def fingerprint(run: Dict) -> str:
    shape = {k: run[k] for k in FIELDS}
    return hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()[:12]


def diff(a: Dict, b: Dict) -> List[str]:
    return [k for k in FIELDS if a[k] != b[k]]


def main() -> None:
    print("=" * 78 + "\nTWO RUNS OF 'THE SAME MODEL'\n" + "=" * 78)
    for r in (RUN_1, RUN_2):
        print(f"  {r['run']}: model {r['model_version']}, score {r['score']:.0%}, system fingerprint {fingerprint(r)}")
    changed = diff(RUN_1, RUN_2)
    print(f"\n  Same model name, different system. {len(changed)} fields changed:")
    for k in changed:
        print(f"    {k:16} {RUN_1[k]}  ->  {RUN_2[k]}")
    documented = [k for k in changed if k in RUN_2["documented_changes"]]
    undocumented = [k for k in changed if k not in documented]
    print("\n  Documented in the run: " + (", ".join(f"{k} ({RUN_2['documented_changes'][k]})" for k in documented) or "nothing"))
    if undocumented:
        print(f"  Not explained: {', '.join(undocumented)}")
        print("  The score drop cannot be blamed on the knowledge base alone: the reranker and the cache")
        print("  changed too. Re-run with one change at a time before drawing a conclusion.")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    manifest = {k: RUN_2[k] for k in ["run", "score"] + FIELDS + ["documented_changes"]}
    manifest["fingerprint"] = fingerprint(RUN_2)
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\n  Manifest of the latest run written to {out / 'run_manifest.json'}")
    print("  Keep one next to every evaluation result. 'Model X scored 84%' is not a reproducible claim.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
