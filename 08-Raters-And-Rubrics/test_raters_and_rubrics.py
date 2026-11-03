"""
test_raters_and_rubrics.py: unit tests for folder 08.

Reference values for kappa come from scikit-learn (not needed to run the folder);
Fleiss' kappa was checked by hand.

Run:  python -m unittest -v test_raters_and_rubrics
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agreement import cohen_kappa, fleiss_kappa, load_json, load_jsonl, mean, weighted_kappa

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class Agreement(unittest.TestCase):
    def test_against_reference_values(self):
        a, b = [0, 1, 1, 0, 1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1, 1, 1, 1, 0]
        self.assertAlmostEqual(cohen_kappa(a, b), 0.3478261, places=6)              # sklearn
        self.assertAlmostEqual(weighted_kappa([3, 5, 7, 8, 10, 2, 6], [4, 5, 6, 9, 10, 3, 4]),
                               0.9108280, places=6)                                  # sklearn, quadratic
        r = [[1, 1, 1], [1, 0, 1], [0, 0, 0], [1, 1, 0], [0, 0, 1], [1, 1, 1]]
        self.assertAlmostEqual(fleiss_kappa(r), 0.2987013, places=6)

    def test_perfect_and_chance(self):
        self.assertEqual(cohen_kappa(["a", "b", "a"], ["a", "b", "a"]), 1.0)
        self.assertLess(cohen_kappa([1, 0, 1, 0], [0, 1, 0, 1]), 0)


class Calibration(unittest.TestCase):
    def test_calibration_raises_agreement(self):
        rows = load_jsonl(HERE / "data" / "calibration.jsonl")
        def labels(rnd):
            per = [[x["score"] >= 7 for x in rows if x["round"] == rnd and x["rater"] == r]
                   for r in ("anna", "ben", "chen")]
            return list(zip(*per))
        self.assertLess(fleiss_kappa(labels("before")), 0.4)
        self.assertGreater(fleiss_kappa(labels("after")), 0.6)


class Blinding(unittest.TestCase):
    def test_unblinded_win_disappears_when_blinded(self):
        import blind_review
        rows = load_jsonl(HERE / "data" / "blind_review.jsonl")
        self.assertGreater(mean(blind_review.diffs(rows, "unblinded")), 1.0)
        self.assertLess(abs(mean(blind_review.diffs(rows, "blinded"))), 0.3)


class Fatigue(unittest.TestCase):
    def test_only_the_tired_session_is_flagged(self):
        out = run(__import__("fatigue_drift").main)
        self.assertIn("chen: from item 91 on", out)
        self.assertIn("anna: stable", out)


class WhoLabels(unittest.TestCase):
    def test_experts_and_generalists_disagree_where_expertise_matters(self):
        from who_labels import preference
        rows = load_jsonl(HERE / "data" / "relevance_labels.jsonl")
        med = [r for r in rows if r["domain"] == "medical"]
        self.assertLess(preference(med, "generalist_score"), 0)
        self.assertGreater(preference(med, "expert_score"), 0)
        self.assertLess(preference(med, "llm_judge_score"), 0)


class Provenance(unittest.TestCase):
    def test_tiers_and_problems(self):
        from label_provenance import problem, required_tier
        card = {"created_by": "g01", "rater_type": "generalist", "expertise": "none",
                "guideline_version": "v2", "n_raters": 1, "agreement": None}
        self.assertEqual(required_tier({**card, "high_risk": False, "used_in_release_gate": False}), "generalist")
        self.assertIsNone(problem({**card, "high_risk": False, "used_in_release_gate": False}))
        self.assertIn("generalist", problem({**card, "high_risk": True, "used_in_release_gate": True}))
        self.assertIn("no provenance", problem({**card, "created_by": None, "high_risk": False,
                                                "used_in_release_gate": False}))


class Rubric(unittest.TestCase):
    def test_blockers_override_scores(self):
        from rubric import score, validate
        support = load_json(HERE / "data" / "rubric_support.json")
        self.assertEqual(validate(support), [])
        self.assertEqual(len(validate(load_json(HERE / "data" / "rubric_vague.json"))), 3)
        leak = next(r for r in load_jsonl(HERE / "data" / "support_responses.jsonl") if r["id"] == "sup-04")
        raw, final, verdict = score(leak, support)
        self.assertGreaterEqual(raw, 7)
        self.assertEqual(final, 0.0)
        self.assertTrue(verdict.startswith("BLOCKED"))

    def test_agent_patch_a_is_blocked(self):
        from agent_fix_review import blocker
        a, b = load_json(HERE / "data" / "agent_patches.json")["patches"]
        self.assertTrue(a["tests_pass"] and b["tests_pass"])
        self.assertEqual(blocker(a), "weakens tenant isolation")
        self.assertEqual(blocker(b), "")


class Exercise(unittest.TestCase):
    def test_example_rubric_fails_all_three(self):
        import exercise.audit_my_rubric as ex
        out = run(ex.main)
        self.assertEqual(out.count("[NO     ]"), 3)
        self.assertIn("Start with question 3", out)

    def test_a_good_rubric_passes(self):
        import exercise.audit_my_rubric as ex
        spec = {"name": "good", "scale": {"min": 0, "max": 10},
                "anchors": load_json(HERE / "data" / "rubric_support.json")["anchors"],
                "blockers": ["personal_data_leak"],
                "labels": {"created_by": "two support leads", "expertise": "5 years of returns policy",
                           "dataset": None}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            p.write_text(json.dumps(spec), encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("All three answered", out)


if __name__ == "__main__":
    unittest.main()
