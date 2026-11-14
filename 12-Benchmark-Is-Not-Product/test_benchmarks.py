"""
test_benchmarks.py: unit tests for folder 12.

Run:  python -m unittest -v test_benchmarks
"""

import contextlib
import io
import json
import math
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from evals import bradley_terry, found_in, load_json, load_jsonl, mean, ndcg, pass_at_k, reciprocal_rank

HERE = Path(__file__).parent


def run(main, argv=("x",)):
    out = io.StringIO()
    with patch("sys.argv", list(argv)), contextlib.redirect_stdout(out):
        main()
    return out.getvalue()


class Metrics(unittest.TestCase):
    def test_pass_at_k(self):
        self.assertAlmostEqual(pass_at_k(10, 3, 1), 0.3)
        self.assertAlmostEqual(pass_at_k(10, 3, 5), 1 - math.comb(7, 5) / math.comb(10, 5))
        self.assertEqual(pass_at_k(10, 0, 10), 0.0)
        self.assertEqual(pass_at_k(10, 9, 2), 1.0)

    def test_bradley_terry_is_the_maximum_likelihood_fit(self):
        votes = [("a", "b")] * 7 + [("b", "a")] * 3 + [("b", "c")] * 6 + [("c", "b")] * 4 + [("a", "c")] * 8 + [("c", "a")] * 2
        r = bradley_terry(votes)
        p = {k: 10 ** ((v - 1000) / 400) for k, v in r.items()}
        wins, games = defaultdict(int), defaultdict(int)
        for w, l in votes:
            wins[w] += 1
            games[tuple(sorted((w, l)))] += 1
        for i in p:   # at the optimum, expected wins == observed wins
            expected = sum(n * p[i] / (p[i] + p[j]) for (a, b), n in games.items() for j in ((b,) if a == i else (a,) if b == i else ()))
            self.assertAlmostEqual(expected, wins[i], places=6)

    def test_ranking_metrics(self):
        self.assertEqual(ndcg([3, 0, 0]), 1.0)
        self.assertAlmostEqual(ndcg([0] * 8 + [3, 0]), 1 / math.log2(10))
        self.assertAlmostEqual(reciprocal_rank([False] * 8 + [True]), 1 / 9)

    def test_found_in(self):
        self.assertTrue(found_in("What is 2 + 2?", "blah. what is 2 2 answer"))
        self.assertFalse(found_in("What is 2 + 3?", "what is 2 2"))


class Data(unittest.TestCase):
    def test_average_hides_weak_subjects(self):
        rows = load_jsonl(HERE / "data" / "mc_results.jsonl")
        self.assertAlmostEqual(mean([r["correct"] for r in rows]), 0.851)
        law = [r["correct"] for r in rows if r["subject"] == "professional_law"]
        self.assertAlmostEqual(mean(law), 0.58)

    def test_arena_top_model_is_least_correct(self):
        votes = load_jsonl(HERE / "data" / "arena_votes.jsonl")
        r = bradley_terry([(v["winner"], v["b"] if v["winner"] == v["a"] else v["a"]) for v in votes])
        self.assertEqual(max(r, key=r.get), "verbose")

    def test_contamination_gap(self):
        rows = load_jsonl(HERE / "data" / "contamination.jsonl")
        corpus = (HERE / "data" / "training_snippets.txt").read_text(encoding="utf-8")
        seen = [r for r in rows if found_in(r["question"], corpus)]
        self.assertGreater(mean([r["correct_original"] for r in seen]) - mean([r["correct_paraphrase"] for r in seen]), 0.15)


class Scenarios(unittest.TestCase):
    def test_patch_a_passes_tests_and_fails_in_the_company(self):
        import patch_passed_failed as p
        a, b = p.PATCHES
        self.assertTrue(p.unit_tests(a) and p.unit_tests(b))
        self.assertFalse(p.friday(a))
        self.assertTrue(p.friday(b))
        self.assertEqual(p.canary_retry(a), 2)
        self.assertEqual(p.canary_retry(b), 1)

    def test_six_questions_support(self):
        out = run(__import__("six_questions").main)
        self.assertIn("7 x decoration, 1 x weak signal", out)

    def test_manifest_finds_undocumented_changes(self):
        import run_manifest as m
        self.assertEqual(m.diff(m.RUN_1, m.RUN_2), ["index_version", "reranker", "cache"])
        self.assertNotEqual(m.fingerprint(m.RUN_1), m.fingerprint(m.RUN_2))


class Exercise(unittest.TestCase):
    def test_example(self):
        import exercise.check_my_benchmark as ex
        out = run(ex.main)
        self.assertIn("3 gaps, 2 unknowns", out)

    def test_missing_replacement_case(self):
        import exercise.check_my_benchmark as ex
        spec = {"result": "r", "six_questions": {}, "replacement_case": "our stuff"}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            p.write_text(json.dumps(spec), encoding="utf-8")
            out = run(ex.main, ["x", str(p)])
        self.assertIn("missing or too vague", out)


if __name__ == "__main__":
    unittest.main()
