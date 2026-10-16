import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import demo
from bot import policz_werdykt
from wyjasnij import BRAK_POLA, roznice


class TestRegresje(unittest.TestCase):
    def test_roznice_odroznia_brak_pola_od_null(self):
        roznica = roznice({"stan": {"pogoda": None}}, {"stan": {}})["stan"]
        self.assertEqual(roznica, [("pogoda", None, BRAK_POLA)])

    def test_zamowienie_bez_chlodzonych_nie_obiecuje_torby(self):
        werdykt = policz_werdykt(
            {"burza_od": "13:00"},
            {"status": "w drodze"},
            {"okno_od": "12:45", "okno_do": "13:30"},
            {"chlodzone_w_deszczu": True},
            {"chlodzone": False},
        )
        self.assertEqual(werdykt, "zdazymy")

    def test_demo_zachowuje_dotychczasowe_wpisy_logu(self):
        katalog = demo.TU / "logi"
        with tempfile.TemporaryDirectory(dir=katalog) as tymczasowy:
            plik = Path(tymczasowy) / "test.jsonl"
            plik.write_text("sentinel\n", encoding="utf-8")
            with patch.object(demo, "LOG", plik), contextlib.redirect_stdout(io.StringIO()):
                demo.main()
            wpisy = plik.read_text(encoding="utf-8").splitlines()

        self.assertEqual(wpisy[0], "sentinel")
        self.assertEqual(len(wpisy), 5)


if __name__ == "__main__":
    unittest.main()