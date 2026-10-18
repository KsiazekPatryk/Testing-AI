# 04 — Collecting Evidence

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post **Test Passed. So What? How to Collect Evidence About AI Quality**.

A green test is not a decision yet. The useful question is not “did the test pass?” but “does the evidence support a release decision?”: ship, roll out gradually, hold, roll back, or collect more data. This folder shows the three tools from the post in a form you can run:

1. **Metamorphic testing:** when there is no single correct answer, test relations that must stay true.
2. **Golden set + live samples:** the golden set catches regressions, live samples catch drift, and new failures from live traffic feed the golden set.
3. **Risk-based sampling:** more tests where a failure is most expensive and hardest to undo.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English.

### Run it

```bash
python metamorphic.py                  # tool 1: test relations, not answers
python golden_vs_live.py               # tool 2: golden set vs live samples
python golden_vs_live.py --promote     # tool 2: write the next version of the golden set
python risk_sampling.py                # tool 3: split a test budget by risk
python exercise/check_my_questions.py  # the exercise from the post
python -m unittest -v test_evidence    # unit tests
```

### The system under test

`assistant.py` is a local, fake support assistant for a shoe store. Store policy: shoes can be returned within 30 days. Its wording changes between runs (temperature and seed), and it has realistic bugs planted on purpose:

- mentioning a **gift** triggers an outdated rule (“90 days”),
- a question in **Spanish** hits a wrong locale rule (“14 days”),
- intent detection is keyword-based, so a **typo** (“retrun”) or a **new word** (“refund”) leads to a generic answer with no policy,
- it knows nothing about the **new loyalty policy** (60 days for members) that appears in live traffic.

### Tool 1: metamorphic testing (`metamorphic.py`)

Each case changes the question in a controlled way and checks that the facts in the answer (the return window and the verdict) stay the same. The wording is allowed to change. The facts are not.

| Transformation | Example | Result |
|---|---|---|
| Paraphrase | “I bought shoes a month and a half ago. Can I send them back?” | holds |
| Typos | “Can I retrun my shoes after 45 dyas?” | **breaks**: no policy at all |
| Irrelevant detail | “… They were a birthday gift from my aunt.” | **breaks**: 30 → 90 days |
| Name change | Anna Kowalska → Mohammed Al-Sayed | holds: same risk, same facts |
| Translation | Polish holds, Spanish **breaks**: 30 → 14 days | |
| Weaker search candidate | a keyword-stuffed promo page | **breaks**: pushes the policy article out of first place |

Every broken relation is saved to `output/golden_set_candidates.json`.

### Tool 2: golden set and live samples (`golden_vs_live.py`)

- `golden_set.json`: known edge cases, past incidents, boundaries (day 30 vs day 31). A time-dependent question (“did the price change this week?”) is checked for stable behaviors instead of a frozen answer: cite the official source, show its date, never invent a price.
- `live_samples/2026-W41.jsonl`, `2026-W42.jsonl`: fresh questions from two weeks of traffic, labeled by reviewers.

The golden set passes 10/10, so nothing known regressed. Week 41 passes 11/12, week 42 only 6/12: new wording, a new loyalty policy and more Spanish traffic. That is drift, and only live sampling catches it. Each pass rate comes with a 95% confidence interval. `--promote` writes `output/golden_set_next.json`: the golden set plus the new failures (and the broken metamorphic relations), ready for review.

### Tool 3: risk-based sampling (`risk_sampling.py`)

`features.json` scores eight features on five dimensions: impact, likelihood, detectability, irreversibility and regulatory exposure. The script splits a budget of 600 samples by risk instead of evenly (every feature still gets at least 20), and shows for each feature:

- the chance of seeing at least one failure if 1% of answers fail,
- how high the true failure rate could still be if you see zero failures (about 3/n),
- how hard slices get more samples than their share of traffic (blurry receipt photos vs clear ones),
- which autonomous actions depend on a single signal (the Boeing 737 MAX lesson).

Try `--budget 2000` or `--true-failure-rate 0.005`, or pass your own features file.

### The exercise from the post

> Take three questions your system answers and prepare two metamorphic transformations for each: a paraphrase and a version with typos. If any of them changes the facts in the answer, you have your first candidate for the golden set.

1. Run `python exercise/check_my_questions.py` and see the result for the local assistant. Typos and one paraphrase break the facts, and the script saves them to `output/exercise_golden_candidates.json`.
2. Open `exercise/my_questions.json` and enter your own three questions. For each, write the paraphrase, the facts every answer must keep (as regular expressions, e.g. `30[- ]day`), and optionally the typo version (leave it empty to generate typos).
3. Paste your own system's answers into `"answers"` (`{"original": "...", "paraphrase": "...", "typos": "..."}`). The script then checks your answers instead of the local assistant.

