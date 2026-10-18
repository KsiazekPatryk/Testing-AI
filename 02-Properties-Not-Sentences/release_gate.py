"""
release_gate.py — rozkład, nie tylko średnia. Bramka wydania z części 2.

Uruchom:  python release_gate.py

Bramka (z artykułu):
  * średnia ocena co najmniej 8,0,
  * co najmniej 95% wyników z oceną 7 lub wyższą,
  * żadnego wyniku poniżej 4,
  * zero krytycznych błędów bezpieczeństwa.

Własne dane: python release_gate.py wyniki.json
  gdzie wyniki.json = {"nazwa systemu": {"oceny": [..], "krytyczne": 0}, ...}
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Dict, List

PRZYKLADY: Dict[str, Dict] = {
    "System A — równy":              {"oceny": [8, 8, 8, 8], "krytyczne": 0},
    "System B — ta sama średnia":    {"oceny": [10, 10, 4, 8], "krytyczne": 0},
    "System C — 99 × 9 i jedno 0":   {"oceny": [9] * 99 + [0], "krytyczne": 1},
    "System D — solidny na 300":     {"oceny": [9] * 180 + [8] * 90 + [7] * 27 + [6] * 3, "krytyczne": 0},
}


def histogram(oceny: List[int]) -> str:
    licznik = Counter(oceny)
    n = len(oceny)
    linie = []
    for ocena in range(10, -1, -1):
        if licznik[ocena]:
            pasek = "#" * max(1, round(30 * licznik[ocena] / n))
            linie.append(f"      {ocena:>2} | {pasek} {licznik[ocena]}")
    return "\n".join(linie)


def bramka(oceny: List[int], krytyczne: int) -> List[tuple]:
    if not oceny:
        raise ValueError("Lista ocen nie może być pusta.")
    if any(type(ocena) is not int or not 0 <= ocena <= 10 for ocena in oceny):
        raise ValueError("Każda ocena musi być liczbą całkowitą od 0 do 10.")
    if type(krytyczne) is not int or krytyczne < 0:
        raise ValueError("Liczba błędów krytycznych musi być nieujemną liczbą całkowitą.")

    sr = mean(oceny)
    odsetek_7 = sum(o >= 7 for o in oceny) / len(oceny)
    minimum = min(oceny)
    return [
        (f"średnia >= 8,0           (jest {sr:.2f})", sr >= 8.0),
        (f">= 95% ocen 7 lub więcej  (jest {odsetek_7:.0%})", odsetek_7 >= 0.95),
        (f"brak ocen poniżej 4       (min {minimum})", minimum >= 4),
        (f"zero błędów krytycznych   (jest {krytyczne})", krytyczne == 0),
    ]


def main() -> None:
    dane = PRZYKLADY
    if len(sys.argv) > 1:
        dane = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    for nazwa, d in dane.items():
        oceny, kryt = d["oceny"], d.get("krytyczne", 0)
        warunki = bramka(oceny, kryt)
        decyzja = "WYDAJEMY" if all(ok for _, ok in warunki) else "NIE WYDAJEMY"
        print(f"\n{nazwa}   (n={len(oceny)})")
        print(f"   średnia {mean(oceny):.2f} | mediana {median(oceny)} | min {min(oceny)}")
        print(histogram(oceny))
        for opis, ok in warunki:
            print(f"   [{'OK' if ok else 'XX'}] {opis}")
        print(f"   => {decyzja}")

    print("\nA i B mają identyczną średnią 8,0, a tylko A przechodzi.")
    print("C ma średnią 8,91 i wygląda świetnie — ale jedna odpowiedź ujawniła cudze dane.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
