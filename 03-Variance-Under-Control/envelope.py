"""
envelope.py — „Loguj pełną kopertę”.

Żeby „ten sam test” był naprawdę tym samym testem, zapisujemy całą kopertę ewaluacji:
model, prompt, narzędzia, dane źródłowe, parametry dekodowania, seed, schemat,
sędzię, czas i infrastrukturę. Jeśli zmieni się którykolwiek element —
porównujesz już coś innego.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from token_model import MODEL_ID, PYTANIE, Ustawienia

WERSJA_PROMPTU = "dostawa-anulowanie-v3"
PROMPT_SYSTEMOWY = ("Jesteś asystentem sklepu. Podawaj termin dostawy z danych, "
                    "limit anulowania zgodnie z polityką i obowiązkowe ostrzeżenia.")
DEFINICJE_NARZEDZI = ["pobierz_termin_dostawy(v2)", "pobierz_polityke_anulowania(v1)"]
SCHEMAT = None  # odpowiedź tekstowa, bez wymuszonego schematu JSON
SEDZIA = {"rodzaj": "reguły", "wersja": "kontrola-faktow-v1"}


def zbuduj_koperte(ustawienia: Ustawienia, migawka_danych: str, przebieg: str,
                    seed_symulacji: Optional[int] = None) -> Dict[str, Any]:
    return {
        "znacznik_czasu": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "przebieg": przebieg,
        "model": {"id": MODEL_ID},
        "prompt": {"wersja": WERSJA_PROMPTU, "systemowy": PROMPT_SYSTEMOWY, "pytanie": PYTANIE},
        "narzedzia": DEFINICJE_NARZEDZI,
        "dane": {"migawka": migawka_danych},
        "dekodowanie": ustawienia.jako_slownik(),
        "symulacja": {"seed": seed_symulacji},
        "schemat": SCHEMAT,
        "sedzia": SEDZIA,
        "infrastruktura": {"python": platform.python_version(), "system": platform.system()},
    }


IGNORUJ = {"znacznik_czasu", "przebieg"}


def porownaj_koperty(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    """Lista elementów koperty, które się różnią (poza znacznikiem czasu)."""
    return [k for k in sorted(set(a) | set(b)) if k not in IGNORUJ and a.get(k) != b.get(k)]


def zapisz(koperta: Dict[str, Any], wyniki: Dict[str, Any], plik: Path) -> None:
    plik.parent.mkdir(parents=True, exist_ok=True)
    plik.write_text(json.dumps({"koperta": koperta, "wyniki": wyniki}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
