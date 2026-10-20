# 05 — Evidence to Release Decision

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post **From Evidence to a Release Decision**.

The previous post ([folder 04](../04-Collecting-Evidence/)) was about collecting evidence. This one is about reading it without fooling yourself, and turning it into a rule that says when a change ships. Every script ends in one of five decisions: **ship, roll out gradually, hold, roll back, or collect more data**.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English.

### Run it

```bash
python stratified_report.py                     # the average lies in two ways
python pairwise.py                              # which version is better? compare in pairs
python incident_replay.py                       # without logs, failures turn into arguments
python release_gate.py                          # the release gate for candidate v2
python release_gate.py data/candidate_v3.jsonl  # ...and for the fixed version v3
python exercise/check_my_gate.py                # the exercise from the post
python -m unittest -v test_release              # unit tests
```

### The data

`data/` holds evaluation results for a support assistant, one scored case per line (`slice`, `score` 0–10, `policy_failure`, `critical`, `latency_ms`, `markers`). `generate_data.py` rebuilds them, always with the same content.

| File | What it is |
|---|---|
| `baseline_v1.jsonl` | The version in production today |
| `candidate_v2.jsonl` | New prompt and retrieval: better average, weak slices, one privacy leak |
| `candidate_v3.jsonl` | v2 after fixes |
| `candidate_v3_quick.jsonl` | Only the first 30 cases of v3 |
| `canary_v3.jsonl` | Production sample from the canary after release |

You can run every script on your own results in the same format.

### The average lies in two ways (`stratified_report.py`)

Candidate v2 has a mean of **8.4** out of 10. Sounds good. The breakdown by slice says otherwise: English support 8.8, billing 8.6, Spanish support **6.9**, policy edge cases **5.8**. The average was not false. It was incomplete.

The second lie: one case out of 300 scored 0 because of a privacy leak. A random review of 100 cases would have missed it about two times out of three. The script lists cases with **markers** (low confidence, missing citation, judge disagreement, unusual tool call). A marker does not prove a failure, but it tells you where to look, and here it points straight at the leak.

### Compare in pairs (`pairwise.py`)

The same 16 questions answered by the old prompt (A) and the new one (B). A judge sees “Answer 1” and “Answer 2” in random order and picks one, or a tie. Result: B wins 69%, A 12%, ties 19%.

- The **rubric judge** (correct, helpful, safe) gives the same verdicts whatever the order.
- The **naive judge** (longer, more confident, prefers what it reads first) flips verdicts when only the order changes, and disagrees with the rubric on 6 questions.
- **Hard checks still apply:** in one question B beats A and still invents a policy exception. Better than before, still unacceptable.
- The same idea for code: two fixes for a flaky payment test. Both make CI green, but only one would an experienced engineer trust in production.

### Without logs, failures turn into arguments (`incident_replay.py`)

A customer gets a wrong answer (“60 days”), and the engineer's run on a clean machine is correct. An answer-only log confirms the error but cannot explain it. A full context log (input, prompt versions, model and sampling settings, retrieved documents, tool calls, state, feature flags, configuration, output, judge score and reasoning) lets another engineer replay the run and reproduce the same class of failure: a stale policy came from the tool cache. Then the script tests the same question with a clean state and with a dirty one (memory, stale cache, an earlier failed attempt).

### The release gate (`release_gate.py`, `release_gate.json`)

The gate combines several kinds of evidence. Each condition protects against something different: mean ≥ 8.0, lower bound of the 95% CI > 7.5, ≥ 95% of scores at 7 or higher, policy failure rate < 2%, no score below 4, zero critical failures (a hard block), latency increase < 10%. It adds per-slice thresholds and says what happens after release: canary, production sampling, rollback triggers.

| Evidence | Decision | Why |
|---|---|---|
| `candidate_v2` | **HOLD** | a privacy leak, plus weak slices, even though the mean went up |
| `candidate_v3_quick` | **COLLECT MORE DATA** | everything passes, but 30 cases are not enough |
| `candidate_v3` | **ROLL OUT GRADUALLY** | every condition passes; canary 5% for 7 days |
| `candidate_v3` + `--canary data/canary_v3.jsonl` | **ROLL BACK** | Spanish support dropped by 1.8 points in production |

A green light on release day is only the beginning: non-deterministic systems drift. And the gate is not a weekend contract: it is expected to evolve, the way mature rubrics do.

### The exercise from the post

> Take one change you plan to ship and write a release gate for it in plain language. Answer five questions:
> 1. What is the sample, and where does it come from (golden set, live traffic, both)?
> 2. Which slices are risky and get their own thresholds?
> 3. Which failures are a hard blocker, regardless of the average?
> 4. What happens after release: canary, monitoring, rollback conditions?
> 5. What single signal would change your decision from “ship” to “hold”?

