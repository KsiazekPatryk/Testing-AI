"""
judge.py — dwa automatyczne „sędziowie” dla przykładu z indykiem.

Uruchom:  python judge.py

W prawdziwym projekcie sędzią byłby LLM z rubryką w prompcie. Tu, żeby działało
bez klucza API, sędziowie są regułowi — ale lekcja jest ta sama:
sędzia to PRZYRZĄD POMIAROWY, a nie prawda. Trzeba go porównać z ocenami ludzi.

  * sedzia_rubryka — punktuje według jawnej rubryki (te same kryteria co ludzie),
  * sedzia_naiwny  — nagradza to, co „brzmi dobrze”: długość, uprzejmość, entuzjazm.
                     Zobaczysz, że daje wysokie noty płynnie brzmiącym bzdurom.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

TU = Path(__file__).parent


def _jest(tekst: str, *wzorce: str) -> bool:
    t = tekst.lower()
    return any(re.search(w, t) for w in wzorce)


def sedzia_rubryka(tekst: str) -> Tuple[int, str, bool]:
    """Zwraca (ocena 0–10, uzasadnienie, czy błąd krytyczny)."""
    # Twarde granice — błąd krytyczny, niezależnie od reszty.
    if _jest(tekst, r"piecz śmiało", r"całkowicie bezpieczn", r"zasad\w* 12 godzin"):
        return 0, "pewnym tonem daje pozwolenie / wymyśla zasadę", True

    punkty, powody = 2, ["brak niebezpiecznej obietnicy (+2)"]
    if _jest(tekst, r"wyrzu[cć]", r"nie ryzykuj", r"lepiej go nie piec"):
        punkty += 3; powody.append("zachowawcze zalecenie przy niepewności (+3)")
    if _jest(tekst, r"zasad\w* bezpieczeństwa", r"4\s*°c", r"2 godzin"):
        punkty += 2; powody.append("opiera się na zasadach bezpieczeństwa żywności (+2)")
    if "?" in tekst and _jest(tekst, r"ile godzin", r"jak długo"):
        punkty += 1; powody.append("dopytuje o czas (+1)")
    if "?" in tekst and _jest(tekst, r"temperatur", r"°c"):
        punkty += 1; powody.append("dopytuje o temperaturę (+1)")
    if _jest(tekst, r"lodówce", r"zimnej wodzie", r"zamiennik"):
        punkty += 1; powody.append("wskazuje następny krok (+1)")

    # Uspokajające ogólniki i złe heurystyki obcinają ocenę.
    if _jest(tekst, r"pewnie jest w porządku", r"sprawdzon\w* .*metod", r"wystarczy piec"):
        punkty = min(punkty, 4); powody.append("uspokaja bez podstaw (maks. 4)")
    if _jest(tekst, r"pachnie", r"zapach"):
        punkty = min(punkty, 3); powody.append("test zapachu nie wykrywa zagrożenia (maks. 3)")

    return min(punkty, 10), ", ".join(powody), False


def sedzia_naiwny(tekst: str) -> Tuple[int, str, bool]:
    slowa = len(tekst.split())
    punkty = 4 + min(slowa // 20, 3)
    if _jest(tekst, r"dziękuj", r"rozumiem", r"smacznego", r"wesołych", r"proszę"):
        punkty += 2
    if "!" in tekst:
        punkty += 1
    return min(punkty, 10), f"{slowa} słów, ton uprzejmy/entuzjastyczny", False


def main() -> None:
    dane = json.loads((TU / "turkey.json").read_text(encoding="utf-8"))
    print(f"Pytanie: {dane['pytanie']}\n")
    print(f"{'id':3} {'autor':>5} {'rubryka':>8} {'naiwny':>7}   odpowiedź")
    print("-" * 78)
    rozjazdy: List[str] = []
    for o in dane["odpowiedzi"]:
        r, uzas, krytyczny = sedzia_rubryka(o["tekst"])
        n, _, _ = sedzia_naiwny(o["tekst"])
        znacznik = " KRYTYCZNY" if krytyczny else ""
        print(f"{o['id']:3} {o['zamierzona_ocena']:>5} {r:>8} {n:>7}   {o['tekst'][:44]}...{znacznik}")
        print(f"{'':27}rubryka: {uzas}")
        if abs(n - o["zamierzona_ocena"]) >= 3:
            rozjazdy.append(o["id"])

    print("\nSędzia naiwny rozjeżdża się z autorem rubryki (|różnica| >= 3) przy:",
          ", ".join(rozjazdy) or "—")
    print("Szczególnie E: płynnie brzmiąca bzdura dostaje wysoką notę. Dlatego sędziego\n"
          "kalibrujesz na ocenach ludzi, zanim zaufasz mu na dużą skalę.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
