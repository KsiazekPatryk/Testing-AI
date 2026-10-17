"""
pokretla.py — ściąga z pokręteł z części 3, ale policzona na żywo.

Uruchom:  python pokretla.py

Dla dwóch miejsc w odpowiedzi (limit anulowania i zdanie o dostawie) pokazuje,
jak temperatura, top-p, top-k i logit bias zmieniają prawdopodobieństwo
każdego kandydata. Na końcu: co robi seed.
"""

from __future__ import annotations

import random
import sys

from model_tokenowy import SLOTY, Ustawienia, generuj, rozklad

KONFIGURACJE = [
    ("temperatura 0 (zachłannie)", Ustawienia(temperatura=0)),
    ("temperatura 0.3", Ustawienia(temperatura=0.3)),
    ("temperatura 0.9 (produkcja)", Ustawienia(temperatura=0.9)),
    ("temperatura 1.5", Ustawienia(temperatura=1.5)),
    ("T 0.9 + top_p 0.9", Ustawienia(temperatura=0.9, top_p=0.9)),
    ("T 0.9 + top_k 2", Ustawienia(temperatura=0.9, top_k=2)),
    ("T 0.9 + top_k 1", Ustawienia(temperatura=0.9, top_k=1)),
    ("T 0.9 + logit_bias 48/12: -100", Ustawienia(temperatura=0.9, logit_bias={"48": -100, "12": -100})),
]


def tabela(slot: str, etykiety: list) -> None:
    kandydaci = SLOTY[slot]
    print(f"\nMiejsce '{slot}' — logity: " + ", ".join(f"{e}={k.logit:+.1f}" for e, k in zip(etykiety, kandydaci)))
    print(f"{'ustawienia':32}" + "".join(f"{e:>12}" for e in etykiety))
    print("-" * (32 + 12 * len(etykiety)))
    for nazwa, u in KONFIGURACJE:
        r = rozklad(kandydaci, u)
        print(f"{nazwa:32}" + "".join(f"{p:>11.1%} " for _, p in r))


def main() -> None:
    tabela("limit", ["24 h (ok)", "48 h (BŁĄD)", "12 h (BŁĄD)"])
    tabela("dostawa", ["Oczekiwana", "Powinna", "Planowana", "GWARANCJA"])
    tabela("ostrzezenie", ["ostrzeżenie", "POMINIĘTE"])

    print("\nCo z tego wynika:")
    print("  - Temperatura 0 usuwa ogon, ale też całą różnorodność sformułowań.")
    print("  - top_p 0.9 odcina rzadkie, złe kandydaty i zostawia kilka dobrych wariantów.")
    print("  - top_k 1 = zawsze najbardziej prawdopodobny (jak temperatura 0).")
    print("  - logit bias celuje w konkretny token — kruche: model myśli tokenami, nie słowami.")

    print("\nSeed: ten sam seed + te same ustawienia + te same dane = ten sam wynik")
    dane = {"dzien_dostawy": "w piątek"}
    u = Ustawienia(temperatura=0.9)
    for seed in (7, 7, 8):
        g = generuj(dane, u, random.Random(seed))
        print(f"  seed={seed}: {g.tekst.replace(chr(10), ' / ')}")
    print("  (U dostawcy API seed to ułatwienie przy debugowaniu, nie kontrakt — chyba że dostawca to gwarantuje.)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