### Files

| File | Role |
|---|---|
| `assistant.py` | Local fake support assistant with planted bugs, and fact extraction from answers |
| `transformations.py` | Typo generator and other controlled transformations |
| `metamorphic.py`, `metamorphic_cases.json` | Tool 1: metamorphic relations |
| `search.py`, `help_center.json` | Help-center search used for the ranking relation |
| `golden_vs_live.py`, `golden_set.json`, `live_samples/` | Tool 2: golden set vs live samples |
| `risk_sampling.py`, `features.json` | Tool 3: risk-based sampling |
| `exercise/` | The exercise: your questions and the checker |
| `test_evidence.py` | Unit tests |
| `output/` | Created by the scripts |

### Plugging in a real model (optional)

Replace the body of `answer()` in `assistant.py` so it calls your API and returns `Reply(text, meta)`. Relations, the golden set and live samples keep working unchanged. For the exercise you don't even need that: paste your system's answers into the JSON file.

---

## Polski

Kod do wpisu **„Test przeszedł. I co z tego? Jak zbierać dowody o jakości AI”**.

Zielony test to jeszcze nie decyzja. Użyteczne pytanie nie brzmi „czy test przeszedł?”, tylko „czy dowody wspierają decyzję o wydaniu?”: wydać, wdrożyć stopniowo, wstrzymać, wycofać albo zebrać więcej danych. Ten folder pokazuje trzy narzędzia z artykułu w formie, którą można uruchomić:

1. **Testowanie metamorficzne:** gdy nie ma jednej poprawnej odpowiedzi, testujesz relacje, które muszą pozostać prawdziwe.
2. **Złoty zbiór i próbki na żywo:** złoty zbiór łapie regresje, próbki na żywo łapią dryf, a nowe awarie z produkcji zasilają złoty zbiór.
3. **Próbkowanie według ryzyka:** więcej testów tam, gdzie błąd jest najdroższy i najtrudniejszy do cofnięcia.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku.

### Uruchom

```bash
python metamorphic.py                  # narzędzie 1: testuj relacje, nie odpowiedzi
python golden_vs_live.py               # narzędzie 2: złoty zbiór vs próbki na żywo
python golden_vs_live.py --promote     # narzędzie 2: zapisz nową wersję złotego zbioru
python risk_sampling.py                # narzędzie 3: podział budżetu testów według ryzyka
python exercise/check_my_questions.py  # ćwiczenie z artykułu
python -m unittest -v test_evidence    # testy jednostkowe
```

### Testowany system

`assistant.py` to lokalny, udawany asystent wsparcia sklepu z butami. Polityka sklepu: buty można zwrócić w ciągu 30 dni. Sformułowania zmieniają się między uruchomieniami (temperatura i seed), a w środku są celowo podłożone, realistyczne błędy:

- wzmianka o **prezencie** uruchamia nieaktualną regułę („90 dni”),
- pytanie **po hiszpańsku** trafia w złą regułę lokalizacji („14 dni”),
- rozpoznawanie intencji opiera się na słowach kluczowych, więc **literówka** („retrun”) albo **nowe słowo** („refund”) kończy się ogólnikową odpowiedzią bez polityki,
- asystent nic nie wie o **nowej polityce dla klubu lojalnościowego** (60 dni dla członków), która pojawia się w ruchu na żywo.

### Narzędzie 1: testowanie metamorficzne (`metamorphic.py`)

Każdy przypadek zmienia pytanie w kontrolowany sposób i sprawdza, czy fakty w odpowiedzi (okno zwrotu i werdykt) zostają te same. Sformułowanie może się zmienić. Fakty nie.

| Transformacja | Przykład | Wynik |
|---|---|---|
| Parafraza | „I bought shoes a month and a half ago. Can I send them back?” | relacja trzyma |
| Literówki | „Can I retrun my shoes after 45 dyas?” | **pęka**: brak jakiejkolwiek polityki |
| Nieistotny szczegół | „… They were a birthday gift from my aunt.” | **pęka**: 30 → 90 dni |
| Zmiana imienia | Anna Kowalska → Mohammed Al-Sayed | trzyma: to samo ryzyko, te same fakty |
| Tłumaczenie | polski trzyma, hiszpański **pęka**: 30 → 14 dni | |
| Słabszy kandydat w wyszukiwaniu | strona promocyjna nafaszerowana słowami kluczowymi | **pęka**: wypycha artykuł o polityce z pierwszego miejsca |

Każda złamana relacja trafia do `output/golden_set_candidates.json`.

