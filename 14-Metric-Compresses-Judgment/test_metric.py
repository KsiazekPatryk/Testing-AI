"""
test_metric.py: unit tests for folder 14.

Run:  python -m unittest -v test_metric
"""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from metrickit import (contrast_ratio, fingerprint, load_json, load_jsonl, ngrams, overlap, percentile_rank,
                       weighted_score, wilson)

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class Kit(unittest.TestCase):
    def test_weights_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            weighted_score({"a": 1.0, "b": 1.0}, {"a": 0.5, "b": 0.6})

    def test_wilson_stays_inside_0_1(self):
        lo, hi = wilson(5, 5)
        self.assertLess(lo, 1.0)
        self.assertEqual(hi, 1.0)

    def test_contrast_black_on_white(self):
        self.assertAlmostEqual(contrast_ratio("#000000", "#FFFFFF"), 21.0, places=1)

    def test_percentile_rank(self):
        self.assertEqual(percentile_rank(4.2, [1.0, 1.2], lower_is_better=True), 0.0)
        self.assertEqual(percentile_rank(0.5, [1.0, 1.2], lower_is_better=True), 1.0)

    def test_overlap(self):
        text = "one two three four five six seven eight nine"
        self.assertEqual(overlap(text, ngrams(text)), 1.0)
        self.assertEqual(overlap(text, ngrams("completely different words here and there and more")), 0.0)


class NumbersFromThePost(unittest.TestCase):
    def test_weighted_score_084(self):
        spec = load_json(HERE / "data" / "metric_spec.json")
        cand = load_json(HERE / "data" / "candidates.json")
        self.assertAlmostEqual(weighted_score(cand["candidates"]["A"], spec["weights"]), 0.84)

    def test_weights_frozen_before_results(self):
        spec = load_json(HERE / "data" / "metric_spec.json")
        self.assertEqual(fingerprint(spec["weights"]), spec["frozen_fingerprint"])

    def test_late_weights_flip_the_winner(self):
        spec = load_json(HERE / "data" / "metric_spec.json")
        cand = load_json(HERE / "data" / "candidates.json")
        a, b = cand["candidates"]["A"], cand["candidates"]["B"]
        self.assertGreater(weighted_score(a, spec["weights"]), weighted_score(b, spec["weights"]))
        late = cand["proposed_after_results"]["weights"]
        self.assertLess(weighted_score(a, late), weighted_score(b, late))


class Blockers(unittest.TestCase):
    def setUp(self):
        import weighted_metric
        self.wm = weighted_metric
        self.case = load_json(HERE / "data" / "allergy_case.json")

    def test_warm_reply_fails_plain_passes(self):
        warm = dict(self.wm.blocker_checks(self.case["replies"]["warm"], self.case["right_tools"]))
        plain = dict(self.wm.blocker_checks(self.case["replies"]["plain"], self.case["right_tools"]))
        self.assertIn("FAIL", warm.values())
        self.assertNotIn("FAIL", plain.values())
        self.assertEqual(plain["escalated_when_tool_failed"], "PASS")

    def test_timeout_without_escalation_fails(self):
        reply = copy.deepcopy(self.case["replies"]["plain"])
        reply["trace"] = [s for s in reply["trace"] if s["step"] != "escalate"]
        checks = dict(self.wm.blocker_checks(reply, self.case["right_tools"]))
        self.assertEqual(checks["escalated_when_tool_failed"], "FAIL")

    def test_gate(self):
        out = run(self.wm.main)
        self.assertIn("candidate A: weighted 0.84, failed blocker checks: 4  ->  BLOCKED", out)
        self.assertIn("candidate B: weighted 0.83, failed blocker checks: 0  ->  GO", out)
        self.assertIn("->  passes", out)          # averaged in, the blocker would not stop the warm reply


