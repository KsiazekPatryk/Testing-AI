"""
test_zwroty.py — ten sam przykład zapisany jako testy (unittest, bez instalowania czegokolwiek).

Uruchom:  python -m unittest -v test_zwroty
"""

import unittest

from rubryka import ocen
from zwroty import KRYTERIA, ODPOWIEDZI, OCZEKIWANE

DOBRE = ODPOWIEDZI[:3]
ZLE = ODPOWIEDZI[3:]


class DokladnaAsercja(unittest.TestCase):
    @unittest.expectedFailure
    def test_dobra_odpowiedz_innymi_slowami(self):
        """Celowo oznaczony jako 'expected failure': pokazuje, że porównanie
        ciągów znaków odrzuca poprawne zachowanie produktu."""
        self.assertEqual(ODPOWIEDZI[1], OCZEKIWANE)


class Wlasciwosci(unittest.TestCase):
    def test_kazda_dobra_odpowiedz_spelnia_blokery(self):
        for odp in DOBRE:
            with self.subTest(odpowiedz=odp):
                wynik = ocen(odp, KRYTERIA)
                self.assertTrue(wynik.przeszla, wynik.opis())

    def test_kazda_zla_odpowiedz_jest_zatrzymana_z_powodem(self):
        for odp in ZLE:
            with self.subTest(odpowiedz=odp):
                wynik = ocen(odp, KRYTERIA)
                self.assertFalse(wynik.przeszla)
                self.assertTrue(wynik.naruszone_blokery, "brak czytelnego powodu porażki")

    def test_brak_nastepnego_kroku_nie_blokuje_wydania(self):
        wynik = ocen(ODPOWIEDZI[1], KRYTERIA)
        self.assertTrue(wynik.przeszla)
        self.assertEqual([k.nazwa for k in wynik.niespelnione_miekkie], ["wskazuje następny krok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
