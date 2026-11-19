"""
check_my_score_change.py: the exercise from the post.

"Take the last score increase on your evaluation dashboard and write two lists: what changed in the
 product, and what changed in the measuring instrument (dataset, labels, rubric, judge, data).
 If the second list is not empty, the increase needs to be re-checked on a comparable package."

Run:  python exercise/check_my_score_change.py
      python exercise/check_my_score_change.py path/to/your_score_change.json

Write the two lists by hand. If you also have the evaluation package manifests (JSON, one object
per package), point 'packages' to them: the script compares your lists with the actual diff.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from evalkit import MEASUREMENT_FIELDS, diff_packages  # noqa: E402

DEFAULT_FILE = HERE / "my_score_change.json"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    spec = json.loads(path.read_text(encoding="utf-8"))
    product = list(spec.get("product_changes") or [])
    measurement = list(spec.get("measurement_changes") or [])
    print(f"{spec.get('dashboard', 'Dashboard')}: {spec.get('score_before')} -> {spec.get('score_after')}")
    if spec.get("what_the_team_believes"):
        print(f"The team believes: {spec['what_the_team_believes']}\n")

    print("Your lists:")
    print(f"  changed in the product:     {', '.join(product) or '(empty)'}")
    print(f"  changed in the measurement: {', '.join(measurement) or '(empty)'}")

    pk = spec.get("packages")
    if pk and pk.get("file"):
        packages = json.loads((path.parent / pk["file"]).read_text(encoding="utf-8"))
        packages = packages.get("packages", packages)
        d = diff_packages(packages[pk["before"]], packages[pk["after"]])
        print(f"\nThe package manifests ({pk['before']} -> {pk['after']}) say:")
        print(f"  changed in the product:     {', '.join(d['product']) or 'nothing'}")
        print(f"  changed in the measurement: {', '.join(d['measurement']) or 'nothing'}")
        if product and not d["product"]:
            print(f"  -> '{', '.join(product)}' is not in the product manifest: nothing was deployed.")
        missed = [m for m in d["measurement"] if m not in measurement]
        if missed:
            print(f"  -> missing from your measurement list: {', '.join(missed)}")
        measurement = sorted(set(measurement) | set(d["measurement"]))
        product = d["product"]

    unknown = [m for m in measurement if m not in MEASUREMENT_FIELDS]
    print()
    if measurement:
        print(f"Verdict: the measurement changed ({len(measurement)} item{'s' if len(measurement) > 1 else ''}). "
              "This increase needs to be re-checked")
        print("on a comparable package: run the old and the new product on the SAME dataset, labels, rubric,")
        print("judge and data, and compare those two numbers.")
        if not product:
            print("No product change at all: the increase is entirely the instrument.")
    elif product:
        print("Verdict: only the product changed. The increase can be read as a product change,")
        print("within the run-to-run noise (report all runs, not the best one).")
    else:
        print("Verdict: nothing listed changed. Then the increase is noise until a re-run shows otherwise.")
    if unknown:
        print(f"(Unrecognized measurement items kept as written: {', '.join(unknown)})")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
