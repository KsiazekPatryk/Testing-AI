"""
test_disagreement.py: unit tests for folder 10.

Reference values come from the post, scikit-learn (Cohen's kappa) and the `krippendorff` package
(Krippendorff's alpha). Neither package is needed to run the folder.

Run:  python -m unittest -v test_disagreement
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agreement import (agreement_pattern, cohen_kappa, entropy, kappa_from_table, krippendorff_alpha,
                       load_json, load_jsonl)

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class NumbersFromThePost(unittest.TestCase):
    def test_cohen_kappa_example(self):
        res = kappa_from_table(50, 30, 10, 10)
        self.assertAlmostEqual(res["observed"], 0.80)
        self.assertAlmostEqual(res["chance"], 0.52)
        self.assertAlmostEqual(res["kappa"], 0.5833333, places=6)

    def test_krippendorff_example(self):
        s, r = "safe", "risky"
        res = krippendorff_alpha([[s, s, s], [s, s, s], [r, r, r], [s, s, r], [s, r, r]])
        self.assertAlmostEqual(res["observed"], 4 / 15)
        self.assertAlmostEqual(res["expected"], 54 / 105)
        self.assertAlmostEqual(res["alpha"], 0.4814815, places=6)


class AgainstReferencePackages(unittest.TestCase):
    def test_kappa_sklearn(self):
        a, b = [0, 1, 1, 0, 1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1, 1, 1, 1, 0]
        self.assertAlmostEqual(cohen_kappa(a, b)["kappa"], 0.3478261, places=6)

    def test_alpha_with_missing_values(self):
        units = [[1, 2, None, 1], [3, 3, 3, None], [None, 5, 4, 5], [2, None, 2, 3], [4, 4, 5, 4], [1, 1, None, 2]]
        # values from krippendorff.alpha(reliability_data=..., level_of_measurement=...)
        self.assertAlmostEqual(krippendorff_alpha(units, "nominal")["alpha"], 0.375, places=6)
        self.assertAlmostEqual(krippendorff_alpha(units, "ordinal")["alpha"], 0.8746638, places=6)
        self.assertAlmostEqual(krippendorff_alpha(units, "interval")["alpha"], 0.8676471, places=6)


class Helpers(unittest.TestCase):
    def test_pattern_and_entropy(self):
        self.assertEqual(agreement_pattern(["a", "a", "a"]), "all")
        self.assertEqual(agreement_pattern(["a", "b", "a"]), "two")
        self.assertEqual(agreement_pattern(["a", "b", "c"]), "none")
        self.assertAlmostEqual(entropy([0.5, 0.5]), 1.0)


class Data(unittest.TestCase):
    def test_new_guideline_raises_agreement(self):
        rows = load_jsonl(HERE / "data" / "reviews.jsonl")
        alpha = {g: krippendorff_alpha([list(r["labels"].values()) for r in rows if r["guideline"] == g])["alpha"]
                 for g in ("v1", "v2")}
        self.assertLess(alpha["v1"], 0.5)
        self.assertGreater(alpha["v2"], 0.6)

    def test_triage(self):
        from harmful_or_healthy import triage
        cases = {c["id"]: triage(c)[0] for c in load_json(HERE / "data" / "disagreement_cases.json")["cases"]}
        self.assertEqual(cases["d-02"], "error")
        self.assertEqual(cases["d-03"], "policy")
        self.assertEqual(cases["d-05"], "preference")
        self.assertEqual(cases["d-07"], "judge")

    def test_balanced_set_serves_more_users_than_the_top_rated_one(self):
        from statistics import mean
        from topic_entropy import coverage
        d = load_json(HERE / "data" / "search_results.json")
        intents = d["queries"][-1]["interpretations"]
        wall, bal = d["result_sets"]["vendor_wall"], d["result_sets"]["balanced"]
        self.assertGreater(mean(r["rating"] for r in wall), mean(r["rating"] for r in bal))
        self.assertGreater(coverage(bal, intents), coverage(wall, intents))

    def test_ring_is_flagged(self):
        out = run(__import__("too_good_agreement").main)
        for acc in ("acc-09", "acc-10", "acc-11", "acc-12"):
            self.assertIn(f"{acc}:   55% correct against gold  <- flagged", out)
        self.assertNotIn("acc-01:   92% correct against gold  <- flagged", out)


class Exercise(unittest.TestCase):
    def test_example(self):
        import exercise.check_my_agreement as ex
        out = run(ex.main)
        self.assertIn("15 / 20 = 75%", out)
        self.assertIn("= 0.44", out)
        self.assertIn("harmful (rubric, policy, error): 4 of 5", out)

    def test_untagged_disagreement_is_reported(self):
        import exercise.check_my_agreement as ex
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "p.csv"
            p.write_text("rater_a,rater_b,reason\npass,pass,\npass,fail,\nfail,fail,\n", encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("not tagged yet", out)


if __name__ == "__main__":
    unittest.main()
