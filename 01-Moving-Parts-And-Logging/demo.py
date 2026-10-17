"""
demo.py — przykład „Zakupy przed burzą” z części 1.

Uruchom:  python demo.py

Co zobaczysz:
  KROK 1. Logujemy tylko odpowiedź. Odpowiedzi się zmieniają, ale nie wiemy dlaczego.
  KROK 2. Logujemy pełny kontekst. Dla każdej pary rozmów widać, który ruchomy element
          (losowość / stan / platforma / ścieżka) zmienił odpowiedź.
  KROK 3. Ten sam świat, różne seedy: zmienia się tylko losowość.
  KROK 4. Cicha degradacja: API pogody leży, a bot brzmi pewnie.
"""

from __future__ import annotations

import sys
from pathlib import Path

from bot import dopisz_do_logu, odpowiedz, wczytaj_swiat
from wyjasnij import wyjasnij

TU = Path(__file__).parent
PYTANIE = "Czy zdążycie dowieźć moje zakupy na piknik, zanim zacznie się burza?"
LOG = TU / "logi" / "rozmowy.jsonl"
SWIATY = sorted((TU / "swiat").glob("t*.json"))


def naglowek(tekst: str) -> None:
    print("\n" + "=" * 78 + f"\n{tekst}\n" + "=" * 78)


def main() -> None:
    naglowek("KROK 1. Logujemy tylko końcową odpowiedź")
    for i, plik in enumerate(SWIATY, 1):
        tekst, _ = odpowiedz(PYTANIE, wczytaj_swiat(plik), seed=1)
        print(f"[{i}] {tekst}")
    print("\nOdpowiedzi się różnią. Produkt dowiedział się czegoś nowego o świecie,"
          "\nczy zabłądził? Z samych odpowiedzi nie da się tego powiedzieć.")

    naglowek("KROK 2. Logujemy pełny kontekst i pytamy: co zmieniło odpowiedź?")
    wpisy = []
    for plik in SWIATY:
        swiat = wczytaj_swiat(plik)
        _, wpis = odpowiedz(PYTANIE, swiat, seed=1)  # ten sam seed: widać tylko zmiany świata
        dopisz_do_logu(LOG, wpis)
        wpisy.append((plik.stem, swiat["_opis"], wpis))
    for (na, _, a), (nb, opis_b, b) in zip(wpisy, wpisy[1:]):
        print(f"\n--- {na}  ->  {nb}")
        print(f"    (scenariusz: {opis_b})")
        print(wyjasnij(a, b))
    print(f"\nPełne wpisy zapisane w: {LOG.relative_to(TU)}")

    naglowek("KROK 3. Ten sam świat (t1), trzy różne seedy")
    swiat = wczytaj_swiat(SWIATY[0])
    runy = [odpowiedz(PYTANIE, swiat, seed=s)[1] for s in (101, 202, 303)]
    for w in runy:
        print(f"  seed={w['losowosc']['seed']}: {w['odpowiedz']}")
    print()
    print(wyjasnij(runy[0], runy[1]))

    naglowek("KROK 4. Awaria, której nie widać (t3: API pogody nie działa)")
    _, zdrowy = odpowiedz(PYTANIE, wczytaj_swiat(TU / "swiat" / "t2_prognoza_sie_zmienila.json"), seed=7)
    _, chory = odpowiedz(PYTANIE, wczytaj_swiat(TU / "swiat" / "t3_pogoda_nie_dziala.json"), seed=7)
    print(f"  Zdrowa ścieżka:     {zdrowy['odpowiedz']}")
    print(f"  Zdegradowana:       {chory['odpowiedz']}")
    print(f"  Ścieżka w logu:     {chory['sciezka']}")
    print(f"  Wynik narzędzia:    {chory['stan']['wyniki_narzedzi']['pogoda']}")
    print("\n  Obie odpowiedzi brzmią płynnie i pewnie. Tylko pole 'sciezka' w logu mówi,"
          "\n  że druga powstała bez prognozy — i że obiecuje coś, czego system nie wie.")
    print("\nDalej: ćwiczenie z artykułu ->  python cwiczenie/sprawdz_pokrycie.py")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