### Narzędzie 2: złoty zbiór i próbki na żywo (`golden_vs_live.py`)

- `golden_set.json`: znane przypadki brzegowe, dawne incydenty, granice (dzień 30 i dzień 31). Pytanie zależne od czasu („czy cena zmieniła się w tym tygodniu?”) jest sprawdzane pod kątem stabilnych zachowań, a nie zamrożonej odpowiedzi: cytuj oficjalne źródło, pokaż jego datę, nie wymyślaj ceny.
- `live_samples/2026-W41.jsonl`, `2026-W42.jsonl`: świeże pytania z dwóch tygodni ruchu, ocenione przez recenzentów.

Złoty zbiór przechodzi 10/10, więc nic znanego się nie zregresowało. Tydzień 41 przechodzi 11/12, tydzień 42 już tylko 6/12: nowe sformułowania, nowa polityka lojalnościowa i więcej ruchu po hiszpańsku. To dryf i wyłapuje go tylko próbkowanie na żywo. Każdy odsetek ma 95% przedział ufności. `--promote` zapisuje `output/golden_set_next.json`: złoty zbiór plus nowe awarie (i złamane relacje metamorficzne), gotowe do przeglądu.

### Narzędzie 3: próbkowanie według ryzyka (`risk_sampling.py`)

`features.json` ocenia osiem funkcji w pięciu wymiarach: wpływ, prawdopodobieństwo, wykrywalność, odwracalność i ekspozycja regulacyjna. Skrypt dzieli budżet 600 próbek według ryzyka zamiast po równo (każda funkcja dostaje co najmniej 20) i pokazuje dla każdej funkcji:

- szansę, że zobaczysz choć jedną awarię, jeśli zawodzi 1% odpowiedzi,
- jak wysoki może nadal być prawdziwy wskaźnik awarii, gdy nie widzisz żadnej (około 3/n),
- jak trudne przekroje dostają więcej próbek, niż wynosi ich udział w ruchu (rozmazane zdjęcia paragonów kontra wyraźne),
- które autonomiczne działania zależą od jednego sygnału (lekcja z Boeinga 737 MAX).

Spróbuj `--budget 2000` albo `--true-failure-rate 0.005` lub podaj własny plik z funkcjami.

### Ćwiczenie z artykułu

> Weź trzy pytania, na które odpowiada twój system, i dla każdego przygotuj dwie transformacje metamorficzne: parafrazę i wersję z literówkami. Jeśli którakolwiek zmieni fakty w odpowiedzi, masz pierwszego kandydata do złotego zbioru.

1. Uruchom `python exercise/check_my_questions.py` i zobacz wynik dla lokalnego asystenta. Literówki i jedna parafraza psują fakty, a skrypt zapisuje je do `output/exercise_golden_candidates.json`.
2. Otwórz `exercise/my_questions.json` i wpisz swoje trzy pytania. Dla każdego podaj parafrazę, fakty, które każda odpowiedź musi zachować (jako wyrażenia regularne, np. `30[- ]day`), i opcjonalnie wersję z literówkami (zostaw puste, a literówki wygenerują się same).
3. Wklej odpowiedzi swojego systemu do `"answers"` (`{"original": "...", "paraphrase": "...", "typos": "..."}`). Skrypt sprawdzi wtedy Twoje odpowiedzi zamiast lokalnego asystenta.

### Pliki

| Plik | Rola |
|---|---|
| `assistant.py` | Lokalny, udawany asystent wsparcia z podłożonymi błędami i odczyt faktów z odpowiedzi |
| `transformations.py` | Generator literówek i inne kontrolowane transformacje |
| `metamorphic.py`, `metamorphic_cases.json` | Narzędzie 1: relacje metamorficzne |
| `search.py`, `help_center.json` | Wyszukiwarka centrum pomocy do relacji rankingowej |
| `golden_vs_live.py`, `golden_set.json`, `live_samples/` | Narzędzie 2: złoty zbiór kontra próbki na żywo |
| `risk_sampling.py`, `features.json` | Narzędzie 3: próbkowanie według ryzyka |
| `exercise/` | Ćwiczenie: Twoje pytania i skrypt sprawdzający |
| `test_evidence.py` | Testy jednostkowe |
| `output/` | Tworzony przez skrypty |

### Podpięcie prawdziwego modelu (opcjonalnie)

Podmień ciało funkcji `answer()` w `assistant.py`, tak żeby wywoływała Twoje API i zwracała `Reply(text, meta)`. Relacje, złoty zbiór i próbki na żywo działają bez zmian. Do ćwiczenia nie jest to nawet potrzebne: wystarczy wkleić odpowiedzi swojego systemu do pliku JSON.
