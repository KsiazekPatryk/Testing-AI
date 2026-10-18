"""
explain.py — „Który ruchomy element zmienił odpowiedź?”

Porównuje dwa wpisy z logu i wypisuje różnice pogrupowane na:
LOSOWOŚĆ, STAN, PLATFORMA oraz ŚCIEŻKĘ wykonania.

Użycie z linii poleceń (numery wpisów liczone od 1):
    python explain.py logs/conversations.jsonl 1 2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

GRUPY = {
    "losowosc": "LOSOWOŚĆ  (próbkowanie modelu)",
    "stan": "STAN      (dane, narzędzia, świat)",
    "platforma": "PLATFORMA (model, prompt, dostawca)",
    "sciezka": "ŚCIEŻKA   (która ścieżka wygenerowała odpowiedź)",
}
BRAK_POLA = "<BRAK POLA>"


def splaszcz(d: Any, prefiks: str = "") -> Dict[str, Any]:
    if isinstance(d, dict):
        wynik: Dict[str, Any] = {}
        for k, v in d.items():
            wynik.update(splaszcz(v, f"{prefiks}.{k}" if prefiks else k))
        return wynik
    return {prefiks: d}


def roznice(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, List[Tuple[str, Any, Any]]]:
    wynik: Dict[str, List[Tuple[str, Any, Any]]] = {g: [] for g in GRUPY}
    for grupa in GRUPY:
        pa = splaszcz(a[grupa]) if grupa in a else {grupa: BRAK_POLA}
        pb = splaszcz(b[grupa]) if grupa in b else {grupa: BRAK_POLA}
        for klucz in sorted(set(pa) | set(pb)):
            va, vb = pa.get(klucz, BRAK_POLA), pb.get(klucz, BRAK_POLA)
            if va != vb:
                wynik[grupa].append((klucz or grupa, va, vb))
    return wynik


def wyjasnij(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    linie = []
    if a["odpowiedz"] == b["odpowiedz"]:
        linie.append("Odpowiedzi są identyczne.")
    else:
        linie.append(f"A: {a['odpowiedz']}")
        linie.append(f"B: {b['odpowiedz']}")
    r = roznice(a, b)
    if not any(r.values()):
        linie.append("Żaden zalogowany ruchomy element się nie zmienił.")
        if a["odpowiedz"] != b["odpowiedz"]:
            linie.append("!! Odpowiedź się zmieniła, a logi tego nie tłumaczą — czegoś nie logujesz.")
        return "\n".join(linie)
    linie.append("Co się zmieniło:")
    for grupa, opis in GRUPY.items():
        if r[grupa]:
            linie.append(f"  {opis}")
            for klucz, va, vb in r[grupa]:
                linie.append(f"     - {klucz}: {va!r} -> {vb!r}")
    if r["sciezka"]:
        linie.append("!! Zmieniła się ścieżka wykonania. Płynna odpowiedź może pochodzić "
                     "ze zdegradowanej ścieżki — nie myl jej ze zdrową.")
    elif not r["stan"] and not r["platforma"] and r["losowosc"]:
        linie.append("=> Zmieniła się tylko losowość. Różnica powinna dotyczyć sformułowania, "
                     "nie faktów. Jeśli zmieniły się fakty — to błąd.")
    return "\n".join(linie)


def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    plik, i, j = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    wpisy = [json.loads(l) for l in plik.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(wyjasnij(wpisy[i - 1], wpisy[j - 1]))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
