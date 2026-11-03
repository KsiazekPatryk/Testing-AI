"""
test_significance.py: unit tests for folder 08.

Reference values come from scipy.stats (not needed to run the folder) and from the post.

Run:  python -m unittest -v test_significance
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stats_tools import (benjamini_hochberg, f_beta, fisher_exact, holm, load_jsonl, n_paired_means,
                         n_per_group_proportions, p_any_false_alarm, power_paired_means, precision_recall,
                         two_proportions)

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class NumbersFromThePost(unittest.TestCase):
    def test_refund_headline(self):
        rows = load_jsonl(HERE / "data" / "refund_policy.jsonl")
        old = [r for r in rows if r["version"] == "old"]
        new = [r for r in rows if r["version"] == "new"]
        res = two_proportions(sum(r["auto_refund"] for r in old), len(old), sum(r["auto_refund"] for r in new), len(new))
        self.assertAlmostEqual(res["p1"], 0.18)
        self.assertAlmostEqual(res["p2"], 0.14)
        self.assertAlmostEqual(res["p"], 0.003, places=3)

    def test_sample_sizes(self):
        self.assertTrue(430 <= n_per_group_proportions(0.10, 0.05) <= 520)       # "about 500"
        self.assertGreater(n_per_group_proportions(0.01, 0.005), 4500)           # "over 4500"

    def test_many_comparisons(self):
        self.assertAlmostEqual(p_any_false_alarm(100), 0.994, places=3)

    def test_precision_recall_f(self):
        pr = precision_recall(40, 10, 20)
        p, r = pr["precision"], pr["recall"]
        self.assertAlmostEqual(p, 0.80)
        self.assertAlmostEqual(r, 0.667, places=3)
        self.assertAlmostEqual(f_beta(p, r, 0.5), 0.77, places=2)
        self.assertAlmostEqual(f_beta(p, r, 1), 0.73, places=2)
        self.assertAlmostEqual(f_beta(p, r, 2), 0.69, places=2)

    def test_bug_detector_at_half(self):
        from precision_recall import counts
        self.assertEqual(counts(load_jsonl(HERE / "data" / "bug_findings.jsonl"), 0.5), (40, 10, 20, 30))


class AgainstScipy(unittest.TestCase):
    def test_fisher(self):
        self.assertAlmostEqual(fisher_exact(6, 54, 4, 56), 0.7430121, places=6)
        self.assertAlmostEqual(fisher_exact(6, 94, 2, 98), 0.2790433, places=6)
        self.assertAlmostEqual(fisher_exact(3, 9, 11, 2), 0.0048324, places=6)


class Power(unittest.TestCase):
    def test_power_grows_with_n(self):
        self.assertLess(power_paired_means(0.3, 1.2, 40), 0.5)
        self.assertGreater(power_paired_means(0.3, 1.2, n_paired_means(0.3, 1.2)), 0.8)


class Corrections(unittest.TestCase):
    def test_holm_and_bh(self):
        p = [0.001, 0.01, 0.02, 0.04, 0.3]
        self.assertEqual(holm(p), [True, True, False, False, False])
        self.assertEqual(benjamini_hochberg(p), [True, True, True, True, False])

    def test_agent_winner_does_not_hold_up(self):
        rows = load_jsonl(HERE / "data" / "agent_search.jsonl")
        conf = json.loads((HERE / "data" / "agent_confirm.json").read_text(encoding="utf-8"))
        best = max((r for r in rows if not r["production"]), key=lambda r: r["passed"])
        self.assertEqual(best["passed"] / best["tasks"], 0.91)
        self.assertEqual(sum(1 for r in rows if not r["production"]), 200)
        self.assertLessEqual(sum(conf["winner"]["fresh_runs_passed"]), sum(conf["production"]["fresh_runs_passed"]))


class Exercise(unittest.TestCase):
    def test_example_is_too_weak(self):
        import exercise.check_my_comparison as ex
        out = run(ex.main)
        self.assertIn("TOO WEAK", out)
        self.assertIn("You need about 128 cases", out)

    def test_a_ready_plan(self):
        import exercise.check_my_comparison as ex
        spec = {"comparison": "A vs B", "test": {"name": "McNemar", "why": "same cases, pass/fail"},
                "assumption": "cases independent, paired", "decision": "replace A with B",
                "minimum_effect": {"metric": "failure rate", "kind": "rate", "value": 0.5, "current_rate": 0.10},
                "sample": {"independent_cases": 600, "paired": True, "runs_per_case": 5},
                "high_risk_slices_checked": ["vip"], "cannot_tell": ["cost"]}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.json"
            p.write_text(json.dumps(spec), encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("The plan is ready", out)


if __name__ == "__main__":
    unittest.main()
