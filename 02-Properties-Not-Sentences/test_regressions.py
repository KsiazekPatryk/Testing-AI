import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import compare_ratings
from release_gate import bramka
from blind_rating import wolna_sciezka_wyniku


class TestRegresje(unittest.TestCase):
    def test_bramka_odrzuca_puste_i_nieprawidlowe_oceny(self):
        for oceny in ([], [11], [-1], [7.5], [True]):
            with self.subTest(oceny=oceny), self.assertRaises(ValueError):
                bramka(oceny, 0)

    def test_bramka_przyjmuje_poprawne_oceny(self):
        self.assertTrue(all(ok for _, ok in bramka([8, 8, 8, 8], 0)))

    def test_powtorna_ocena_nie_nadpisuje_pliku(self):
        with tempfile.TemporaryDirectory() as tymczasowy:
            katalog = Path(tymczasowy)
            poprzedni = katalog / "patryk.json"
            poprzedni.write_text("stare oceny", encoding="utf-8")

            self.assertEqual(wolna_sciezka_wyniku(katalog, "patryk"), katalog / "patryk-2.json")
            self.assertEqual(poprzedni.read_text(encoding="utf-8"), "stare oceny")

    def test_porownywarka_odrzuca_rozne_zestawy_odpowiedzi(self):
        with tempfile.TemporaryDirectory() as tymczasowy:
            katalog = Path(tymczasowy)
            arkusze = []
            for nazwa, plik in (("a", "turkey.json"), ("b", "my_answers.json")):
                sciezka = katalog / f"{nazwa}.json"
                sciezka.write_text(json.dumps({"plik": plik, "oceniajacy": nazwa, "oceny": {}}),
                                   encoding="utf-8")
                arkusze.append(str(sciezka))

            with patch("sys.argv", ["compare_ratings.py", *arkusze]), self.assertRaises(SystemExit):
                compare_ratings.main()


if __name__ == "__main__":
    unittest.main()