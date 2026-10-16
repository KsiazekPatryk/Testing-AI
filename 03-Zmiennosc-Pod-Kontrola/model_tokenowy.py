"""
model_tokenowy.py — miniaturowy model językowy z prawdziwym próbkowaniem.

Bez klucza API i bez internetu, ale pokrętła działają naprawdę:
temperatura, top-p, top-k, seed i logit bias zmieniają rozkład dokładnie tak,
jak opisuje artykuł (logity -> logit bias -> temperatura -> softmax -> top-k -> top-p).

Uproszczenie: odpowiedź składa się z kilku „miejsc” (slotów). W każdym model wybiera
jeden fragment tekstu z listy kandydatów z własnymi logitami. Dla czytelności
fragment = jeden „token”. Prawdziwy LLM robi to samo, tylko dla tysięcy tokenów po kolei.

Scenariusz: klient pyta „Kiedy dotrze moje zamówienie i do kiedy mogę je anulować?”
Polityka sklepu: anulowanie do 24 godzin przed wysyłką; zamówienie zawiera produkty
chłodzone, więc ostrzeżenie o odbiorze osobistym jest obowiązkowe.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

MODEL_ID = "lokalny-model-tokenowy-v1"
PYTANIE = "Kiedy dotrze moje zamówienie i do kiedy mogę je anulować?"


@dataclass
class Kandydat:
    tekst: str
    logit: float
    problem: Optional[str] = None   # None = akceptowalny; inaczej opis problemu dla użytkownika


# Logity „wytrenowanego” modelu. Złe kandydaty mają niskie logity — rzadkie, ale możliwe.
SLOTY: Dict[str, List[Kandydat]] = {
    "format": [
        Kandydat("akapit", 1.5),
        Kandydat("lista", 1.0),
    ],
    "dostawa": [
        Kandydat("Oczekiwana dostawa: {dzien}.", 2.0),
        Kandydat("Paczka powinna dotrzeć {dzien}.", 1.8),
        Kandydat("Dostawę zaplanowaliśmy {dzien}.", 1.2),
        Kandydat("Paczka dotrze {dzien} — gwarantujemy to.", -0.3,
                  problem="obietnica, której system nie może zagwarantować"),
    ],
    "anulowanie": [
        Kandydat("Anulować możesz do", 2.0),
        Kandydat("Anulowanie jest możliwe do", 1.7),
        Kandydat("Masz czas na anulowanie do", 1.0),
    ],
    "limit": [
        Kandydat("24", 4.0),
        Kandydat("48", 0.5, problem="zły limit anulowania (48 h zamiast 24 h)"),
        Kandydat("12", -0.5, problem="zły limit anulowania (12 h zamiast 24 h)"),
    ],
    "ostrzezenie": [
        Kandydat("Zamówienie zawiera produkty chłodzone — ktoś musi je odebrać osobiście.", 2.2),
        Kandydat("", 0.0, problem="pominięte obowiązkowe ostrzeżenie"),
    ],
    "zakonczenie": [
        Kandydat("Daj znać, jeśli mogę jeszcze pomóc.", 1.0),
        Kandydat("", 0.8),
        Kandydat("Miłego dnia!", 0.5),
    ],
}


@dataclass
class Ustawienia:
    temperatura: float = 0.9
    top_p: float = 1.0
    top_k: Optional[int] = None
    seed: Optional[int] = None
    logit_bias: Dict[str, float] = field(default_factory=dict)

    def jako_slownik(self) -> dict:
        return {"temperatura": self.temperatura, "top_p": self.top_p, "top_k": self.top_k,
                "seed": self.seed, "logit_bias": dict(self.logit_bias)}


def rozklad(kandydaci: List[Kandydat], u: Ustawienia) -> List[Tuple[Kandydat, float]]:
    """Prawdopodobieństwo każdego kandydata po zastosowaniu pokręteł."""
    logity = [k.logit + u.logit_bias.get(k.tekst, 0.0) for k in kandydaci]

    if u.temperatura <= 0:                       # zachłannie: zawsze najbardziej prawdopodobny
        naj = max(range(len(logity)), key=lambda i: logity[i])
        return [(k, 1.0 if i == naj else 0.0) for i, k in enumerate(kandydaci)]

    skalowane = [l / u.temperatura for l in logity]
    m = max(skalowane)
    wykladniki = [math.exp(s - m) for s in skalowane]
    suma = sum(wykladniki)
    p = [w / suma for w in wykladniki]

    kolejnosc = sorted(range(len(p)), key=lambda i: p[i], reverse=True)
    zostaw = set(kolejnosc[: u.top_k] if u.top_k else kolejnosc)

    if u.top_p < 1.0:
        skumulowane, jadro = 0.0, set()
        for i in kolejnosc:
            if i not in zostaw:
                continue
            jadro.add(i)
            skumulowane += p[i]
            if skumulowane >= u.top_p:
                break
        zostaw = jadro

    suma_zostaw = sum(p[i] for i in zostaw)
    return [(k, p[i] / suma_zostaw if i in zostaw else 0.0) for i, k in enumerate(kandydaci)]


@dataclass
class Generacja:
    tekst: str
    wybory: Dict[str, Kandydat]

    @property
    def problemy(self) -> List[str]:
        return [k.problem for k in self.wybory.values() if k.problem]


def generuj(dane: Dict[str, str], u: Ustawienia, rng: random.Random) -> Generacja:
    wybory: Dict[str, Kandydat] = {}
    for slot, kandydaci in SLOTY.items():
        r = rozklad(kandydaci, u)
        wybory[slot] = rng.choices([k for k, _ in r], weights=[p for _, p in r], k=1)[0]

    zdania = [
        wybory["dostawa"].tekst.format(dzien=dane["dzien_dostawy"]),
        f"{wybory['anulowanie'].tekst} {wybory['limit'].tekst} godzin przed wysyłką.",
        wybory["ostrzezenie"].tekst,
        wybory["zakonczenie"].tekst,
    ]
    zdania = [z for z in zdania if z]
    if wybory["format"].tekst == "lista":
        tekst = "\n".join(f"- {z}" for z in zdania)
    else:
        tekst = " ".join(zdania)
    return Generacja(tekst, wybory)
