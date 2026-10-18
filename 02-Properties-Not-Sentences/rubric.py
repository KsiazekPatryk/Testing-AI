"""
rubric.py — kryteria oceny zamiast „oczekiwany tekst == rzeczywisty tekst”.

Kryterium opisuje WŁAŚCIWOŚĆ odpowiedzi:
  * WYMAGA   — w odpowiedzi musi pojawić się dana treść (np. „30 dni”),
  * ZAKAZUJE — w odpowiedzi nie może pojawić się dana treść (np. obietnica wyjątku).

Każde kryterium jest albo:
  * BLOKEREM  — twarda granica; jedno naruszenie = test nie przechodzi, koniec dyskusji,
  * MIĘKKIE   — jakość, którą raportujemy, ale która sama nie zatrzymuje wydania.

Tu sprawdzamy kryteria regułami (wyrażenia regularne). W prawdziwym projekcie
część kryteriów oceniają ludzie albo sędzia LLM — ale ich DEFINICJA wygląda tak samo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Kryterium:
    nazwa: str
    rodzaj: str                 # "wymaga" albo "zakazuje"
    wzorce: List[str]           # wystarczy, że pasuje jeden
    bloker: bool = True
    powod_porazki: str = ""

    def sprawdz(self, odpowiedz: str) -> bool:
        tekst = odpowiedz.lower()
        trafienie = any(re.search(w, tekst) for w in self.wzorce)
        return trafienie if self.rodzaj == "wymaga" else not trafienie


@dataclass
class Wynik:
    przeszla: bool                                  # brak naruszonych blokerów
    naruszone_blokery: List[Kryterium] = field(default_factory=list)
    niespelnione_miekkie: List[Kryterium] = field(default_factory=list)

    def opis(self) -> str:
        if self.przeszla and not self.niespelnione_miekkie:
            return "PRZESZŁA"
        czesci = []
        if self.naruszone_blokery:
            czesci.append("NIE PRZESZŁA, bo " + "; ".join(k.powod_porazki for k in self.naruszone_blokery))
        else:
            czesci.append("PRZESZŁA")
        if self.niespelnione_miekkie:
            czesci.append("uwagi: " + "; ".join(k.powod_porazki for k in self.niespelnione_miekkie))
        return " | ".join(czesci)


def ocen(odpowiedz: str, kryteria: List[Kryterium]) -> Wynik:
    wynik = Wynik(przeszla=True)
    for k in kryteria:
        if k.sprawdz(odpowiedz):
            continue
        if k.bloker:
            wynik.przeszla = False
            wynik.naruszone_blokery.append(k)
        else:
            wynik.niespelnione_miekkie.append(k)
    return wynik
