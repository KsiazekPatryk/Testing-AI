"""
test_llm_judge.py: unit tests for folder 11.

Run:  python -m unittest -v test_llm_judge
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from judge import blockers_v2, judge_copyright, judge_v1, judge_v2
from metrics import cohen_kappa, load_json, load_jsonl, pass_agreement, within

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class Metrics(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(within([1, 5, 9], [2, 7, 9]), 2 / 3)
        self.assertEqual(pass_agreement([8, 3], [9, 8]), 0.5)
        self.assertAlmostEqual(cohen_kappa([0, 1, 1, 0, 1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1, 1, 1, 1, 0]),
                               0.3478261, places=6)                       # sklearn


class Judges(unittest.TestCase):
    def test_v1_prefers_warm_policy_break(self):
        warm = "I'm so sorry, I completely understand how frustrating this is! I've issued a refund in full right away."
        short = "I've checked your order: it qualifies under our 30-day policy. Next step: you will receive a label within 1 hour."
        self.assertGreater(judge_v1(warm)[0], judge_v1(short)[0])
        self.assertGreater(judge_v2(short)[0], judge_v2(warm)[0])

    def test_blockers(self):
        self.assertTrue(blockers_v2("You can return it within our 60-day return window."))
        self.assertTrue(blockers_v2("I've refunded you.", context="my insulin was left in the rain"))
        self.assertFalse(blockers_v2("I've checked your order and it qualifies under our 30-day policy."))

    def test_all_probes_pass_for_v2_only(self):
        out = run(__import__("judge_under_test").main)
        self.assertIn("judge_v1: 0 of 5 probes passed", out)
        self.assertIn("judge_v2: 5 of 5 probes passed", out)

    def test_copyright_judge_has_wrong_sense_of_time(self):
        self.assertEqual(judge_copyright("© 2026 Shop", 2026)[0], "outdated")
        from copyright_year import deterministic
        data = load_json(HERE / "data" / "footers.json")
        self.assertTrue(all(deterministic(f["footer"], 2026)[0] == f["truth"] for f in data["footers"]))


class Insulin(unittest.TestCase):
    def test_v2_with_context_matches_anchors(self):
        case = load_json(HERE / "data" / "insulin_case.json")
        for r in case["replies"]:
            self.assertEqual(judge_v2(r["text"], context=case["message"])[0], r["anchor"], r["id"])


class Calibration(unittest.TestCase):
    def test_privacy_pattern_and_correction(self):
        import calibration
        rows = load_jsonl(HERE / "data" / "replies.jsonl")
        for r in rows:
            r["v2"] = judge_v2(r["reply"], context=r["question"])[0]
        train = [r for i, r in enumerate(rows) if i % 2 == 0]
        test = [r for i, r in enumerate(rows) if i % 2 == 1 and r["segment"] == "privacy"]
        corr = calibration.correction(train)
        self.assertLessEqual(corr["privacy"][10], -3)
        h = [r["human"] for r in test]
        self.assertGreater(pass_agreement(h, [calibration.corrected(r, corr) for r in test]),
                           pass_agreement(h, [r["v2"] for r in test]))

    def test_routing_rules_written(self):
        import calibration
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(calibration, "HERE", Path(tmp)), patch("calibration.load_jsonl",
                                                                     lambda p: load_jsonl(HERE / "data" / "replies.jsonl")):
                run(calibration.main)
            rules = json.loads((Path(tmp) / "output" / "routing_rules.json").read_text(encoding="utf-8"))
        self.assertEqual(rules["medical"]["route"], "human")
        self.assertEqual(rules["refunds"]["route"], "automatic")
        self.assertEqual(rules["privacy"]["route"], "automatic_corrected")


class Exercise(unittest.TestCase):
    def test_example_points_at_the_rubric(self):
        import exercise.check_my_disagreements as ex
        out = run(ex.main)
        self.assertIn("Most cases (6 of 10) are an ambiguous rubric", out)

    def test_other_majority(self):
        import exercise.check_my_disagreements as ex
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.csv"
            p.write_text("human_score,judge_score,category\n3,8,judge_error\n2,9,judge_error\n7,4,preference\n",
                         encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("The largest group is judge_error (2 of 3)", out)


if __name__ == "__main__":
    unittest.main()
