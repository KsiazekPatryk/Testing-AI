"""
test_signal_or_noise.py: unit tests for folder 07.

The reference values come from scipy.stats (not needed to run the folder).

Run:  python -m unittest -v test_signal_or_noise
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stats_tests import (binomial_tail, chi2_sf, chi_square, fisher_exact, load_jsonl, mann_whitney,
                         mcnemar_exact, paired_t, sign_test, t_two_sided_p, welch_t, wilcoxon_signed_rank)

HERE = Path(__file__).parent


class Distributions(unittest.TestCase):
    def test_t_and_chi_square_tails(self):
        self.assertAlmostEqual(t_two_sided_p(2.0, 10), 0.07339, places=4)       # scipy: 0.073388
        self.assertAlmostEqual(chi2_sf(3.84, 1), 0.05004, places=4)             # scipy: 0.050044
        self.assertAlmostEqual(chi2_sf(20.0, 5), 0.00125, places=5)             # scipy: 0.001250


class NumbersFromThePost(unittest.TestCase):
    def test_chi_square_escalations(self):
        res = chi_square([[70, 20, 10], [55, 35, 10]])
        self.assertAlmostEqual(res["chi2"], 5.89, places=2)
        self.assertAlmostEqual(res["p"], 0.053, places=3)
        self.assertEqual(res["expected"][0], [62.5, 27.5, 10.0])

    def test_coins(self):
        self.assertEqual(binomial_tail(15, 20) * 2 ** 20, 21700)
        res = sign_test(15, 5)
        self.assertAlmostEqual(res["p_one_sided"], 0.021, places=3)
        self.assertAlmostEqual(res["p_two_sided"], 0.041, places=3)

    def test_paired_t_on_prompt_eval(self):
        rows = load_jsonl(HERE / "data" / "prompt_eval.jsonl")
        res = paired_t([r["old"] for r in rows], [r["new"] for r in rows])
        self.assertAlmostEqual(res["diff"], 0.5)
        self.assertAlmostEqual(res["p"], 0.0033046, places=6)                   # scipy ttest_rel
        self.assertLess(res["p"], welch_t([r["old"] for r in rows], [r["new"] for r in rows])["p"])


class OtherTests(unittest.TestCase):
    def test_against_scipy(self):
        rows = load_jsonl(HERE / "data" / "prompt_eval.jsonl")
        old, new = [r["old"] for r in rows], [r["new"] for r in rows]
        self.assertAlmostEqual(wilcoxon_signed_rank(old, new)["p"], 0.0051244, places=5)
        ab = load_jsonl(HERE / "data" / "ab_independent.jsonl")
        a = [r["score"] for r in ab if r["version"] == "old"]
        b = [r["score"] for r in ab if r["version"] == "new"]
        self.assertAlmostEqual(welch_t(a, b)["p"], 0.0256483, places=6)          # scipy ttest_ind
        self.assertAlmostEqual(mann_whitney(a, b)["p"], 0.0440148, places=6)     # scipy mannwhitneyu
        self.assertAlmostEqual(fisher_exact([[1, 9], [11, 3]]), 0.0027595, places=6)

    def test_mcnemar_counts_only_disagreements(self):
        res = mcnemar_exact([1, 1, 0, 0, 1], [1, 0, 1, 1, 1])
        self.assertEqual((res["b_fixed"], res["b_broke"]), (2, 1))


class RepeatedRuns(unittest.TestCase):
    def test_significance_disappears_at_prompt_level(self):
        rows = load_jsonl(HERE / "data" / "repeated_runs.jsonl")
        old_all = [r["score"] for r in rows if r["version"] == "old"]
        new_all = [r["score"] for r in rows if r["version"] == "new"]
        self.assertLess(welch_t(old_all, new_all)["p"], 0.05)
        prompts = sorted({r["prompt"] for r in rows})
        def m(p, v):
            vals = [r["score"] for r in rows if r["prompt"] == p and r["version"] == v]
            return sum(vals) / len(vals)
        res = paired_t([m(p, "old") for p in prompts], [m(p, "new") for p in prompts])
        self.assertGreater(res["p"], 0.05)


class Exercise(unittest.TestCase):
    def test_a_clean_win_passes(self):
        import exercise.check_my_win as ex
        spec = {"claim": "B wins",
                "q1_written_before_test": {"hypothesis_written_at": "2026-10-01",
                                           "results_first_seen_at": "2026-10-05",
                                           "metric_chosen_after_seeing_results": False},
                "q2_pairing": {"same_cases_through_both_versions": True, "test_used": "paired t-test"},
                "q3_independent_cases": {"independent_cases": 120, "total_results": 240}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            out = io.StringIO()
            with patch("sys.argv", ["x", str(path)]), contextlib.redirect_stdout(out):
                ex.main()
        self.assertIn("All three answered", out.getvalue())

    def test_the_example_win_is_still_a_hypothesis(self):
        import exercise.check_my_win as ex
        out = io.StringIO()
        with patch("sys.argv", ["x"]), contextlib.redirect_stdout(out):
            ex.main()
        self.assertIn("is, for now, a hypothesis", out.getvalue())


if __name__ == "__main__":
    unittest.main()
