"""
test_evidence.py: unit tests for the building blocks of folder 04.

Run:  python -m unittest -v test_evidence
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from assistant import answer, extract_facts, parse_days
from golden_vs_live import check, wilson
from risk_sampling import allocate, chance_to_see, risk_score, rule_of_three
from search import load_articles, rank
from transformations import add_typos

HERE = Path(__file__).parent


class Transformations(unittest.TestCase):
    def test_typos_are_reproducible_and_keep_digits(self):
        q = "Can I return my shoes after 45 days?"
        self.assertEqual(add_typos(q, seed=3), add_typos(q, seed=3))
        self.assertIn("45", add_typos(q, seed=3, rate=1.0))
        self.assertNotEqual(add_typos(q, seed=3, rate=1.0), q)


class Assistant(unittest.TestCase):
    def test_parse_days(self):
        self.assertEqual(parse_days("a month and a half ago"), 45)
        self.assertEqual(parse_days("after 6 weeks"), 42)
        self.assertEqual(parse_days("po 45 dniach"), 45)
        self.assertIsNone(parse_days("after 45 dyas"))

    def test_wording_changes_but_facts_do_not(self):
        q = "Can I return my shoes after 45 days?"
        texts = {answer(q, seed=s).text for s in range(10)}
        facts = {tuple(extract_facts(t).items()) for t in texts}
        self.assertGreater(len(texts), 1)
        self.assertEqual(len(facts), 1)

    def test_planted_gift_bug_breaks_the_relation(self):
        base = extract_facts(answer("Can I return my shoes after 45 days?", seed=1).text)
        gift = extract_facts(answer("Can I return my shoes after 45 days? It was a gift.", seed=1).text)
        self.assertNotEqual(base, gift)

    def test_name_does_not_change_risk(self):
        a = answer("Hi, I'm Anna. Can I return boots I bought 12 days ago?", seed=1).meta["risk"]
        b = answer("Hi, I'm Mohammed. Can I return boots I bought 12 days ago?", seed=1).meta["risk"]
        self.assertEqual(a, b)


class GoldenAndLive(unittest.TestCase):
    def test_golden_set_passes(self):
        golden = json.loads((HERE / "golden_set.json").read_text(encoding="utf-8"))["cases"]
        failing = [c["id"] for i, c in enumerate(golden) if not check(c, i)[0]]
        self.assertEqual(failing, [])

    def test_wilson_interval_contains_the_rate(self):
        lo, hi = wilson(92, 100)
        self.assertLess(lo, 0.92)
        self.assertGreater(hi, 0.92)


class Ranking(unittest.TestCase):
    def test_keyword_stuffing_bug_is_visible(self):
        data = json.loads((HERE / "help_center.json").read_text(encoding="utf-8"))
        q = "return shoes after 30 days"
        self.assertEqual(rank(q, load_articles())[0][0], "returns-policy")
        stuffed = [c for c in data["weak_candidates"] if c["id"] == "promo-landing-page"]
        self.assertEqual(rank(q, load_articles() + stuffed)[0][0], "promo-landing-page")


class RiskSampling(unittest.TestCase):
    def test_allocation_adds_up_and_respects_the_floor(self):
        parts = allocate([47, 40, 3, 1], 600, 20)
        self.assertEqual(sum(parts), 600)
        self.assertTrue(all(p >= 20 for p in parts))
        self.assertGreater(parts[0], parts[3])

    def test_rare_failure_math(self):
        self.assertAlmostEqual(rule_of_three(300), 0.01)
        self.assertLess(chance_to_see(30, 0.01), 0.3)

    def test_risk_score_range(self):
        worst = {"impact": 5, "likelihood": 5, "detectability": 5, "irreversibility": 5, "regulatory": 5}
        self.assertEqual(risk_score(worst), 125)


class Exercise(unittest.TestCase):
    def test_pasted_answers_are_checked_instead_of_the_local_assistant(self):
        import exercise.check_my_questions as ex
        spec = {"typo_seed": 1, "questions": [{
            "id": "mine", "question": "Q", "paraphrase": "Q2", "typos": "Q3", "facts": ["30 days"],
            "answers": {"original": "Returns: 30 days.", "paraphrase": "Returns: 30 days.",
                        "typos": "Free shipping!"}}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "q.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            with patch("sys.argv", ["x", str(path)]), patch.object(ex, "ROOT", Path(tmp)), \
                    patch("builtins.print"):
                ex.main()
            saved = json.loads((Path(tmp) / "output" / "exercise_golden_candidates.json").read_text())
        self.assertEqual([c["id"] for c in saved["candidates"]], ["mine::typos"])


if __name__ == "__main__":
    unittest.main()
