"""
test_score_up.py: unit tests for folder 13.

Run:  python -m unittest -v test_score_up
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evalkit import ci95, diff_packages, fingerprint, load_json, load_jsonl, ndcg

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class NumbersFromThePost(unittest.TestCase):
    def test_ndcg_orders(self):
        expected = {(3, 2, 1, 0): 1.00, (3, 2, 0, 1): 0.99, (2, 3, 1, 0): 0.92, (1, 0, 2, 3): 0.69, (0, 1, 2, 3): 0.61}
        for order, value in expected.items():
            self.assertAlmostEqual(round(ndcg(list(order)), 2), value, msg=str(order))

    def test_score_78_to_86(self):
        import score_went_up as s
        rows = load_jsonl(HERE / "data" / "search_eval.jsonl")
        p, t = s.score(rows, s.SETTINGS["search-eval-v14"])
        self.assertEqual(round(100 * p / t), 78)
        p, t = s.score(rows, s.SETTINGS["search-eval-v15"])
        self.assertEqual(round(100 * p / t), 86)
        self.assertEqual(t, 108)

    def test_record_is_8_6(self):
        import record_is_a_lead as r
        scores = [s for _, s in r.run_log(20, 27)]
        self.assertEqual(max(scores), 8.6)
        self.assertAlmostEqual(sum(scores) / 20, 8.0, places=1)


class Packages(unittest.TestCase):
    def test_diff_finds_no_product_change(self):
        p = load_json(HERE / "data" / "packages.json")["packages"]
        d = diff_packages(p["search-eval-v14"], p["search-eval-v15"])
        self.assertEqual(d["product"], [])
        self.assertIn("judge", d["measurement"])
        self.assertNotEqual(fingerprint(p["search-eval-v14"]), fingerprint(p["search-eval-v15"]))

    def test_ci(self):
        lo, hi = ci95([8.0, 8.2, 7.9, 8.1])
        self.assertAlmostEqual((lo + hi) / 2, 8.05)
        self.assertAlmostEqual(hi - lo, 2 * 3.18 * 0.1290994 / 2, places=3)


class RedTeam(unittest.TestCase):
    def test_refuses_unapproved_environment(self):
        out = run(__import__("red_team").main, ["x", "--env", "production"])
        self.assertIn("Not running", out)
        self.assertNotIn("RED-TEAM VIEW", out)

    def test_v3_regression(self):
        out = run(__import__("red_team").main, ["x", "--version", "v2"])
        self.assertIn("came back: rp-01, pa-02, ag-02", out)
        self.assertIn("no critical bypass", out)


class Exercise(unittest.TestCase):
    def test_example(self):
        import exercise.check_my_score_change as ex
        out = run(ex.main)
        self.assertIn("'new ranking' is not in the product manifest", out)
        self.assertIn("the increase is entirely the instrument", out)

    def test_product_only(self):
        import exercise.check_my_score_change as ex
        spec = {"dashboard": "d", "score_before": 1, "score_after": 2, "product_changes": ["prompt v23"],
                "measurement_changes": []}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.json"
            p.write_text(json.dumps(spec), encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("only the product changed", out)


if __name__ == "__main__":
    unittest.main()
