"""
dwa_przebiegi.py — „Dwa przebiegi zamiast jednego” z części 3.

Uruchom:  python dwa_przebiegi.py            (domyślnie 300 zapytań na przebieg)
          python dwa_przebiegi.py --n 1000

PRZEBIEG STABILNY:    temperatura 0, stały seed, zamrożona migawka danych, stabilne narzędzia.
                      Pytanie: czy system potrafi zrobić właściwą rzecz bez zbędnej losowości?
PRZEBIEG PRODUKCYJNY: temperatura 0.9, dane na żywo (w trakcie router zmienia termin dostawy),
                      prawdziwe opóźnienia z ponowieniami.
                      Pytanie: czy nadal robi właściwą rzecz, gdy wraca prawdziwy świat?

Wariancję raportujemy OSOBNO dla każdego wymiaru — jedna zbiorcza liczba ukryłaby
dokładnie ten rodzaj niestabilności, który odczują użytkownicy.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from statistics import quantiles
from typing import Dict, List, Tuple

from koperta import porownaj_koperty, zapisz, zbuduj_koperte
from model_tokenowy import Generacja, Ustawienia, generuj

TU = Path(__file__).parent


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% przedział ufności dla odsetka (metoda Wilsona)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    mianownik = 1 + z * z / n
    srodek = (p + z * z / (2 * n)) / mianownik
    margines = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / mianownik
    return max(0.0, srodek - margines), min(1.0, srodek + margines)


def przebieg(n: int, produkcyjny: bool, seed: int):
    rng = random.Random(seed)
    if produkcyjny:
        u = Ustawienia(temperatura=0.9, seed=None)
        migawka = "na-zywo"
    else:
        u = Ustawienia(temperatura=0.0, seed=42)
        migawka = "termin-2026-10-16T08:00 (zamrożona)"

    wyniki: List[Generacja] = []
    dni: List[str] = []
    opoznienia: List[float] = []
    for i in range(n):
        if produkcyjny:
            # Dane na żywo: po 70% zapytań router przesuwa dostawę na sobotę. Zasadna zmiana świata.
            dzien = "w piątek" if i < 0.7 * n else "w sobotę"
            ms = rng.lognormvariate(math.log(450), 0.25)
            if rng.random() < 0.02:          # ponowienie po timeoucie narzędzia
                ms += rng.uniform(3000, 8000)
        else:
            dzien = "w piątek"
            ms = rng.uniform(380, 420)       # stuby narzędzi, stały czas
        wyniki.append(generuj({"dzien_dostawy": dzien}, u, rng))
        dni.append(dzien)
        opoznienia.append(ms)
    return u, migawka, wyniki, dni, opoznienia


def podsumuj(wyniki: List[Generacja], dni: List[str], opoznienia: List[float]) -> Dict[str, object]:
    n = len(wyniki)
    def licz(slot: str) -> int:
        return sum(1 for g in wyniki if g.wybory[slot].problem)
    q = quantiles(opoznienia, n=100)
    return {
        "n": n,
        "unikalne_teksty": len({g.tekst for g in wyniki}),
        "lista_proc": sum(g.wybory["format"].tekst == "lista" for g in wyniki) / n,
        "zly_limit": licz("limit"),
        "gwarancja": licz("dostawa"),
        "bez_ostrzezenia": licz("ostrzezenie"),
        "sobota": sum(d == "w sobotę" for d in dni),
        "p50": q[49], "p95": q[94], "p99": q[98],
        "ponad_2s": sum(o > 2000 for o in opoznienia),
    }


def proc(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k / n:6.1%} [{lo:.1%}–{hi:.1%}]"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()

    u_s, mig_s, w_s, d_s, o_s = przebieg(a.n, produkcyjny=False, seed=a.seed)
    u_p, mig_p, w_p, d_p, o_p = przebieg(a.n, produkcyjny=True, seed=a.seed)
    s, p = podsumuj(w_s, d_s, o_s), podsumuj(w_p, d_p, o_p)
    n = a.n

    print(f"Ten sam zestaw: {n} zapytań „Kiedy dotrze moje zamówienie i do kiedy mogę je anulować?”")
    print("Odsetki z 95% przedziałem ufności (Wilson).\n")
    print(f"{'wymiar':32} {'STABILNY':>24} {'PRODUKCYJNY':>24}   rodzaj")
    print("-" * 100)
    wiersze = [
        ("sformułowanie (unikalne teksty)", f"{s['unikalne_teksty']}", f"{p['unikalne_teksty']}", "akceptowalne"),
        ("struktura (odsetek list)", f"{s['lista_proc']:.0%}", f"{p['lista_proc']:.0%}", "akceptowalne*"),
        ("fakty: zły limit anulowania", proc(s["zly_limit"], n), proc(p["zly_limit"], n), "BLOKUJĄCE"),
        ("obietnica 'gwarantujemy'", proc(s["gwarancja"], n), proc(p["gwarancja"], n), "BLOKUJĄCE"),
        ("pominięte ostrzeżenie", proc(s["bez_ostrzezenia"], n), proc(p["bez_ostrzezenia"], n), "BLOKUJĄCE"),
        ("dane: dostawa przesunięta", proc(s["sobota"], n), proc(p["sobota"], n), "zasadna zmiana świata"),
        ("opóźnienie p50 / p95 / p99 [ms]",
         f"{s['p50']:.0f} / {s['p95']:.0f} / {s['p99']:.0f}",
         f"{p['p50']:.0f} / {p['p95']:.0f} / {p['p99']:.0f}", "zależy od SLO"),
        ("odpowiedzi wolniejsze niż 2 s", proc(s["ponad_2s"], n), proc(p["ponad_2s"], n), "zależy od SLO"),
    ]
    for w in wiersze:
        print(f"{w[0]:32} {w[1]:>24} {w[2]:>24}   {w[3]}")
    print("  * dopóki format nie jest kontraktem (np. API oczekuje JSON-a)")

    blokery_s = s["zly_limit"] + s["gwarancja"] + s["bez_ostrzezenia"]
    blokery_p = p["zly_limit"] + p["gwarancja"] + p["bez_ostrzezenia"]
    print("\nInterpretacja:")
    if blokery_s == 0 and blokery_p > 0:
        print("  - Przebieg stabilny jest czysty, produkcyjny nie. Przypadek testowy jest w porządku;")
        print("    awarie biorą się z próbkowania modelu. Kierunek: pokrętła albo deterministyczne fakty w kodzie.")
    elif blokery_s > 0:
        print("  - Błędy już w przebiegu stabilnym: problem jest w samym systemie (prompt, dane, logika),")
        print("    nie w losowości. Pokrętła tego nie naprawią.")
    else:
        print("  - Oba przebiegi czyste na tej próbie — sprawdź górną granicę przedziału ufności, zanim uznasz, że ryzyka nie ma.")
    print("  - Przesunięcie dostawy na sobotę w przebiegu produkcyjnym to NIE błąd modelu: zmienił się świat.")
    print("    Widać to tylko dlatego, że migawka danych jest częścią koperty.")
    print("  - Średnie opóźnienie wygląda dobrze w obu przebiegach; ogon (p99) mówi co innego.")

    k_s = zbuduj_koperte(u_s, mig_s, "stabilny", seed_symulacji=a.seed)
    k_p = zbuduj_koperte(u_p, mig_p, "produkcyjny", seed_symulacji=a.seed)
    print(f"\nRóżnice w kopertach obu przebiegów: {', '.join(porownaj_koperty(k_s, k_p))}")
    print("  -> To celowo dwa różne testy. Porównujesz je, żeby rozdzielić źródła awarii, nie żeby uśrednić.")

    katalog = TU / "raporty"
    zapisz(k_s, s, katalog / "przebieg_stabilny.json")
    zapisz(k_p, p, katalog / "przebieg_produkcyjny.json")
    print(f"\nKoperty i wyniki zapisane w {katalog.relative_to(TU)}/")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
