"""
shoe_returns.py — przykład z artykułu: „Kupiłem buty 45 dni temu, czy mogę je zwrócić?”

Uruchom:  python shoe_returns.py

Porównuje dwa podejścia do tej samej listy odpowiedzi modelu:
  1. dokładna asercja: odpowiedź == oczekiwane zdanie,
  2. kryteria oceny:   czy odpowiedź ma właściwości akceptowalnej odpowiedzi.
"""

from __future__ import annotations

import sys

from rubric import Kryterium, ocen

PYTANIE = "Kupiłem buty 45 dni temu, czy mogę je zwrócić?"
OCZEKIWANE = "Nie, buty można zwrócić tylko w ciągu 30 dni."

# Odpowiedzi, które model mógłby dać w kolejnych uruchomieniach.
ODPOWIEDZI = [
    "Nie, buty można zwrócić tylko w ciągu 30 dni.",
    "Zwroty są możliwe przez 30 dni od zakupu, więc zakup sprzed 45 dni jest już poza standardowym okresem.",
    "Niestety minęło już 45 dni, a na zwrot mamy 30 dni od zakupu. Jeśli buty mają wadę, "
    "możesz złożyć reklamację — chętnie pomogę z formularzem.",
    "Termin zwrotu to 30 dni, ale proszę spróbować — prawdopodobnie zostanie przyjęty.",
    "Standardowo mamy 30 dni, ale proszę napisać do obsługi klienta, na pewno jakoś to załatwią.",
    "Tak, oczywiście! Zwroty przyjmujemy w ciągu 60 dni.",
]

KRYTERIA = [
    Kryterium(
        "limit 30 dni", "wymaga", [r"\b30\s*dni"],
        powod_porazki="nie podała limitu 30 dni",
    ),
    Kryterium(
        "45 dni to za późno", "wymaga",
        [r"^nie\b", r"nie (można|da się|przyjmiemy|jest możliw)", r"poza .*okres",
         r"minęł", r"tylko (w ciągu|przez) 30", r"po terminie"],
        powod_porazki="nie stwierdziła jasno, że po 45 dniach zwrot nie przysługuje",
    ),
    Kryterium(
        "nie sugeruje przyjęcia zwrotu", "zakazuje",
        [r"(prawdopodobnie|pewnie|raczej)\s+(zostanie\s+)?(przyjęt|uzna|zaakcept)",
         r"spróbo?wa", r"^tak\b"],
        powod_porazki="zasugerowała, że zwrot po 45 dniach może zostać przyjęty",
    ),
    Kryterium(
        "nie obiecuje nieudokumentowanego wyjątku", "zakazuje",
        [r"jakoś\s+(to\s+)?załatw", r"zrobimy\s+wyjątek", r"na pewno .*(pomog|załatw)"],
        powod_porazki="zasugerowała nieistniejący wyjątek od polityki",
    ),
    Kryterium(
        "wskazuje następny krok", "wymaga",
        [r"reklamac", r"formularz", r"kontakt", r"możesz", r"pomogę"],
        bloker=False,
        powod_porazki="brak jasnego następnego kroku (miękkie)",
    ),
]


def main() -> None:
    print(f"Pytanie:      {PYTANIE}")
    print(f"Oczekiwane:   {OCZEKIWANE}\n")
    for i, odp in enumerate(ODPOWIEDZI, 1):
        dokladna = "OK " if odp == OCZEKIWANE else "BŁĄD"
        wynik = ocen(odp, KRYTERIA)
        print(f"[{i}] {odp}")
        print(f"    dokładna asercja: {dokladna}")
        print(f"    kryteria oceny:   {wynik.opis()}\n")

    print("Wniosek: dokładna asercja odrzuca dobre odpowiedzi [2] i [3], bo sprawdza zdanie.\n"
          "Kryteria przepuszczają [1]–[3] i odrzucają [4]–[6] z powodem, z którym zespół wie, co zrobić.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