1. Run `python exercise/check_my_gate.py` to see a complete example for the support assistant. The script checks every answer, writes the gate as a plain-language document to `output/my_release_gate.md`, and adds the decision for the example evidence.
2. Open `exercise/my_release_gate.json` and replace the answers with your own change. The script flags empty or vague answers: a sample without a size or source, a risky slice without a number, an after-release plan without a rollback condition, or more than one signal.
3. Optional: point `evidence` to your own results file (and gate) to get a decision as well.

If you can answer these, you stopped asking whether the test passed. You started asking whether the evidence is enough.

### Files

| File | Role |
|---|---|
| `stats.py` | Mean with a confidence interval, Wilson interval, grouping by slice |
| `generate_data.py`, `data/` | Evaluation results used by every script |
| `stratified_report.py` | Weak slices, rare disasters and markers |
| `pairwise.py`, `pairwise_cases.json` | Pairwise comparison: rubric judge vs naive judge, hard checks |
| `incident_replay.py` | Answer-only log vs full context log, replay, clean vs dirty state |
| `release_gate.py`, `release_gate.json` | The release gate and the five decisions |
| `exercise/` | The exercise: your release gate and the checker |
| `test_release.py` | Unit tests |
| `output/` | Created by the scripts |

---

## Polski

Przykład do wpisu **„Od dowodów do decyzji o wydaniu”**.

Poprzedni wpis ([folder 04](../04-Collecting-Evidence/)) dotyczył zbierania dowodów. Ten dotyczy tego, jak je czytać, żeby nie oszukać samego siebie, i jak zamienić je w regułę, która mówi, kiedy wypuszczamy zmianę. Każdy skrypt kończy się jedną z pięciu decyzji: **wydać, wdrożyć stopniowo, wstrzymać, wycofać albo zebrać więcej danych**.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku.

### Uruchom

```bash
python stratified_report.py                     # średnia kłamie na dwa sposoby
python pairwise.py                              # która wersja jest lepsza? porównanie parami
python incident_replay.py                       # bez logów awarie stają się kłótniami
python release_gate.py                          # bramka wydania dla kandydata v2
python release_gate.py data/candidate_v3.jsonl  # ...i dla poprawionej wersji v3
python exercise/check_my_gate.py                # ćwiczenie z artykułu
python -m unittest -v test_release              # testy jednostkowe
```

### Dane

`data/` zawiera wyniki ewaluacji asystenta wsparcia, jeden oceniony przypadek na linię (`slice`, `score` 0–10, `policy_failure`, `critical`, `latency_ms`, `markers`). `generate_data.py` odtwarza je, zawsze z tą samą treścią.

| Plik | Co to jest |
|---|---|
| `baseline_v1.jsonl` | Wersja działająca dziś na produkcji |
| `candidate_v2.jsonl` | Nowy prompt i wyszukiwanie: lepsza średnia, słabe przekroje, jeden wyciek danych |
| `candidate_v3.jsonl` | v2 po poprawkach |
| `candidate_v3_quick.jsonl` | Tylko pierwsze 30 przypadków z v3 |
| `canary_v3.jsonl` | Próbka z produkcji podczas canary po wydaniu |

Każdy skrypt możesz uruchomić na własnych wynikach w tym samym formacie.

### Średnia kłamie na dwa sposoby (`stratified_report.py`)

Kandydat v2 ma średnią **8,4** na 10. Brzmi dobrze. Rozbicie na przekroje mówi co innego: wsparcie po angielsku 8,8, rozliczenia 8,6, wsparcie po hiszpańsku **6,9**, przypadki brzegowe polityk **5,8**. Średnia nie była fałszywa. Była niekompletna.

Drugie kłamstwo: jeden przypadek na 300 dostał 0, bo ujawnił prywatne dane. Losowy przegląd 100 przypadków przeoczyłby go mniej więcej dwa razy na trzy. Skrypt wypisuje przypadki z **markerami** (niska pewność, brak cytowania, niezgoda sędziów, nietypowe wywołanie narzędzia). Marker nie dowodzi awarii, ale mówi, gdzie szukać, i tutaj wskazuje prosto na wyciek.

### Porównanie parami (`pairwise.py`)

Te same 16 pytań, na które odpowiada stary prompt (A) i nowy (B). Sędzia widzi „Odpowiedź 1” i „Odpowiedź 2” w losowej kolejności i wybiera jedną albo remis. Wynik: B wygrywa w 69%, A w 12%, remis w 19%.

- **Sędzia z rubryką** (poprawność, pomocność, bezpieczeństwo) daje te same werdykty niezależnie od kolejności.
- **Naiwny sędzia** (dłużej, pewniej, woli to, co czyta pierwsze) zmienia werdykty, gdy zmienia się tylko kolejność, i nie zgadza się z rubryką w 6 pytaniach.
- **Twarde kontrole nadal obowiązują:** w jednym pytaniu B wygrywa z A, a i tak wymyśla wyjątek od polityki. Lepiej niż wcześniej, nadal niedopuszczalnie.
- Ta sama idea dla kodu: dwie poprawki niestabilnego testu płatności. Obie dają zielone CI, ale tylko jednej doświadczony inżynier zaufałby na produkcji.

