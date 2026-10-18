"""
blind_rating.py — ćwiczenie z części 2, krok 1: ocena na ślepo.

„Napisz cztery przykładowe odpowiedzi: na 10, 7, 4 i 0. Pokaż je komuś z zespołu
 bez ocen i poproś, żeby je ocenił.”

Skrypt pokazuje odpowiedzi w losowej kolejności, BEZ zamierzonych ocen,
pyta o ocenę 0–10 i zapisuje wynik do ratings/<imie>.json.

Użycie:
    python blind_rating.py                          # przykład z indykiem
    python blind_rating.py my_answers.json     # Twoje własne odpowiedzi

Każda osoba z zespołu uruchamia skrypt u siebie (albo po kolei na jednym komputerze),
a potem porównujecie:  python compare_ratings.py ratings/ania.json ratings/bartek.json
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

TU = Path(__file__).parent


def sciezka_odpowiedzi(plik: Path) -> str:
    absolutna = plik.resolve()
    try:
        return absolutna.relative_to(TU.resolve()).as_posix()
    except ValueError:
        return str(absolutna)


def wolna_sciezka_wyniku(katalog: Path, nazwa: str) -> Path:
    wynik = katalog / f"{nazwa}.json"
    numer = 2
    while wynik.exists():
        wynik = katalog / f"{nazwa}-{numer}.json"
        numer += 1
    return wynik


def zapytaj_o_ocene(prompt: str) -> int:
    while True:
        wpis = input(prompt).strip()
        if wpis.isdigit() and 0 <= int(wpis) <= 10:
            return int(wpis)
        print("  Podaj liczbę całkowitą od 0 do 10.")


def main() -> None:
    plik = Path(sys.argv[1]) if len(sys.argv) > 1 else TU / "turkey.json"
    dane = json.loads(plik.read_text(encoding="utf-8"))

    imie = input("Twoje imię (do nazwy pliku z ocenami): ").strip() or "anonim"
    imie_pliku = re.sub(r"[^\w-]", "_", imie.lower())

    odpowiedzi = list(dane["odpowiedzi"])
    random.Random(imie_pliku).shuffle(odpowiedzi)   # każdy widzi inną kolejność

    print("\n" + "=" * 78)
    print(f"PYTANIE KLIENTA: {dane['pytanie']}")
    print("=" * 78)
    print("Skala:")
    for zakres, opis in dane["skala"].items():
        print(f"  {zakres:>5}: {opis}")

    oceny = {}
    for nr, o in enumerate(odpowiedzi, 1):
        print(f"\n--- Odpowiedź {nr}/{len(odpowiedzi)} ---")
        print(o["tekst"])
        oceny[o["id"]] = zapytaj_o_ocene("Twoja ocena (0–10): ")

    katalog = TU / "ratings"
    katalog.mkdir(exist_ok=True)
    wyjscie = wolna_sciezka_wyniku(katalog, imie_pliku)
    wyjscie.write_text(json.dumps({"plik": sciezka_odpowiedzi(plik), "oceniajacy": imie, "oceny": oceny},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nZapisano: {wyjscie.relative_to(TU)}")
    print("Teraz poproś drugą osobę o to samo, a potem:")
    print(f"  python compare_ratings.py {wyjscie.relative_to(TU)} ratings/<druga_osoba>.json")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrzerwano — nic nie zapisano.")
