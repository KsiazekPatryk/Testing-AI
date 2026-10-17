"""
bot.py — chatbot sklepu: „Czy zdążycie przed burzą?”

Budowa celowo przypomina prawdziwy produkt:
  1. narzędzia pobierają stan świata (pogoda, magazyn, kierowca, obietnica dostawy, polityka),
  2. ZWYKŁY KOD liczy werdykt (deterministyczna część — tu AI niepotrzebne),
  3. model językowy tylko ubiera werdykt w słowa (część niedeterministyczna),
  4. każde wywołanie zostawia wpis w logu, z ruchomymi elementami
     rozdzielonymi na trzy grupy: LOSOWOŚĆ, STAN, PLATFORMA (+ ścieżka wykonania).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from model import zapytaj_model

WERSJA_PROMPTU = "burza-prompt-v2"
SYSTEM = (
    "Jesteś asystentem sklepu z dostawą zakupów. Odpowiadaj krótko i uprzejmie. "
    "Opieraj się wyłącznie na faktach podanych w wiadomości."
)


class NarzedzieNiedostepne(Exception):
    pass


# --- Narzędzia (w prawdziwym systemie: wywołania API) -----------------------

def narzedzie_pogoda(swiat: Dict[str, Any]) -> Dict[str, Any]:
    pogoda = swiat["pogoda"]
    if not pogoda.get("dostepna"):
        raise NarzedzieNiedostepne("meteo-api: timeout po 3 s")
    return pogoda


def narzedzie_magazyn(swiat):
    return swiat["magazyn"]


def narzedzie_kierowca(swiat):
    return swiat["kierowca"]


def narzedzie_obietnica(swiat):
    return swiat["obietnica_dostawy"]


def narzedzie_polityka(swiat):
    return swiat["polityka"]


# --- Deterministyczna logika biznesowa --------------------------------------

def _godzina(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def policz_werdykt(pogoda, kierowca, obietnica, polityka, zamowienie) -> str:
    if kierowca["status"] == "anulowany":
        return "kierowca_anulowal"
    if pogoda is None:
        return "nieznany"
    if _godzina(pogoda["burza_od"]) >= _godzina(obietnica["okno_do"]):
        return "zdazymy"
    if zamowienie.get("chlodzone") and not polityka["chlodzone_w_deszczu"]:
        return "przelozyc"
    if not zamowienie.get("chlodzone"):
        return "zdazymy"
    return "chlodzone_w_torbie"


# --- Bot ----------------------------------------------------------------------

def odpowiedz(pytanie: str, swiat: Dict[str, Any], *, temperatura: float = 0.7,
              seed: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    """Zwraca (tekst odpowiedzi, pełny wpis do logu)."""
    wyniki_narzedzi: Dict[str, str] = {}

    try:
        pogoda = narzedzie_pogoda(swiat)
        wyniki_narzedzi["pogoda"] = "ok"
        sciezka = "glowna"
    except NarzedzieNiedostepne as e:
        pogoda = None
        wyniki_narzedzi["pogoda"] = f"BLAD: {e}"
        sciezka = "zapasowa_bez_pogody"   # <- to MUSI trafić do logu

    magazyn = narzedzie_magazyn(swiat); wyniki_narzedzi["magazyn"] = "ok"
    kierowca = narzedzie_kierowca(swiat); wyniki_narzedzi["kierowca"] = "ok"
    obietnica = narzedzie_obietnica(swiat); wyniki_narzedzi["obietnica_dostawy"] = "ok"
    polityka = narzedzie_polityka(swiat); wyniki_narzedzi["polityka"] = "ok"

    werdykt = policz_werdykt(pogoda, kierowca, obietnica, polityka, swiat["zamowienie"])

    prompt = "\n".join([
        f"PYTANIE: {pytanie}",
        f"WERDYKT: {werdykt}",
        f"OKNO_DOSTAWY: dziś {obietnica['okno_od']}–{obietnica['okno_do']}",
        f"BURZA_OD: {pogoda['burza_od'] if pogoda else 'brak danych'}",
        f"BRAKI: {', '.join(magazyn['braki']) or 'brak'}",
    ])

    wynik = zapytaj_model(SYSTEM, prompt, temperatura=temperatura, seed=seed)

    wpis = {
        "zalogowano": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pytanie": pytanie,
        "odpowiedz": wynik.tekst,
        "sciezka": sciezka,
        "werdykt_kodu": werdykt,
        "losowosc": {
            "temperatura": temperatura,
            "seed": seed,
        },
        "stan": {
            "czas_zapytania": swiat.get("czas_zapytania"),
            "pogoda": pogoda,
            "magazyn": magazyn,
            "kierowca": kierowca,
            "obietnica_dostawy": obietnica,
            "polityka": polityka,
            "lokalizacja": swiat["lokalizacja"],
            "wyniki_narzedzi": wyniki_narzedzi,
        },
        "platforma": {
            "model_id": wynik.model_id,
            "system_fingerprint": wynik.system_fingerprint,
            "wersja_promptu": WERSJA_PROMPTU,
        },
    }
    return wynik.tekst, wpis


def wczytaj_swiat(sciezka: Path) -> Dict[str, Any]:
    return json.loads(Path(sciezka).read_text(encoding="utf-8"))


def dopisz_do_logu(plik: Path, wpis: Dict[str, Any]) -> None:
    plik.parent.mkdir(parents=True, exist_ok=True)
    with open(plik, "a", encoding="utf-8") as f:
        f.write(json.dumps(wpis, ensure_ascii=False) + "\n")
