# 09 — Raters and Rubrics

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**Who Evaluates the Evaluators?**](https://paprico.substack.com/p/kto-ocenia-oceniajacych) (in English, also available in Polish).

Rubrics, samples, confidence intervals and statistical tests all rest on one quiet assumption: that someone already decided what the examples mean. Those are the labels. If the labels are wrong, all the statistics built on them are precise counting of the wrong thing. This folder shows, with numbers, how to choose and calibrate raters, why whoever labels the data defines quality, and how to build a rubric that can be applied consistently.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. Agreement measures (Cohen's, weighted and Fleiss' kappa) are written out in `agreement.py`.

### Run it

```bash
python rater_calibration.py        # a rater is an instrument: calibrate before counting
python blind_review.py             # if the reviewer knows which answer is new, the new one wins
python fatigue_drift.py            # gold items catch fatigue and drift
python who_labels.py               # whoever labels the data defines quality
python label_provenance.py         # labels as evidence with a chain of custody
python rubric.py                   # dimensions, anchors, blockers, versions
python agent_fix_review.py         # green tests, a nice diff, and hidden risk
python exercise/audit_my_rubric.py # the exercise from the post
python -m unittest -v test_raters_and_rubrics
```

### Calibrate before counting (`rater_calibration.py`)

Three reviewers score the same 40 support answers twice: first with "Rate the quality from 1 to 10", then with the anchored rubric after one calibration session.

| | Before | After |
|---|---|---|
| Pass rate (≥ 7): Anna / Ben / Chen | 78% / 35% / 55% | 78% / 68% / 70% |
| Pass/fail agreement, all three (Fleiss' kappa) | 0.32 (fair) | 0.71 (substantial) |
| Agreement on the 0–10 scale (weighted kappa) | 0.46–0.57 | 0.87–0.89 |

Same answers, same people; only the instrument changed. The script lists the items with the largest spread, which are the ones to discuss in the calibration session. It then applies arbitration rules written down before counting: 33 items are unanimous, 5 are decided by majority, 2 go to a senior reviewer, and 7 would be "uncertain" if they were part of a release gate. Try `--pass-at 8`.

### Blind review (`blind_review.py`)

60 cases where the old and the new version have the same true quality. Unblinded, the reviewer sees "NEW" and the new answer always comes first: **+1.60 points, the new one wins 45 of 60**. Blinded, with the source hidden and the order random: **+0.08, 23 vs 19**. Being shown first is worth +0.45 by itself. Neither effect is bad will. Both are measurement error, and both favor the version you hope will win.

### Fatigue and drift (`fatigue_drift.py`)

Three sessions of 150 items, with every 5th item a gold item (a known answer, used as an attention check). Anna and Ben stay at 6/6 on gold in every block. From item 91 on, Chen drops to 3/6 and then 2/6, and his pass rate climbs to 80%. Those labels should not be counted as they are. Try `--block 25 --min-gold 0.9`.

### Whoever labels the data defines quality (`who_labels.py`)

60 queries in 5 domains. Each has a polished, popular answer and an expert-grounded one, scored by a generalist, a domain expert, and an LLM judge tuned on the generalist labels.

| Domain | Generalist prefers | Expert prefers | LLM judge prefers |
|---|---|---|---|
| general | tie | tie | tie |
| medical | polished (−2.2) | grounded (+5.8) | polished |
| construction | polished | grounded | polished |
| legal | polished | grounded | polished |

The examples from the post: "best treatment for runner's knee after a marathon" and "best waterproof work boots for a roofer in Phoenix in summer" (`--domain construction`). With flat pay per query, 92% of the medical labels came from four people. In expert domains the LLM judge is within 1 point of the generalist 93% of the time and within 1 point of the expert 18% of the time, with an average confidence of 0.92. The script ends with tiered labeling: who should label what.

### Label provenance (`label_provenance.py`)

An evaluation set of 200 labels. 37 have no record of who made them. Two rubric versions are mixed in one set. 38 of the 43 labels used in the release gate have a problem: no provenance, made by a generalist or an LLM where an expert is needed, or made by a single rater with unknown disagreement. Point it at your own file: `python label_provenance.py your_labels.jsonl`.

### The rubric (`rubric.py`)

- `data/rubric_vague.json` ("1 = bad, 10 = good") fails validation three times.
- `data/rubric_support.json` has five weighted dimensions, anchors at 10/7/4/0, three blockers and a changelog.
- A very polite answer that leaks another customer's address scores a weighted 7.7, which would pass without blockers. The blocker makes it 0.
- The script also contrasts the support weights with a medical-summary rubric (style 5%, a missed red flag is a blocker).
- It leaves out a score made under rubric v1 instead of mixing versions in one experiment.

### Green tests, nice diff (`agent_fix_review.py`)

An agent fixes a failing tenant isolation test. Both patches turn the test green, and patch A is the smaller diff. Patch A moves the authorization check into one controller route and removes it from the shared service. Background jobs and exports lose the check. Scored on functional correctness, security boundary, blast radius, evidence and maintainability, with the blocker "weakens tenant isolation", patch A is blocked and patch B is accepted.

### The exercise from the post

> Take the rubric or instruction that someone uses to score your system's outputs, and check:
> 1. Does every point on the scale have a described anchor, or just "1 = bad, 10 = good"?
> 2. Are there blockers that override every score?
> 3. Do you know who created the labels in your evaluation set, and with what expertise?
>
> If the answer to the third question is "I don't know", that is where to start.

1. Run `python exercise/audit_my_rubric.py`. The example is a typical team-wiki instruction, and it fails all three questions. Anchors 2–9 are missing, there are no blockers, and 37 of the 200 labels have no record.
2. Open `exercise/my_rubric.json` and copy in your own scale and anchors, exactly as written in your instruction. Add your blockers and what you know about who made the labels. Leave unknown fields as `null`.
3. If you have the label file, point `dataset` to it (one JSON label per line, with `created_by`, `rater_type`, `expertise` and `guideline_version`). For comparison: `python exercise/audit_my_rubric.py data/rubric_support.json`.

### Files

| File | Role |
|---|---|
| `agreement.py` | Percent agreement, Cohen's kappa, weighted kappa, Fleiss' kappa |
| `generate_data.py`, `data/` | Example data and rubrics used by every script (always the same content) |
| `rater_calibration.py` | Calibration, overlap and arbitration |
| `blind_review.py` | Blinding: hidden source, random order |
| `fatigue_drift.py` | Gold items, fatigue and drift within a session |
| `who_labels.py` | Generalists vs experts vs an LLM judge, flat pay, tiered labeling |
| `label_provenance.py` | Label cards: who, guideline, expertise, disagreement |
| `rubric.py` | Dimensions, anchors, blockers, specificity, versioning |
| `agent_fix_review.py` | The tenant isolation patch, reviewed with a rubric |
| `exercise/` | The exercise: your rubric and the checker |
| `test_raters_and_rubrics.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Kto ocenia oceniających?”**](https://paprico.substack.com/p/kto-ocenia-oceniajacych) (po angielsku, z wersją po polsku).

Rubryki, próbki, przedziały ufności i testy statystyczne opierają się na jednym cichym założeniu: że ktoś wcześniej zdecydował, co oznaczają przykłady. To są etykiety. Jeśli etykiety są złe, cała statystyka na nich zbudowana jest precyzyjnym liczeniem niewłaściwej rzeczy. Ten folder pokazuje na liczbach, jak dobrać i skalibrować oceniających, dlaczego kto etykietuje, ten definiuje jakość, i jak zbudować rubrykę, której da się używać konsekwentnie.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Miary zgodności (kappa Cohena, ważona i Fleissa) są rozpisane w `agreement.py`.

### Uruchom

```bash
python rater_calibration.py        # oceniający to instrument: kalibracja przed liczeniem
python blind_review.py             # jeśli recenzent wie, która odpowiedź jest nowa, nowa wygrywa
python fatigue_drift.py            # złote przykłady wyłapują zmęczenie i dryf
python who_labels.py               # kto etykietuje, ten definiuje jakość
python label_provenance.py         # etykiety jako dowody z pochodzeniem
python rubric.py                   # wymiary, kotwice, blokery, wersje
python agent_fix_review.py         # zielone testy, ładny diff i ukryte ryzyko
python exercise/audit_my_rubric.py # ćwiczenie z artykułu
python -m unittest -v test_raters_and_rubrics
```

### Kalibracja przed liczeniem (`rater_calibration.py`)

Trzech recenzentów ocenia te same 40 odpowiedzi wsparcia dwa razy: najpierw według „Oceń jakość od 1 do 10”, potem według rubryki z kotwicami, po jednej sesji kalibracyjnej.

| | Przed | Po |
|---|---|---|
| Odsetek zaliczeń (≥ 7): Anna / Ben / Chen | 78% / 35% / 55% | 78% / 68% / 70% |
| Zgodność zalicza/nie zalicza, cała trójka (kappa Fleissa) | 0,32 (słaba) | 0,71 (znaczna) |
| Zgodność na skali 0–10 (kappa ważona) | 0,46–0,57 | 0,87–0,89 |

Te same odpowiedzi i ci sami ludzie, zmienił się tylko instrument. Skrypt wypisuje przykłady z największym rozrzutem, czyli te do omówienia na sesji kalibracyjnej. Potem stosuje zasady arbitrażu zapisane przed liczeniem: 33 przykłady są jednogłośne, 5 rozstrzyga większość, 2 trafiają do starszego recenzenta, a 7 dostałoby etykietę „niepewne”, gdyby były częścią bramki wydania. Spróbuj `--pass-at 8`.

### Ślepa próba (`blind_review.py`)

60 przypadków, w których stara i nowa wersja mają tę samą prawdziwą jakość. Bez ślepej próby recenzent widzi „NOWA”, a nowa odpowiedź zawsze jest pierwsza: **+1,60 punktu, nowa wygrywa 45 z 60**. Ze ślepą próbą, przy ukrytym źródle i losowej kolejności: **+0,08, 23 do 19**. Sama pozycja „pierwsza” jest warta +0,45. Żaden z tych efektów nie jest złą wolą. Oba są błędem pomiarowym i oba sprzyjają wersji, której kibicujesz.

### Zmęczenie i dryf (`fatigue_drift.py`)

Trzy sesje po 150 przykładów, w których co piąty przykład jest złoty (ma znaną odpowiedź i służy jako test uwagi). Anna i Ben mają 6/6 na złotych przykładach w każdym bloku. Od przykładu 91 Chen spada do 3/6, a potem do 2/6, a jego odsetek zaliczeń rośnie do 80%. Tych etykiet nie powinno się liczyć w obecnej postaci. Spróbuj `--block 25 --min-gold 0.9`.

### Kto etykietuje, ten definiuje jakość (`who_labels.py`)

60 zapytań w 5 dziedzinach. Każde ma odpowiedź efektowną i popularną oraz odpowiedź opartą na wiedzy eksperckiej. Każdą ocenia ogólny oceniający, ekspert dziedzinowy i sędzia LLM dostrojony na etykietach ogólnych oceniających.

| Dziedzina | Ogólny oceniający woli | Ekspert woli | Sędzia LLM woli |
|---|---|---|---|
| ogólna | remis | remis | remis |
| medyczna | efektowną (−2,2) | ekspercką (+5,8) | efektowną |
| budowlana | efektowną | ekspercką | efektowną |
| prawna | efektowną | ekspercką | efektowną |

Przykłady z artykułu: „najlepsze leczenie kolana biegacza po maratonie” i „najlepsze wodoodporne buty robocze dla dekarza na lato w Phoenix” (`--domain construction`). Przy tej samej stawce za każde zapytanie 92% etykiet medycznych pochodzi od czterech osób. W dziedzinach eksperckich sędzia LLM mieści się w 1 punkcie od ogólnego oceniającego w 93% przypadków, a od eksperta w 18%, przy średniej pewności 0,92. Na koniec skrypt pokazuje etykietowanie warstwowe, czyli kto powinien etykietować co.

### Pochodzenie etykiet (`label_provenance.py`)

Zbiór ewaluacyjny ma 200 etykiet. 37 z nich nie ma informacji, kto je stworzył. W jednym zbiorze są pomieszane dwie wersje rubryki. 38 z 43 etykiet używanych w bramce wydania ma problem: brak pochodzenia, autor ogólny albo LLM tam, gdzie potrzebny jest ekspert, albo jeden oceniający i nieznana niezgodność. Własny plik: `python label_provenance.py twoje_etykiety.jsonl`.

### Rubryka (`rubric.py`)

- `data/rubric_vague.json` („1 = źle, 10 = dobrze”) trzy razy nie przechodzi walidacji.
- `data/rubric_support.json` ma pięć ważonych wymiarów, kotwice 10/7/4/0, trzy blokery i historię zmian.
- Bardzo uprzejma odpowiedź, która ujawnia adres innego klienta, ma ważony wynik 7,7, więc bez blokerów by przeszła. Bloker daje jej 0.
- Skrypt porównuje też wagi wsparcia z rubryką do podsumowań medycznych (styl 5%, pominięty sygnał alarmowy jest blokerem).
- Ocena wystawiona według wersji v1 jest wyłączona z porównania, zamiast mieszać wersje w jednym eksperymencie.

### Zielone testy, ładny diff (`agent_fix_review.py`)

Agent naprawia test izolacji klientów (tenantów), który nie przechodzi. Obie poprawki dają zielony test, a poprawka A ma mniejszy diff. Poprawka A przenosi kontrolę autoryzacji do jednej trasy kontrolera i usuwa ją ze wspólnego serwisu. Zadania w tle i eksporty tracą kontrolę. Według rubryki z wymiarami (poprawność funkcjonalna, granica bezpieczeństwa, promień rażenia, dowody, utrzymywalność) i blokerem „osłabia izolację” poprawka A jest zablokowana, a poprawka B przyjęta.

### Ćwiczenie z artykułu

> Weź rubrykę albo instrukcję, według której ktoś ocenia wyniki twojego systemu, i sprawdź:
> 1. Czy każda ocena na skali ma opisaną kotwicę, czy tylko „1 = źle, 10 = dobrze”?
> 2. Czy istnieją blokery, które przebijają każdy wynik?
> 3. Czy wiesz, kto stworzył etykiety w twoim zbiorze ewaluacyjnym i z jaką ekspertyzą?
>
> Jeśli na trzecie pytanie odpowiedź brzmi „nie wiem”, to od tego warto zacząć.

1. Uruchom `python exercise/audit_my_rubric.py`. Przykład to typowa instrukcja z firmowej wiki i nie przechodzi żadnego z trzech pytań. Brakuje kotwic od 2 do 9, nie ma blokerów, a 37 z 200 etykiet nie ma metryczki.
2. Otwórz `exercise/my_rubric.json` i wpisz swoją skalę i kotwice dokładnie tak, jak są zapisane w instrukcji. Dodaj blokery i to, co wiesz o autorach etykiet. Nieznane pola zostaw jako `null`.
3. Jeśli masz plik z etykietami, wskaż go w `dataset` (jedna etykieta JSON na linię, z polami `created_by`, `rater_type`, `expertise` i `guideline_version`). Dla porównania: `python exercise/audit_my_rubric.py data/rubric_support.json`.

### Pliki

| Plik | Rola |
|---|---|
| `agreement.py` | Zgodność procentowa, kappa Cohena, kappa ważona, kappa Fleissa |
| `generate_data.py`, `data/` | Przykładowe dane i rubryki używane przez wszystkie skrypty (zawsze ta sama treść) |
| `rater_calibration.py` | Kalibracja, nakładanie ocen i arbitraż |
| `blind_review.py` | Ślepa próba: ukryte źródło, losowa kolejność |
| `fatigue_drift.py` | Złote przykłady, zmęczenie i dryf w trakcie sesji |
| `who_labels.py` | Ogólni oceniający a eksperci a sędzia LLM, jedna stawka, etykietowanie warstwowe |
| `label_provenance.py` | Metryczki etykiet: kto, według jakiej wytycznej, z jaką ekspertyzą i niezgodnością |
| `rubric.py` | Wymiary, kotwice, blokery, specyficzność, wersjonowanie |
| `agent_fix_review.py` | Poprawka izolacji tenantów oceniona rubryką |
| `exercise/` | Ćwiczenie: Twoja rubryka i skrypt sprawdzający |
| `test_raters_and_rubrics.py` | Testy jednostkowe |
