"""
model.py — lokalny, udawany model językowy (bez klucza API, bez internetu).

Udaje LLM na tyle, na ile potrzeba w tym przykładzie:
  * czyta fakty z promptu (linie w formacie "KLUCZ: wartość"),
  * losuje sformułowania — im wyższa temperatura, tym więcej losowości,
  * przy tym samym seedzie zwraca to samo (da się odtworzyć wynik),
  * zwraca metadane platformy (id modelu, fingerprint), tak jak prawdziwe API.

I zachowuje się jak prawdziwy model w jednym nieprzyjemnym szczególe:
gdy brakuje danych o pogodzie, i tak odpowiada płynnie i pewnie.

Chcesz podpiąć prawdziwy model? Podmień ciało funkcji `zapytaj_model`
tak, żeby wysyłała `system` i `prompt` do Twojego API i zwracała OdpowiedzModelu.
Reszta przykładu (logowanie, porównywanie) działa bez zmian.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

MODEL_ID = "lokalny-udawany-model-2026-10"
FINGERPRINT = "fp_local_0001"


@dataclass
class OdpowiedzModelu:
    tekst: str
    model_id: str
    system_fingerprint: str


def zapytaj_model(system: str, prompt: str, *, temperatura: float = 0.7,
                  seed: Optional[int] = None) -> OdpowiedzModelu:
    rng = random.Random(seed)
    fakty = _wczytaj_fakty(prompt)

    def wybierz(warianty: List[str]) -> str:
        # Temperatura 0 => zawsze pierwszy (najbardziej "prawdopodobny") wariant.
        if temperatura <= 0.05:
            return warianty[0]
        # Niska temperatura => częściej pierwszy wariant, wysoka => równomiernie.
        wagi = [1.0 / (i + 1) ** (1.0 / temperatura) for i in range(len(warianty))]
        return rng.choices(warianty, weights=wagi, k=1)[0]

    werdykt = fakty.get("WERDYKT", "")
    okno = fakty.get("OKNO_DOSTAWY", "")
    burza = fakty.get("BURZA_OD", "")
    braki = fakty.get("BRAKI", "brak")

    zdania: List[str] = []
    if werdykt == "kierowca_anulowal":
        zdania.append(wybierz([
            "Niestety kierowca anulował kurs — szukamy zastępstwa i wrócimy z nowym terminem.",
            "Kurs został anulowany przez kierowcę. Przydzielamy nowego i podamy nowe okno dostawy.",
        ]))
    elif werdykt == "zdazymy":
        zdania.append(wybierz([
            f"Tak, zdążymy — dostawa planowana jest {okno}, a burza ma się zacząć od {burza}.",
            f"Spokojnie, zakupy dotrą {okno}, przed zapowiadaną burzą (od {burza}).",
            f"Wygląda dobrze: okno dostawy {okno}, prognoza burzy od {burza}.",
        ]))
    elif werdykt == "przelozyc":
        zdania.append(wybierz([
            f"Burza ma przyjść już od {burza}, a okno dostawy to {okno}. "
            "Zgodnie z zasadami nie dowozimy produktów chłodzonych w deszczu, więc proponujemy przełożenie.",
            f"Niestety prognoza mówi o burzy od {burza}, czyli w trakcie okna {okno}. "
            "Produkty chłodzone nie mogą czekać w deszczu — zaproponujemy nowy termin.",
        ]))
    elif werdykt == "chlodzone_w_torbie":
        zdania.append(wybierz([
            f"Burza może zacząć się w trakcie okna {okno} (od {burza}), "
            "ale produkty chłodzone przywieziemy w torbie termicznej.",
            f"Dostawa {okno} może trafić na początek burzy ({burza}); chłodzone będą w torbie termicznej.",
        ]))
    else:
        # Brak danych o pogodzie. Uczciwa odpowiedź brzmiałaby "nie wiem".
        # Model — jak prawdziwe modele — i tak odpowiada pewnie. To jest cicha degradacja.
        zdania.append(wybierz([
            f"Tak, spokojnie zdążymy przed burzą — dostawa {okno}!",
            f"Nie ma problemu, zakupy będą u Ciebie {okno}, na długo przed burzą.",
        ]))

    if braki and braki != "brak":
        zdania.append(wybierz([
            f"Uwaga: zabrakło: {braki}.",
            f"Niestety niedostępne są: {braki}.",
            f"Jednej rzeczy nie mamy na stanie: {braki}.",
        ]))

    return OdpowiedzModelu(" ".join(zdania), MODEL_ID, FINGERPRINT)


def _wczytaj_fakty(prompt: str) -> Dict[str, str]:
    fakty: Dict[str, str] = {}
    for linia in prompt.splitlines():
        if ":" not in linia:
            continue
        klucz, wartosc = linia.split(":", 1)
        if klucz.strip().isupper():
            fakty[klucz.strip()] = wartosc.strip()
    return fakty