### Bez logów awarie stają się kłótniami (`incident_replay.py`)

Klient dostaje złą odpowiedź („60 dni”), a uruchomienie inżyniera na czystej maszynie jest poprawne. Log z samą odpowiedzią potwierdza błąd, ale go nie wyjaśnia. Log z pełnym kontekstem (wejście, wersje promptów, model i parametry próbkowania, pobrane dokumenty, wywołania narzędzi, stan, flagi funkcji, konfiguracja, wynik, ocena sędziego i uzasadnienie) pozwala innemu inżynierowi odtworzyć przebieg i zobaczyć tę samą klasę awarii: nieaktualna polityka przyszła z cache narzędzia. Na koniec skrypt testuje to samo pytanie z czystym stanem i z brudnym (pamięć, nieaktualny cache, wcześniejsza nieudana próba).

### Bramka wydania (`release_gate.py`, `release_gate.json`)

Bramka łączy kilka rodzajów dowodów. Każdy warunek chroni przed czymś innym: średnia ≥ 8,0, dolna granica 95% przedziału ufności > 7,5, ≥ 95% ocen 7 lub wyższych, wskaźnik awarii polityk < 2%, żadnej oceny poniżej 4, zero krytycznych awarii (twarda blokada), wzrost opóźnienia < 10%. Do tego progi dla przekrojów i plan na czas po wydaniu: canary, próbkowanie produkcyjne, wyzwalacze wycofania.

| Dowody | Decyzja | Dlaczego |
|---|---|---|
| `candidate_v2` | **WSTRZYMAĆ** | wyciek danych i słabe przekroje, choć średnia wzrosła |
| `candidate_v3_quick` | **ZEBRAĆ WIĘCEJ DANYCH** | wszystko przechodzi, ale 30 przypadków to za mało |
| `candidate_v3` | **WDROŻYĆ STOPNIOWO** | wszystkie warunki spełnione; canary 5% przez 7 dni |
| `candidate_v3` + `--canary data/canary_v3.jsonl` | **WYCOFAĆ** | wsparcie po hiszpańsku spadło na produkcji o 1,8 punktu |

Zielone światło w dniu wydania to dopiero początek: systemy niedeterministyczne dryfują. A bramka nie jest kontraktem na weekend: ma ewoluować, tak jak dojrzałe rubryki.

### Ćwiczenie z artykułu

> Weź jedną zmianę, którą planujesz wypuścić, i zapisz dla niej bramkę wydania prostym językiem. Odpowiedz na pięć pytań:
> 1. Jaka jest próbka i skąd pochodzi (złoty zbiór, ruch na żywo, oba)?
> 2. Które przekroje są ryzykowne i mają własne progi?
> 3. Które awarie są twardym blokerem, niezależnie od średniej?
> 4. Co się dzieje po wydaniu: canary, monitoring, warunki rollbacku?
> 5. Jaki jeden sygnał zmieniłby twoją decyzję z „wydać” na „wstrzymać”?

1. Uruchom `python exercise/check_my_gate.py`, żeby zobaczyć kompletny przykład dla asystenta wsparcia. Skrypt sprawdza każdą odpowiedź, zapisuje bramkę jako dokument prostym językiem w `output/my_release_gate.md` i dodaje decyzję dla przykładowych dowodów.
2. Otwórz `exercise/my_release_gate.json` i wpisz odpowiedzi dla swojej zmiany. Skrypt wskaże puste albo zbyt ogólne odpowiedzi: próbkę bez liczby albo źródła, ryzykowny przekrój bez progu, plan po wydaniu bez warunku wycofania albo więcej niż jeden sygnał.
3. Opcjonalnie wskaż w `evidence` własny plik z wynikami (i bramkę), żeby dostać też decyzję.

Jeśli umiesz na to odpowiedzieć, przestałeś pytać, czy test przeszedł. Zacząłeś pytać, czy dowody wystarczają.

### Pliki

| Plik | Rola |
|---|---|
| `stats.py` | Średnia z przedziałem ufności, przedział Wilsona, grupowanie po przekrojach |
| `generate_data.py`, `data/` | Wyniki ewaluacji używane przez wszystkie skrypty |
| `stratified_report.py` | Słabe przekroje, rzadkie katastrofy i markery |
| `pairwise.py`, `pairwise_cases.json` | Porównanie parami: sędzia z rubryką kontra naiwny, twarde kontrole |
| `incident_replay.py` | Log z samą odpowiedzią kontra pełny kontekst, odtworzenie, czysty i brudny stan |
| `release_gate.py`, `release_gate.json` | Bramka wydania i pięć decyzji |
| `exercise/` | Ćwiczenie: Twoja bramka wydania i skrypt sprawdzający |
| `test_release.py` | Testy jednostkowe |
| `output/` | Tworzony przez skrypty |