class WhatMetricMisses(unittest.TestCase):
    def test_same_accuracy_different_business(self):
        import what_metric_misses as w
        homes = load_jsonl(HERE / "data" / "home_flips.jsonl")
        for m in ("independent", "momentum"):
            self.assertAlmostEqual(sum(abs(h[f"err_{m}"]) for h in homes) / len(homes), 0.04, places=4)
        ind, mom = w.by_quarter(homes, "independent"), w.by_quarter(homes, "momentum")
        self.assertGreater(sum(ind.values()), 0)
        self.assertLess(sum(mom.values()), 0)
        self.assertLess(min(mom.values()), 5 * min(ind.values()))

    def test_spike_and_alternatives(self):
        import what_metric_misses as w
        out = run(w.main)
        self.assertIn("60+ s", out)
        self.assertIn("switched_tab", out)
        self.assertIn("slow_page", out)


class Style(unittest.TestCase):
    def test_all_correct_but_not_all_good(self):
        import correct_but_ugly as c
        rubric = load_json(HERE / "data" / "style_rubric.json")
        texts = load_json(HERE / "data" / "style_outputs.json")["texts"]
        for t in texts.values():
            self.assertTrue(all(f in t["text"] for f in t["facts"]))
        ceil = {n: c.judge_in_context(t["text"], t["context"], rubric)[1] for n, t in texts.items()}
        self.assertEqual(ceil["refund_plain"], 10)
        self.assertEqual(ceil["ldl_calm"], 10)
        self.assertEqual(ceil["ldl_alarming"], 1)
        self.assertEqual(ceil["ldl_soothing"], 1)
        self.assertEqual(c.judge_in_context(texts["ldl_warm"]["text"], "consumer", rubric)[1], 10)
        self.assertEqual(c.judge_in_context(texts["ldl_warm"]["text"], "medical", rubric)[1], 7)

    def test_accessibility(self):
        import correct_but_ugly as c
        out = run(c.main)
        self.assertIn("revenue_v1: numbers correct: True; 6 problem(s)", out)
        self.assertIn("revenue_v2: numbers correct: True; accessible", out)

    def test_demo_is_the_best_slice(self):
        import taste_at_scale as t
        out = run(t.main)
        self.assertIn("demo (short, English)                  2 m", out)
        self.assertEqual(out.count("%   first-draft generator"), 4)
        self.assertIn("first half 85%, second half 85%", out)


class CurveAndPeers(unittest.TestCase):
    def test_curve(self):
        import bending_curve as b
        out = run(b.main)
        self.assertIn("Your data cannot tell them apart", out)
        self.assertIn("leader  failure rate  8.2% ", out)
        self.assertIn("shipping            88% ->  85%", out)

    def test_peers(self):
        import quality_is_relative as q
        out = run(q.main)
        self.assertEqual(out.count("we beat 0% of the group"), 3)
        self.assertEqual(out.count("its absence is a finding"), 2)
        out = run(q.main, ["x", "--no-method"])
        self.assertIn("Not comparing", out)


class Exam(unittest.TestCase):
    def test_exam(self):
        import exams_need_testing as e
        out = run(e.main)
        self.assertIn("11/12 correct by the answer key = 92%", out)
        self.assertIn("removed: 6 leaked, 1 ambiguous; left: 5 items", out)
        self.assertIn("defining risk                   0 item(s)", out)


class Exercise(unittest.TestCase):
    def test_example_is_decoration(self):
        import exercise.audit_my_eval_suite as ex
        out = run(ex.main)
        self.assertIn("You have decoration, not an evaluation", out)
        self.assertEqual(out.count("GAP"), 6)

    def test_good_suite(self):
        import exercise.audit_my_eval_suite as ex
        spec = {"suite": "s", "audit_date": "2026-11-22", "1_owner": "quality team",
                "2_versioned": {"dataset": True, "labels": True, "rubric": True, "judge": True},
                "3_case_groups": [{"group": "g", "cases": 10, "last_reviewed": "2026-10-01"}],
                "4_leakage": {"cases_are_public": False, "times_used_to_tune_prompts_or_models": 3,
                              "untouched_holdout_exists": True},
                "5_metric_vs_users": {"metric": "m", "what_users_experience": "u", "same_thing": True},
                "6_can_change_release": {"answer": True, "last_time_it_changed_a_decision": "2026-10-20, v4.2 held"}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.json"
            p.write_text(json.dumps(spec), encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertNotIn("GAP", out)
        self.assertIn("run like a product", out)


if __name__ == "__main__":
    unittest.main()
