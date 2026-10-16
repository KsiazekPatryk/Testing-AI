import unittest

from koperta import zbuduj_koperte
from model_tokenowy import Ustawienia


class TestRegresje(unittest.TestCase):
    def test_koperta_zapisuje_seed_symulacji_osobno(self):
        koperta = zbuduj_koperte(
            Ustawienia(seed=None), "migawka", "produkcyjny", seed_symulacji=23
        )

        self.assertIsNone(koperta["dekodowanie"]["seed"])
        self.assertEqual(koperta["symulacja"]["seed"], 23)


if __name__ == "__main__":
    unittest.main()