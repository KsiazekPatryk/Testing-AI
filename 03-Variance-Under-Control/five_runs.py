"""
five_runs.py — ćwiczenie z części 3.

„Uruchom te same dane wejściowe pięć razy. Potem zapisz trzy listy:
  1. różnice nieszkodliwe (inne słowa, inna kolejność, inny format),
  2. różnice, które zmieniają to, czego doświadcza użytkownik,
  3. ustawienia, które mogłyby zmniejszyć wariancję.”

Uruchom:
    python five_runs.py                       # 5 uruchomień, ustawienia produkcyjne
    python five_runs.py --seed 3              # powtarzalna seria
    python five_runs.py --n 20 --temperatura 1.2
    python five_runs.py --top-p 0.9           # sprawdź, czy pokrętło pomaga
    python five_runs.py --bias 48=-100 --bias 12=-100

Raport w Markdown ląduje w reports/, razem z pełną kopertą ewaluacji.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from envelope import zbuduj_koperte, zapisz
from token_model import PYTANIE, SLOTY, Ustawienia, generuj, rozklad

TU = Path(__file__).parent
DANE = {"dzien_dostawy": "w piątek"}
MIGAWKA = "termin-2026-10-16T08:00"
NIESZKODLIWE_SLOTY = {"format": "format odpowiedzi", "dostawa": "sformułowanie zdania o dostawie",
                      "anulowanie": "sformułowanie zdania o anulowaniu", "zakonczenie": "zakończenie"}


def p_problemu(slot: str, u: Ustawienia) -> float:
    return sum(p for k, p in rozklad(SLOTY[slot], u) if k.problem)


def p_problemu_w_odpowiedzi(u: Ustawienia) -> float:
    czysta = 1.0
    for slot in SLOTY:
        czysta *= 1 - p_problemu(slot, u)
    return 1 - czysta


def propozycje(slot: str, u: Ustawienia) -> List[str]:
    """Lista 3: co mogłoby zmniejszyć wariancję w tym miejscu — z policzonym efektem."""
    teraz = p_problemu(slot, u)
    proby = [
        ("top_p 0.9", replace(u, top_p=0.9)),
        ("temperatura 0.3", replace(u, temperatura=0.3)),
        ("temperatura 0", replace(u, temperatura=0)),
    ]
    zle_tokeny = [k.tekst for k in SLOTY[slot] if k.problem and k.tekst]
    if zle_tokeny:
        bias = dict(u.logit_bias, **{t: -100.0 for t in zle_tokeny})
        proby.append((f"logit_bias {{{', '.join(repr(t) + ': -100' for t in zle_tokeny)}}}",
                      replace(u, logit_bias=bias)))
    linie = [f"{nazwa}: ryzyko w tym miejscu {teraz:.1%} -> {p_problemu(slot, nu):.1%}" for nazwa, nu in proby]
    strukturalne = {
        "limit": "Lepiej niż pokrętło: wstaw limit z polityki w kodzie, model tylko go ubiera w słowa.",
        "ostrzezenie": "Lepiej niż pokrętło: dołącz ostrzeżenie deterministycznie albo wymuś sekcję schematem.",
        "dostawa": "Dodaj zakazane twierdzenie ('gwarantujemy', 'na pewno dotrze') do testów — bloker.",
    }
    if slot in strukturalne:
        linie.append(strukturalne[slot])
    return linie


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--temperatura", type=float, default=0.9)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--bias", action="append", default=[], help="TOKEN=WARTOSC, np. 48=-100")
    a = ap.parse_args()

    seed = a.seed if a.seed is not None else random.randrange(10_000)
    bias = {t: float(v) for t, v in (b.split("=", 1) for b in a.bias)}
    u = Ustawienia(temperatura=a.temperatura, top_p=a.top_p, top_k=a.top_k, seed=seed, logit_bias=bias)
    rng = random.Random(seed)

    out: List[str] = []
    def pisz(linia: str = "") -> None:
        print(linia); out.append(linia)

    pisz(f"# Pięć uruchomień: {PYTANIE}")
    pisz(f"Ustawienia: {u.jako_slownik()}")
    pisz(f"Odtworzysz tę serię poleceniem: python five_runs.py --n {a.n} --seed {seed}"
         + (f" --temperatura {a.temperatura}" if a.temperatura != 0.9 else "")
         + (f" --top-p {a.top_p}" if a.top_p != 1.0 else "")
         + (f" --top-k {a.top_k}" if a.top_k else "")
         + "".join(f" --bias {b}" for b in a.bias))
    pisz()

    runy = [generuj(DANE, u, rng) for _ in range(a.n)]
    for i, g in enumerate(runy, 1):
        pisz(f"## Uruchomienie {i}")
        pisz(g.tekst)
        pisz()

    # Lista 1 — nieszkodliwe różnice
    pisz("## Lista 1 — różnice nieszkodliwe")
    jest = False
    for slot, opis in NIESZKODLIWE_SLOTY.items():
        warianty: Dict[str, int] = {}
        for g in runy:
            k = g.wybory[slot]
            if not k.problem:
                t = k.tekst.format(dzien=DANE["dzien_dostawy"]) or "(brak)"
                warianty[t] = warianty.get(t, 0) + 1
        if len(warianty) > 1:
            jest = True
            pisz(f"- {opis}: {len(warianty)} warianty — " + "; ".join(f"„{t}” ×{n}" for t, n in warianty.items()))
    if not jest:
        pisz("- brak (wszystkie uruchomienia sformułowane identycznie)")
    pisz()

    # Lista 2 — różnice, które zmieniają doświadczenie użytkownika
    pisz("## Lista 2 — różnice, które zmieniają to, czego doświadcza użytkownik")
    problematyczne_sloty = set()
    for i, g in enumerate(runy, 1):
        for slot, k in g.wybory.items():
            if k.problem:
                problematyczne_sloty.add(slot)
                pisz(f"- uruchomienie {i}: {k.problem}")
    ryzyko = p_problemu_w_odpowiedzi(u)
    if not problematyczne_sloty and ryzyko > 0:
        pisz("- w tej serii pusta. To nie dowód, że problemu nie ma:")
    elif not problematyczne_sloty:
        pisz("- pusta: przy tych ustawieniach złe kandydaty są poza zasięgiem próbkowania."
             " (W prawdziwym LLM sprawdź to na większej próbie, a nie na pięciu uruchomieniach.)")
    pisz(f"- prawdopodobieństwo problemu w pojedynczej odpowiedzi przy tych ustawieniach: {ryzyko:.1%}")
    pisz(f"- szansa, że {a.n} uruchomień NIE pokaże żadnego problemu: {(1 - ryzyko) ** a.n:.0%}")
    pisz()

    # Lista 3 — ustawienia, które mogłyby zmniejszyć wariancję
    pisz("## Lista 3 — ustawienia, które mogłyby zmniejszyć wariancję")
    sloty_do_analizy = problematyczne_sloty or {s for s in SLOTY if p_problemu(s, u) > 0}
    if not sloty_do_analizy:
        pisz("- przy tych ustawieniach żadne miejsce nie ma ryzykownych kandydatów")
    for slot in sorted(sloty_do_analizy):
        pisz(f"- miejsce '{slot}':")
        for linia in propozycje(slot, u):
            pisz(f"    - {linia}")
    pisz("- Cena: niższa temperatura i top-p zabierają też część nieszkodliwej różnorodności (lista 1).")

    znacznik = datetime.now().strftime("%Y%m%d-%H%M%S")
    raport = TU / "reports" / f"five_runs_{znacznik}.md"
    raport.parent.mkdir(exist_ok=True)
    raport.write_text("\n".join(out) + "\n", encoding="utf-8")
    zapisz(zbuduj_koperte(u, MIGAWKA, "five_runs"),
           {"odpowiedzi": [g.tekst for g in runy], "problemy": [g.problemy for g in runy]},
           TU / "reports" / f"five_runs_{znacznik}_envelope.json")
    print(f"\nRaport: {raport.relative_to(TU)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
