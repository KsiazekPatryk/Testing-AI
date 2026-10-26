"""
test_uncertainty.py: unit tests for folder 06.

Run:  python -m unittest -v test_uncertainty
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from calibration import brier, ece
from perplexity_vs_product import cross_entropy
from stats import load_jsonl, mean_ci, multiplier, paired_difference_ci, percentile, proportion_ci, wilson

HERE = Path(__file__).parent


class Formulas(unittest.TestCase):
    def test_numbers_from_the_post(self):
        _, lo, hi = proportion_ci(92, 100)
        self.assertEqual((round(lo, 3), round(hi, 3)), (0.867, 0.973))
        margin = 1.96 * 1.4 / 10
        self.assertAlmostEqual(margin, 0.27, places=2)

    def test_small_samples_use_a_bigger_multiplier(self):
        self.assertGreater(multiplier(5), 1.96)
        self.assertEqual(multiplier(200), 1.96)

    def test_wilson_handles_100_percent(self):
        lo, hi = wilson(10, 10)
        self.assertLess(lo, 0.8)
        self.assertEqual(hi, 1.0)

    def test_percentile_matches_spreadsheet(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertAlmostEqual(percentile([1, 2, 3, 4], 95), 3.85)

    def test_more_data_narrows_the_interval(self):
        _, lo1, hi1 = mean_ci([7, 9, 8, 6, 10] * 4)
        _, lo2, hi2 = mean_ci([7, 9, 8, 6, 10] * 40)
        self.assertLess(hi2 - lo2, hi1 - lo1)


class Data(unittest.TestCase):
    def test_delivery_delays_have_a_long_tail(self):
        delays = [r["delay_min"] for r in load_jsonl(HERE / "data" / "delivery_delays.jsonl")]
        self.assertLess(percentile(delays, 50), 3)
        self.assertGreater(percentile(delays, 95), 40)

    def test_paired_comparison(self):
        rows = load_jsonl(HERE / "data" / "version_pairs.jsonl")
        a = [r["a"] for r in rows]
        _, lo, hi = paired_difference_ci(a, [r["b_prompt_tweak"] for r in rows])
        self.assertTrue(lo < 0 < hi)
        _, lo, _ = paired_difference_ci(a, [r["b_retrieval_fix"] for r in rows])
        self.assertGreater(lo, 0)

    def test_calibration_is_local(self):
        rows = load_jsonl(HERE / "data" / "judge_confidence.jsonl")
        en = [r for r in rows if r["judge"] == "calibrated" and r["language"] == "en"]
        pl = [r for r in rows if r["judge"] == "calibrated" and r["language"] == "pl"]
        self.assertLess(ece(en)[0], ece(pl)[0])
        self.assertLess(brier(en), brier(pl))

    def test_lower_perplexity_model(self):
        self.assertLess(cross_entropy([0.6, 0.6]), cross_entropy([0.3, 0.3]))


class Exercise(unittest.TestCase):
    def test_pass_rate_metric_without_slices(self):
        import exercise.add_uncertainty as ex
        spec = {"metric": "Refund flow", "kind": "pass_rate", "values": [1] * 46 + [0] * 4}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            with patch("sys.argv", ["x", str(path)]), patch.object(ex, "ROOT", Path(tmp)), \
                    contextlib.redirect_stdout(io.StringIO()):
                ex.main()
            text = (Path(tmp) / "output" / "my_metric_with_uncertainty.md").read_text(encoding="utf-8")
        self.assertIn("92% on 50 examples", text)
        self.assertIn("Wilson", text)


if __name__ == "__main__":
    unittest.main()
