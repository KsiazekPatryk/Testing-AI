"""
add_uncertainty.py: the exercise from the post.

"Pick one metric you report today as a single number and add uncertainty to it:
   1. How many examples are behind that number?
   2. What is the spread: median, minimum, standard deviation?
   3. What is the approximate 95% confidence interval?
   4. Which single slice is the riskiest, and how does it score on its own?"

Run:  python exercise/add_uncertainty.py
      python exercise/add_uncertainty.py path/to/your_metric.json

The script answers the four questions for your metric and rewrites the single number
as an honest sentence. It saves the result to output/my_metric_with_uncertainty.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from stats import load_jsonl, mean_ci, wilson  # noqa: E402

DEFAULT_FILE = HERE / "my_metric.json"
MIN_SLICE = 30


def load_results(spec: Dict, base: Path) -> List[Tuple[float, Optional[str]]]:
    if "values" in spec:
        return [(float(v), None) for v in spec["values"]]
    rows = load_jsonl((base / spec["results"]).resolve())
    field, slice_field = spec.get("value_field", "value"), spec.get("slice_field")
    return [(float(r[field]), r.get(slice_field) if slice_field else None) for r in rows]


def estimate(values: List[float], kind: str) -> Tuple[float, float, float]:
    if kind == "pass_rate":
        k = int(sum(values))
        lo, hi = wilson(k, len(values))
        return k / len(values), lo, hi
    return mean_ci(values)


def fmt(x: float, kind: str) -> str:
    return f"{x:.0%}" if kind == "pass_rate" else f"{x:.1f}"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    kind = spec.get("kind", "score")
    results = load_results(spec, path.parent)
    values = [v for v, _ in results]
    n = len(values)
    est, lo, hi = estimate(values, kind)
    lines: List[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say(f"# {spec['metric']}")
    say(f"\nReported today: \"{spec.get('reported_today', fmt(est, kind))}\"")

    say(f"\n## 1. How many examples are behind that number?\n\n{n}")
    if n < 30:
        say("That is a small sample: treat the number as a rough, directional read.")

    say("\n## 2. What is the spread?\n")
    if kind == "pass_rate":
        say(f"{int(sum(values))} passed, {n - int(sum(values))} failed.")
    else:
        fail_below = spec.get("fail_below")
        fails = sum(v < fail_below for v in values) if fail_below is not None else None
        say(f"median {median(values):.1f}, minimum {min(values):.0f}, standard deviation "
            f"{stdev(values) if n > 1 else 0:.1f}" +
            (f", failure rate {fails / n:.0%} (score below {fail_below})" if fails is not None else ""))

    method = "Wilson" if kind == "pass_rate" else ("mean ± t × SE, small sample" if n < 31 else "mean ± 1.96 × SE")
    say(f"\n## 3. What is the approximate 95% confidence interval?\n\n{fmt(lo, kind)}–{fmt(hi, kind)} "
        f"({method} method)")

    say("\n## 4. Which slice is the riskiest, and how does it score on its own?\n")
    slices: Dict[str, List[float]] = {}
    for v, s in results:
        if s is not None:
            slices.setdefault(s, []).append(v)
    worst = None
    if slices:
        worst = min(slices, key=lambda s: mean(slices[s]))
        w_est, w_lo, w_hi = estimate(slices[worst], kind)
        for s, vals in sorted(slices.items(), key=lambda x: mean(x[1])):
            s_est, s_lo, s_hi = estimate(vals, kind)
            marker = "  <- riskiest" if s == worst else ""
            ci = f"{fmt(s_lo, kind)}–{fmt(s_hi, kind)}" if len(vals) > 1 else "n/a"
            say(f"- {s}: {fmt(s_est, kind)} (n = {len(vals)}, 95% CI {ci}){marker}")
    else:
        say("No slice field given. Add one (language, topic, risk level): the average hides weak slices.")

    say("\n## The honest sentence\n")
    sentence = (f"\"{spec['metric']}: {fmt(est, kind)} on {n} examples "
                f"(approximate 95% CI {fmt(lo, kind)}–{fmt(hi, kind)})")
    if worst is not None:
        sentence += f"; the weakest slice, {worst}, scores {fmt(w_est, kind)} on its own"
    sentence += ".\""
    say(sentence)
    if worst is not None and len(slices[worst]) < MIN_SLICE:
        say(f"\nMore honest still: \"It's probably fine overall, but we need more data on {worst}: "
            f"only {len(slices[worst])} examples, so its interval is wide.\" And that is okay.")

    out = ROOT / "output" / "my_metric_with_uncertainty.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
