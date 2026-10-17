"""
sprawdz_pokrycie.py — ćwiczenie z części 1.

„Wypisz wszystkie ruchome elementy, które mogą zmienić odpowiedź.
 Potem sprawdź, ile z nich faktycznie logujesz.”

Skrypt bierze inwentarz (JSON) i prawdziwy log (JSONL), a następnie sprawdza,
czy każdy element naprawdę występuje w logu — nie „czy myślisz, że go logujesz”.

Użycie:
    python cwiczenie/sprawdz_pokrycie.py
        (domyślnie: inwentarz bota burzowego + logi/rozmowy.jsonl z demo.py)
    python cwiczenie/sprawdz_pokrycie.py MOJ_INWENTARZ.json MOJ_LOG.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

TU = Path(__file__).parent
DOMYSLNY_INWENTARZ = TU / "inwentarz_burza.json"
DOMYSLNY_LOG = TU.parent / "logi" / "rozmowy.jsonl"


def jest_w_logu(wpisy: List[Dict[str, Any]], sciezka: str) -> bool:
    """True, jeśli klucz istnieje i ma wartość w co najmniej jednym wpisie."""
    for wpis in wpisy:
        wezel: Any = wpis
        for czesc in sciezka.split("."):
            if isinstance(wezel, dict) and czesc in wezel:
                wezel = wezel[czesc]
            else:
                wezel = None
                break
        if wezel is not None:
            return True
    return False


def main() -> None:
    inwentarz_plik = Path(sys.argv[1]) if len(sys.argv) > 1 else DOMYSLNY_INWENTARZ
    log_plik = Path(sys.argv[2]) if len(sys.argv) > 2 else DOMYSLNY_LOG

    if not log_plik.exists():
        print(f"Nie ma pliku logu {log_plik}. Najpierw uruchom: python demo.py")
        sys.exit(1)

    inwentarz = json.loads(inwentarz_plik.read_text(encoding="utf-8"))
    wpisy = [json.loads(l) for l in log_plik.read_text(encoding="utf-8").splitlines() if l.strip()]

    print(f"Funkcja: {inwentarz['funkcja']}")
    print(f"Log:     {log_plik}  ({len(wpisy)} wpisów)\n")
    print(f"{'element':42} {'grupa':10} {'status'}")
    print("-" * 78)

    statystyki: Dict[str, List[int]] = {}
    luki = []
    for el in inwentarz["elementy"]:
        pole = el.get("pole_w_logu")
        if pole is None:
            status, ok = "NIE LOGUJEMY", False
        elif jest_w_logu(wpisy, pole):
            status, ok = f"ok  ({pole})", True
        else:
            status, ok = f"BRAK W LOGU — myśleliśmy, że jest ({pole})", False
        if not ok:
            luki.append(el)
        statystyki.setdefault(el["grupa"], [0, 0])
        statystyki[el["grupa"]][0] += ok
        statystyki[el["grupa"]][1] += 1
        print(f"{el['element'][:42]:42} {el['grupa']:10} {status}")

    print("\nPokrycie wg grup:")
    razem_ok = razem = 0
    for grupa, (ok, n) in statystyki.items():
        razem_ok += ok; razem += n
        print(f"  {grupa:10} {ok}/{n}")
    print(f"  {'RAZEM':10} {razem_ok}/{razem}  ({100 * razem_ok / razem:.0f}%)")

    if luki:
        print("\nPytanie kontrolne: gdyby odpowiedź zmieniła się przez któryś z tych elementów,")
        print("czy umiałbyś to wyjaśnić z logów?")
        for el in luki:
            print(f"  - {el['element']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
