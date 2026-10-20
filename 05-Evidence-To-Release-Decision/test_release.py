"""
test_release.py: unit tests for folder 05.

Run:  python -m unittest -v test_release
"""

import contextlib
import io
import json
import random
import unittest
from pathlib import Path

from exercise.check_my_gate import review
from incident_replay import QUESTION, clean_state, dirty_state, judge, run_agent
from pairwise import compare, rubric, rubric_judge
from release_gate import check_canary, evaluate
from stats import load, mean_ci, wilson

HERE = Path(__file__).parent
GATE = json.loads((HERE / "release_gate.json").read_text(encoding="utf-8"))
BASELINE = load(HERE / "data" / "baseline_v1.jsonl")


def decide(name: str):
    with contextlib.redirect_stdout(io.StringIO()):
        return evaluate(GATE, load(HERE / "data" / f"{name}.jsonl"), BASELINE)[0]


class ReleaseGate(unittest.TestCase):
    def test_privacy_leak_is_a_hard_block(self):
        self.assertEqual(decide("candidate_v2"), "HOLD")

    def test_too_few_cases_means_collect_more_data(self):
        self.assertEqual(decide("candidate_v3_quick"), "COLLECT MORE DATA")

    def test_fixed_version_goes_to_canary(self):
        self.assertEqual(decide("candidate_v3"), "ROLL OUT GRADUALLY")

    def test_canary_drop_triggers_rollback(self):
        with contextlib.redirect_stdout(io.StringIO()):
            decision, reasons = check_canary(GATE, load(HERE / "data" / "candidate_v3.jsonl"),
                                             load(HERE / "data" / "canary_v3.jsonl"))
        self.assertEqual(decision, "ROLL BACK")
        self.assertIn("spanish_support", reasons[0])


class Statistics(unittest.TestCase):
    def test_small_samples_have_wider_intervals(self):
        _, lo_small, hi_small = mean_ci([8, 9, 7, 8, 9])
        _, lo_big, hi_big = mean_ci([8, 9, 7, 8, 9] * 20)
        self.assertGreater(hi_small - lo_small, hi_big - lo_big)

    def test_wilson(self):
        lo, hi = wilson(11, 13)
        self.assertTrue(0 < lo < 11 / 13 < hi <= 1)


class Pairwise(unittest.TestCase):
    def test_rubric_ignores_order(self):
        cases = json.loads((HERE / "pairwise_cases.json").read_text(encoding="utf-8"))["support"]
        a = compare(cases, rubric_judge, random.Random(1))
        b = compare(cases, rubric_judge, random.Random(99))
        self.assertEqual(a, b)

    def test_better_is_not_acceptable(self):
        _, violations = rubric("Our window is 30 days, so it is too late, but we can make an exception.", "outside")
        self.assertTrue(violations)


class Reproducibility(unittest.TestCase):
    def test_clean_state_hides_the_bug(self):
        self.assertGreaterEqual(judge(run_agent(QUESTION, clean_state())[0])[0], 7)
        self.assertLess(judge(run_agent(QUESTION, dirty_state())[0])[0], 7)


class Exercise(unittest.TestCase):
    def test_example_gate_is_complete(self):
        spec = json.loads((HERE / "exercise" / "my_release_gate.json").read_text(encoding="utf-8"))
        self.assertEqual(review(spec["answers"]), [])

    def test_placeholders_are_caught(self):
        problems = review({"1_sample": "TBD"})
        self.assertTrue(any(p.startswith("1_sample") for p in problems))
        self.assertTrue(any(p.startswith("5_signal_to_hold") for p in problems))


if __name__ == "__main__":
    unittest.main()
