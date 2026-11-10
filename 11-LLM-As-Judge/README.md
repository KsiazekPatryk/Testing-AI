# 11 — LLM as a Judge

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**LLM as a Judge: A Powerful Tool, Not an Oracle**](https://paprico.substack.com/p/llm-jako-sedzia-potezne-narzedzie) (in English, also available in Polish).

An LLM judge can evaluate natural-language output that deterministic tests handle poorly, and it is fast and cheap to rerun. But the judge is also a system under test. This folder shows:

- the evaluation hierarchy;
- how a judge fails;
- how to calibrate it against a trusted reviewer;
- why the output of calibration is a set of routing rules, not one accuracy number;
- why the human rating system has to be defined before anything is automated.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. The judge in `judge.py` is an offline, rule-based stand-in for an LLM, so the folder runs anywhere, but it fails the way real judges fail:

- `judge_v1` is the bare prompt ("rate how helpful this reply is, 0–10"). It rewards a warm tone and length, likes the word "refund", wobbles between runs, and does not know what year it is.
- `judge_v2` is the calibrated prompt. It has anchored scores, the policy in context, examples, and blocker checks kept separate from the quality score.

### Run it

```bash
python hierarchy.py                      # the cheapest check that can do the job
python judge_under_test.py               # the judge is a system under test too
python copyright_year.py                 # even a simple task can fail
python calibration.py                    # does the judge score like your best reviewer?
python routing.py                        # apply the routing rules to a new batch
python insulin_case.py                   # the angry customer and the insulin
python raters_first.py                   # raters are part of the product
python exercise/check_my_disagreements.py  # the exercise from the post
python -m unittest -v test_llm_judge
```

### The hierarchy (`hierarchy.py`)

200 outputs go through four layers:

| Layer | Outputs |
|---|---|
| 1. Deterministic checks (schema, banned phrases, missing citation) | 40, all caught without a judge |
| 2. One calibrated judge | 111 |
| 3. Humans: ambiguous cases and a 5% calibration sample | 11 |
| 4. Two judges + human arbitration (high risk only) | 38 |

One run costs $74, compared with $300 for sending everything to humans.

### The judge under test (`judge_under_test.py`)

The same 20 replies are scored 5 times each. With `judge_v1` the score changes for 13 of them, with `judge_v2` for 8. Then come five probe pairs that differ in one thing each: verbosity, a fluent but wrong answer, a warm tone mistaken for policy compliance, a safe short answer, and a subtle policy contradiction. `judge_v1` fails all five and `judge_v2` passes all five.

### The copyright year (`copyright_year.py`)

The prompt says "The current year is 2026". The judge trusts its own sense of time anyway and calls "© 2026" outdated because "2026 is in the future". It gets 3 of 10 footers right, while a ten-line deterministic check gets 10 of 10. When neither works, turn the category off.

### Calibration (`calibration.py`)

A trusted reviewer scored 240 replies with the same rubric.

1. **The headline looks fine.** `judge_v2` is within 1 point of the reviewer 79% of the time, with a pass/fail κ of 0.78. But the privacy segment hides a pattern: the 26 replies the judge scored 10 get 6.2 from the reviewer. They over-share an address or a name, and the judge reads "I can confirm" as diligence.
2. **Four fixes, cheapest first:**
   1. *Examples in the prompt.* `judge_v1` → `judge_v2`: within 1 point rises from 39% to 79%, and pass/fail agreement from 62% to 89%.
   2. *Blockers kept separate from the score.* The checks catch all 37 replies the reviewer scored 4 or lower.
   3. *A per-segment correction.* It is learned on half of the data and checked on the other half. In privacy, the mean error falls from 2.50 to 0.44 and pass/fail agreement rises from 53% to 97%.
   4. *Routing rules,* written to `output/routing_rules.json`:

| Segment | Route | Audit |
|---|---|---|
| refunds | automatic | 5% |
| general | automatic, corrected | 20% |
| privacy | automatic, corrected | 20% |
| medical | human (high risk) | 100% |
| any segment, blocker found | blocks the release | |

`routing.py` applies these rules to 120 new replies. 66 are scored automatically, 13 go to a human audit, 13 go to the human queue, and 28 block the release.

### The angry customer and the insulin (`insulin_case.py`)

"Your driver left my $312 order IN THE RAIN, including my insulin."

| Reply | Anchor | v1 | v2, reply only | v2 + customer message |
|---|---|---|---|---|
| A: recognizes the risk, escalates, checks before refunding | 10 | 8 | 10 | 10 |
| B: apology, general refund path, no escalation | 6 | 8 | 8 | 6 |
| C: friendly, refund approved without checking | 3 | 10 | 3 | 3 |
| D: argues with the customer | 0 | 3 | 0 | 0 |
| E: same as B, much warmer | 6 | 10 | 8 | 6 |

The bare judge rewards sounding empathetic. Without the customer's message, even the calibrated judge cannot know the case is about insulin, which makes missing context a calibration finding too.

### Raters are part of the product (`raters_first.py`)

- **Check the humans first.** Two trained reviewers agree within 1 point 96% of the time (κ 0.86).
- **Look at where they split.** All 9 of their big disagreements are on "vague" replies, which is a preference to settle in the rubric.
- **Only then compare the judge.** It is as close to the trusted reviewer as a second human in every segment except privacy, so privacy is not automated until it has been calibrated.

### The exercise from the post

> Find ten cases where a human and the LLM judge (or two raters) gave different scores. Do not average them. Put each case into one of five categories: ambiguous rubric, missing context, legitimate preference difference, judge error, rater expertise gap. If most cases land in the first category, the problem is the definition of quality, not the model and not the judge.

1. Run `python exercise/check_my_disagreements.py`. It refuses to average the scores, lists every case, and tallies the categories. In the example, 6 of 10 cases are an ambiguous rubric, so the definition of quality is the problem.
2. Replace `exercise/my_disagreements.csv` with your own ten cases. It needs the columns `human_score`, `judge_score` and `category`, and `case` and `note` are optional. The categories are `ambiguous_rubric`, `missing_context`, `preference`, `judge_error` and `expertise_gap`.

### Files

| File | Role |
|---|---|
| `judge.py` | Offline judge: `judge_v1` (bare prompt), `judge_v2` (calibrated, with blocker checks), the copyright judge |
| `metrics.py` | Within-k agreement, pass/fail agreement, Cohen's kappa |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `hierarchy.py` | Deterministic checks → one judge → humans → several judges, with costs |
| `judge_under_test.py` | Consistency between runs and probe pairs for known biases |
| `copyright_year.py` | A simple task the judge fails, and a deterministic check that does not |
| `calibration.py` | Judge vs human, patterns, four fixes, routing rules |
| `routing.py` | The routing rules applied to a new batch |
| `insulin_case.py` | The post's example with anchored scores |
| `raters_first.py` | Human agreement first, then the judge |
| `exercise/` | The exercise: ten disagreements and the checker |
| `test_llm_judge.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„LLM jako sędzia: potężne narzędzie, nie wyrocznia”**](https://paprico.substack.com/p/llm-jako-sedzia-potezne-narzedzie) (po angielsku, z wersją po polsku).

Sędzia LLM potrafi oceniać odpowiedzi w języku naturalnym, z którymi deterministyczne testy radzą sobie słabo, i jest szybki i tani w powtarzaniu. Ale sędzia też jest systemem pod testem. Ten folder pokazuje:

- hierarchię ewaluacji;
- jak sędzia zawodzi;
- jak skalibrować go względem zaufanego recenzenta;
- dlaczego wynikiem kalibracji są reguły kierowania, a nie jedna liczba trafności;
- dlaczego system ocen ludzkich trzeba zdefiniować, zanim cokolwiek zautomatyzujesz.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Sędzia w `judge.py` to regułowy zamiennik LLM, który działa offline, więc folder uruchomisz wszędzie. Zawodzi jednak tak, jak zawodzą prawdziwi sędziowie:

- `judge_v1` to goły prompt („oceń, jak pomocna jest odpowiedź, 0–10”). Nagradza ciepły ton i długość, lubi słowo „refund”, waha się między uruchomieniami i nie wie, który jest rok.
- `judge_v2` to skalibrowany prompt. Ma oceny z kotwicami, politykę w kontekście, przykłady i sprawdzanie blokerów oddzielone od oceny jakości.

### Uruchom

```bash
python hierarchy.py                      # najtańsza kontrola, która wystarczy
python judge_under_test.py               # sędzia też jest systemem pod testem
python copyright_year.py                 # nawet proste zadanie może się wyłożyć
python calibration.py                    # czy sędzia ocenia jak twój najlepszy recenzent?
python routing.py                        # reguły kierowania na nowej partii
python insulin_case.py                   # wściekły klient i insulina
python raters_first.py                   # oceniający to też część produktu
python exercise/check_my_disagreements.py  # ćwiczenie z artykułu
python -m unittest -v test_llm_judge
```

### Hierarchia (`hierarchy.py`)

200 wyników przechodzi przez cztery warstwy:

| Warstwa | Wyniki |
|---|---|
| 1. Kontrole deterministyczne (schemat, zakazane frazy, brak cytowania) | 40, wszystkie wyłapane bez sędziego |
| 2. Jeden skalibrowany sędzia | 111 |
| 3. Ludzie: przypadki niejednoznaczne i 5% próbki kalibracyjnej | 11 |
| 4. Dwóch sędziów + arbitraż człowieka (tylko wysokie ryzyko) | 38 |

Jedno uruchomienie kosztuje 74 USD, a wysłanie wszystkiego do ludzi kosztowałoby 300 USD.

### Sędzia pod testem (`judge_under_test.py`)

Te same 20 odpowiedzi jest ocenianych po 5 razy. U `judge_v1` ocena zmienia się dla 13 z nich, u `judge_v2` dla 8. Potem pięć par sond, z których każda różni się jedną rzeczą: rozwlekłość, płynna, ale błędna odpowiedź, ciepły ton pomylony ze zgodnością z polityką, bezpieczna krótka odpowiedź i subtelna sprzeczność z polityką. `judge_v1` oblewa wszystkie pięć, a `judge_v2` przechodzi wszystkie.

### Rok w stopce (`copyright_year.py`)

Prompt mówi „The current year is 2026”. Sędzia i tak ufa własnemu poczuciu czasu i uznaje „© 2026” za nieaktualne, bo „2026 to przyszłość”. Dobrze ocenia 3 z 10 stopek, a dziesięciolinijkowa kontrola deterministyczna 10 z 10. Gdy nie działa ani jedno, ani drugie, wyłącz tę kategorię.

### Kalibracja (`calibration.py`)

Zaufany recenzent ocenił 240 odpowiedzi według tej samej rubryki.

1. **Ogólny wynik wygląda dobrze.** `judge_v2` mieści się w 1 punkcie od recenzenta w 79% przypadków, przy κ dla zalicza/nie zalicza 0,78. Ale segment prywatności ukrywa wzorzec: 26 odpowiedzi, którym sędzia dał 10, dostaje od recenzenta 6,2. Ujawniają adres albo nazwisko, a sędzia czyta „I can confirm” jako staranność.
2. **Cztery poprawki, od najtańszej:**
   1. *Przykłady w prompcie.* `judge_v1` → `judge_v2`: odsetek ocen w granicach 1 punktu rośnie z 39% do 79%, a zgodność zalicza/nie zalicza z 62% do 89%.
   2. *Blokery oddzielone od oceny.* Kontrole wyłapują wszystkie 37 odpowiedzi, którym recenzent dał 4 lub mniej.
   3. *Korekta dla segmentu.* Jest wyuczona na połowie danych i sprawdzona na drugiej połowie. W prywatności średni błąd spada z 2,50 do 0,44, a zgodność zalicza/nie zalicza rośnie z 53% do 97%.
   4. *Reguły kierowania,* zapisane w `output/routing_rules.json`:

| Segment | Ścieżka | Audyt |
|---|---|---|
| zwroty | automatycznie | 5% |
| ogólne | automatycznie z korektą | 20% |
| prywatność | automatycznie z korektą | 20% |
| medyczne | człowiek (wysokie ryzyko) | 100% |
| dowolny segment, znaleziony bloker | blokuje wydanie | |

`routing.py` stosuje te reguły do 120 nowych odpowiedzi. 66 jest ocenianych automatycznie, 13 idzie do audytu człowieka, 13 do kolejki ludzi, a 28 blokuje wydanie.

### Wściekły klient i insulina (`insulin_case.py`)

„Your driver left my $312 order IN THE RAIN, including my insulin.”

| Odpowiedź | Kotwica | v1 | v2, sama odpowiedź | v2 + wiadomość klienta |
|---|---|---|---|---|
| A: rozpoznaje ryzyko, eskaluje, sprawdza przed zwrotem | 10 | 8 | 10 | 10 |
| B: przeprosiny, ogólna ścieżka zwrotu, bez eskalacji | 6 | 8 | 8 | 6 |
| C: przyjazna, zwrot zatwierdzony bez sprawdzenia | 3 | 10 | 3 | 3 |
| D: kłóci się z klientem | 0 | 3 | 0 | 0 |
| E: to samo co B, dużo cieplej | 6 | 10 | 8 | 6 |

Goły sędzia nagradza brzmienie empatyczne. Bez wiadomości klienta nawet skalibrowany sędzia nie wie, że chodzi o insulinę, więc brak kontekstu to również wynik kalibracji.

### Oceniający to też część produktu (`raters_first.py`)

- **Najpierw sprawdź ludzi.** Dwóch przeszkolonych recenzentów mieści się w 1 punkcie w 96% przypadków (κ 0,86).
- **Zobacz, gdzie się rozchodzą.** Wszystkie 9 ich dużych rozbieżności dotyczy „ogólnikowych” odpowiedzi, czyli preferencji do ustalenia w rubryce.
- **Dopiero wtedy porównaj sędziego.** Jest tak blisko zaufanego recenzenta jak drugi człowiek w każdym segmencie oprócz prywatności, więc prywatności nie automatyzujesz przed kalibracją.

### Ćwiczenie z artykułu

> Znajdź dziesięć przypadków, w których człowiek i sędzia LLM (albo dwóch oceniających) wystawili różne oceny. Nie uśredniaj ich. Przypisz każdy przypadek do jednej z pięciu kategorii: niejednoznaczna rubryka, brakujący kontekst, uprawniona różnica preferencji, błąd sędziego, luka w ekspertyzie oceniającego. Jeśli większość trafi do pierwszej kategorii, problemem jest definicja jakości, a nie model ani sędzia.

1. Uruchom `python exercise/check_my_disagreements.py`. Skrypt nie uśrednia ocen: wypisuje każdy przypadek i liczy kategorie. W przykładzie 6 z 10 przypadków to niejednoznaczna rubryka, więc problemem jest definicja jakości.
2. Podmień `exercise/my_disagreements.csv` na swoje dziesięć przypadków. Wymagane kolumny to `human_score`, `judge_score` i `category`, a `case` i `note` są opcjonalne. Kategorie to `ambiguous_rubric`, `missing_context`, `preference`, `judge_error` i `expertise_gap`.

### Pliki

| Plik | Rola |
|---|---|
| `judge.py` | Sędzia offline: `judge_v1` (goły prompt), `judge_v2` (skalibrowany, z blokerami), sędzia roku w stopce |
| `metrics.py` | Zgodność w granicach k punktów, zgodność zalicza/nie zalicza, kappa Cohena |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `hierarchy.py` | Kontrole deterministyczne → jeden sędzia → ludzie → kilku sędziów, z kosztami |
| `judge_under_test.py` | Powtarzalność między uruchomieniami i pary sond na znane odchylenia |
| `copyright_year.py` | Proste zadanie, którego sędzia nie umie, i kontrola deterministyczna, która umie |
| `calibration.py` | Sędzia a człowiek, wzorce, cztery poprawki, reguły kierowania |
| `routing.py` | Reguły kierowania zastosowane do nowej partii |
| `insulin_case.py` | Przykład z artykułu z ocenami kotwiczonymi |
| `raters_first.py` | Najpierw zgodność ludzi, potem sędzia |
| `exercise/` | Ćwiczenie: dziesięć rozbieżności i skrypt sprawdzający |
| `test_llm_judge.py` | Testy jednostkowe |
