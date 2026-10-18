"""
compare_ratings.py — ćwiczenie z części 2, krok 2: gdzie rubryka się rozjeżdża?

„Jeśli wasze oceny się rozjadą, właśnie znalazłeś miejsce,
 w którym rubryka wymaga doprecyzowania.”

Użycie:
    python compare_ratings.py                         # gotowy przykład: Ania vs Bartek
    python compare_ratings.py ratings/ty.json ratings/kolega.json [kolejne...]
    python compare_ratings.py ... --sedziowie         # dołącz automatycznych sędziów z judge.py
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path
from statistics import mean, median

from judge import sedzia_naiwny, sedzia_rubryka

TU = Path(__file__).parent
PROG_ROZJAZDU = 2


def main() -> None:
    argumenty = [a for a in sys.argv[1:] if not a.startswith("--")]
    z_sedziami = "--sedziowie" in sys.argv
    pliki = [Path(a) for a in argumenty] or [TU / "ratings" / "example_ania.json",
                                             TU / "ratings" / "example_bartek.json"]
    arkusze = [json.loads(p.read_text(encoding="utf-8")) for p in pliki]
    zrodla = {Path(a["plik"]).resolve() if Path(a["plik"]).is_absolute()
              else (TU / a["plik"]).resolve() for a in arkusze}
    if len(zrodla) != 1:
        raise SystemExit("Nie można porównać ocen z różnych zestawów odpowiedzi.")
    dane = json.loads(next(iter(zrodla)).read_text(encoding="utf-8"))

    ludzie = {a["oceniajacy"]: a["oceny"] for a in arkusze}
    sedziowie = {}
    if z_sedziami:
        sedziowie["sędzia-rubryka"] = {o["id"]: sedzia_rubryka(o["tekst"])[0] for o in dane["odpowiedzi"]}
        sedziowie["sędzia-naiwny"] = {o["id"]: sedzia_naiwny(o["tekst"])[0] for o in dane["odpowiedzi"]}
    kolumny = {**ludzie, **sedziowie}

    nazwy = list(kolumny)
    print(f"Pytanie: {dane['pytanie']}\n")
    print("Rozrzut liczony jest tylko między ludźmi. Gwiazdka (*) przy sędzi = różni się")
    print(f"od mediany ludzi o {PROG_ROZJAZDU}+ pkt.\n")
    print(f"{'id':3} " + " ".join(f"{n[:14]:>14}" for n in nazwy) + f" {'rozrzut':>8} {'zamierzona':>10}")
    print("-" * (15 * len(nazwy) + 24))

    rozjazdy = []
    for o in dane["odpowiedzi"]:
        oceny_ludzi = [ludzie[n][o["id"]] for n in ludzie if o["id"] in ludzie[n]]
        rozrzut = max(oceny_ludzi) - min(oceny_ludzi) if oceny_ludzi else 0
        mediana_ludzi = median(oceny_ludzi) if oceny_ludzi else None
        komorki = []
        for n in nazwy:
            w = kolumny[n].get(o["id"])
            gw = ""
            if n in sedziowie and w is not None and mediana_ludzi is not None \
                    and abs(w - mediana_ludzi) >= PROG_ROZJAZDU:
                gw = "*"
            komorki.append(f"{('-' if w is None else str(w) + gw):>14}")
        zamierzona = o.get("zamierzona_ocena", "?")
        flaga = "  <- ROZJAZD LUDZI" if rozrzut >= PROG_ROZJAZDU else ""
        print(f"{o['id']:3} " + " ".join(komorki) + f" {rozrzut:>8} {zamierzona:>10}{flaga}")
        if rozrzut >= PROG_ROZJAZDU:
            rozjazdy.append(o)

    print("\nŚrednia bezwzględna różnica między parami oceniających:")
    for a, b in combinations(nazwy, 2):
        wspolne = [i for i in kolumny[a] if i in kolumny[b]]
        mad = mean(abs(kolumny[a][i] - kolumny[b][i]) for i in wspolne)
        print(f"  {a} vs {b}: {mad:.1f} pkt")

    if not rozjazdy:
        print("\nBrak rozjazdów >= 2 pkt. Rubryka jest na tyle jasna, że można ją dać sędziemu LLM.")
        return
    print(f"\nRozjazdy (>= {PROG_ROZJAZDU} pkt) — tu rubryka wymaga doprecyzowania:")
    for o in rozjazdy:
        print(f"  [{o['id']}] {o['tekst'][:110]}...")
    print("\nPytania do omówienia w zespole:")
    print("  - Która cecha tej odpowiedzi podbiła ocenę u jednej osoby, a obniżyła u drugiej?")
    print("  - Czy to twarda granica (bloker), czy miękka jakość (punkty)?")
    print("  - Jaki przykład kotwiczący dopisać, żeby następnym razem ocenić tak samo?")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
