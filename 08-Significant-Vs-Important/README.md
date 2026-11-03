# 08 — Significant vs Important

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**Statistically Significant Is Not the Same as Important**](https://paprico.substack.com/p/istotne-statystycznie-to-nie-to-samo) (in English, also available in Polish).

The previous post asked "is this difference real?". This one is the second half: what to do with a result that passed the test. Does the difference matter? Could the sample have seen it at all? How many times did we roll the die before we got a six? And how do you choose a quality metric when different mistakes cost different amounts? This folder covers practical significance, power analysis, the multiple comparisons trap, and precision, recall and F-score.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. Every formula lives in `stats_tools.py`. The results match `scipy.stats`, which the unit tests check against reference values.

### Run it

```bash
python ship_it_slow_down.py           # "ship it, the result is significant": slow down
python two_significances.py           # statistical vs practical significance
python power_analysis.py              # is your flashlight strong enough?
python multiple_comparisons.py        # roll the die a hundred times, remember the best roll
python precision_recall.py            # "better" depends on what a mistake costs
python exercise/check_my_comparison.py  # the exercise from the post
python -m unittest -v test_significance
```

### "Ship it, the result is significant." Slow down (`ship_it_slow_down.py`)

3,000 support conversations. The new returns-policy prompt cut automatic refunds from 18% to 14%, p = 0.003. The slices tell a different story:

| Slice | Old | New |
|---|---|---|
| Low-value orders: auto refunds / complaints | 20.0% / 3.0% | 18.0% / 3.0% |
| Orders above 3000 PLN: escalations | 9.3% | 18.7% (doubled) |
| Angry customers: minutes per conversation | 9.0 | 13.0 |
| Angry customers: defensive tone | 4% | 17% |

A p-value only says that something changed. The report puts it next to the effect size, the interval, failure indicators and the high-risk slices.

### Two kinds of significance (`two_significances.py`)

Every example is judged against `minimum_effect.json`, written before the results: +0.3 points, or 20% fewer policy failures, with guardrails for latency, cost and high-risk slices.

| Example | Statistics | Product |
|---|---|---|
| Score 8.10 → 8.12 on 60,000 conversations, latency +39%, cost +29% | p < 0.001 | not important: the whole interval is below +0.3 |
| Policy failures 6/100 → 2/100 | p = 0.279, CI −10.6 to +1.9 pp | possibly important, needs more data |
| Search relevance +0.02 on 200,000 queries | p < 0.001 | invisible globally, but in the "urgent child passport" slice official sources go 55% → 82% and scam pages 9% → 1% |

### Power analysis (`power_analysis.py`)

- With 40 paired cases (sd of differences 1.2), the evaluation reliably sees only effects of about 0.53 points or more. Its chance of seeing +0.3 is 35%, so +0.3 needs about 128 cases and +0.1 about 1,133.
- Cases per version (95% confidence, 80% power): 10% → 5% failures needs 474; 1% → 0.5% needs 5,065.
- The coding agent with 6/60 vs 4/60 security problems: p = 0.74, power 10%, about 1,138 tasks per version needed. That result should trigger more sampling, not a celebration.
- The simulation runs a real +0.3 effect 2,000 times on 40 cases. Only 37% of the runs see it.

Try `--cases 100 --effect 0.2 --sd 1.0` or `--rate-from 0.02 --rate-to 0.01`.

### Multiple comparisons (`multiple_comparisons.py`)

- With 100 comparisons, 1 − 0.95¹⁰⁰ = 99.4% chance of at least one false alarm.
- The agent search: 200 configurations (prompt × model × tool permissions × judge rubric), all on the same 200 dev tasks. Production gets 84%, the winner 91% (+7 points, p = 0.034 on its own).
- The script answers the post's five questions from the data:
  - The winner was found, not chosen in advance.
  - On a fresh held-out set it gets 82% vs production's 83%.
  - 5 of its passes weakened a test.
  - Over 5 repeated runs: 82.7% vs 82.9%.
- A dashboard with 40 slices: without correction, 4 are "significant", and 2 of them are false alarms. Holm and Benjamini-Hochberg keep only the 2 planned ones.

### Precision, recall, F-score (`precision_recall.py`)

The bug detector from the post: 40 true positives, 10 false alarms, 20 misses, 30 true negatives.

| | Value | When |
|---|---|---|
| precision | 0.80 | |
| recall | 0.67 | |
| F0.5 | 0.77 | false alarms are expensive (PR comments, account locks) |
| F1 | 0.73 | both errors cost about the same |
| F2 | 0.69 | a miss is worse (privacy leaks, security audits) |

The threshold sweep shows that the threshold, not the model, moves the balance. Each F has a different best threshold: F0.5 at 0.60, F2 at 0.25.

### The exercise from the post

> Pick one comparison in front of you: two prompts, two models, two policies. Write down:
> - which test you will use and why,
> - which assumption the test rests on (e.g. independent cases, pairing),
> - which product decision the result should support,
> - what minimum effect would matter to you.
>
> Then also write down what this test cannot tell you. That last list often turns out to be the most valuable.

1. Run `python exercise/check_my_comparison.py`. In the example, the test, the assumption and the decision are in place. But 40 cases have only 35% power for the +0.3 that matters, so you need about 128. The script also proposes items for the "cannot tell" list: cost, rare failures, unplanned slices, 13 comparisons and a single run per case.
2. Open `exercise/my_comparison.json` and describe your own comparison. For a score metric, give the expected sd of the per-case differences. For a rate, set `"kind": "rate"`, `current_rate`, and the relative drop as `value` (0.2 = 20% fewer).
3. Write your own `cannot_tell` list first, then compare it with what the script adds.

### Files

| File | Role |
|---|---|
| `stats_tools.py` | Two proportions (Wilson/Newcombe CI), two means, Fisher, sample size and power, Holm, Benjamini-Hochberg, precision, recall, F-beta |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `minimum_effect.json` | The minimum meaningful effect and guardrails, written before the results |
| `ship_it_slow_down.py` | The refund-policy headline and its slices |
| `two_significances.py` | Statistical vs practical significance, three examples |
| `power_analysis.py` | What a sample can see, sample sizes, the coding agent, a simulation |
| `multiple_comparisons.py` | 1 − 0.95ᵐ, the agent search, a fresh set, corrections for a dashboard |
| `precision_recall.py` | Precision, recall, F0.5/F1/F2 and the threshold |
| `exercise/` | The exercise: your comparison and the checker |
| `test_significance.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Istotne statystycznie to nie to samo co ważne”**](https://paprico.substack.com/p/istotne-statystycznie-to-nie-to-samo) (po angielsku, z wersją po polsku).

Poprzedni wpis pytał: „czy ta różnica jest prawdziwa?”. Ten jest drugą połową: co zrobić z wynikiem, który przeszedł test. Czy różnica ma znaczenie? Czy próbka w ogóle mogła ją zobaczyć? Ile razy rzuciliśmy kostką, zanim wypadła szóstka? I jak wybrać miarę jakości, gdy różne błędy kosztują różnie? Ten folder pokazuje istotność praktyczną, analizę mocy, pułapkę wielokrotnych porównań oraz precyzję, czułość i F-score.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Wszystkie wzory są w `stats_tools.py`. Wyniki zgadzają się z `scipy.stats`, co sprawdzają testy jednostkowe na wartościach referencyjnych.

### Uruchom

```bash
python ship_it_slow_down.py           # „wysyłamy, wynik jest istotny”: zwolnij
python two_significances.py           # istotność statystyczna a praktyczna
python power_analysis.py              # czy twoja latarka jest wystarczająco mocna?
python multiple_comparisons.py        # rzuć kostką sto razy, zapamiętaj najlepszy rzut
python precision_recall.py            # „lepsze” zależy od kosztu pomyłki
python exercise/check_my_comparison.py  # ćwiczenie z artykułu
python -m unittest -v test_significance
```

### „Wysyłamy, wynik jest istotny”. Zwolnij (`ship_it_slow_down.py`)

3000 rozmów wsparcia. Nowy prompt polityki zwrotów zmniejszył automatyczne zwroty z 18% do 14%, p = 0,003. Przekroje mówią co innego:

| Przekrój | Stara | Nowa |
|---|---|---|
| Zamówienia o niskiej wartości: zwroty / skargi | 20,0% / 3,0% | 18,0% / 3,0% |
| Zamówienia powyżej 3000 zł: eskalacje | 9,3% | 18,7% (podwojone) |
| Rozzłoszczeni klienci: minut na rozmowę | 9,0 | 13,0 |
| Rozzłoszczeni klienci: defensywny ton | 4% | 17% |

Wartość p mówi tylko, że coś się zmieniło. W raporcie stoi obok wielkości efektu, przedziału, wskaźników awarii i przekrojów wysokiego ryzyka.

### Dwie różne istotności (`two_significances.py`)

Każdy przykład jest oceniany względem `minimum_effect.json`, zapisanego przed wynikami: +0,3 punktu albo 20% mniej awarii polityki, plus ograniczenia dla opóźnienia, kosztu i przekrojów wysokiego ryzyka.

| Przykład | Statystyka | Produkt |
|---|---|---|
| Ocena 8,10 → 8,12 na 60 000 rozmów, opóźnienie +39%, koszt +29% | p < 0,001 | bez znaczenia: cały przedział jest poniżej +0,3 |
| Awarie polityki 6/100 → 2/100 | p = 0,279, CI od −10,6 do +1,9 pp | może być ważne, potrzeba więcej danych |
| Trafność wyszukiwania +0,02 na 200 000 zapytań | p < 0,001 | globalnie niewidoczne, ale w wycinku „pilna wizyta w sprawie paszportu dla dziecka” oficjalne źródła rosną z 55% do 82%, a strony oszustów spadają z 9% do 1% |

### Analiza mocy (`power_analysis.py`)

- Przy 40 sparowanych przypadkach (sd różnic 1,2) ewaluacja wiarygodnie widzi tylko efekty od około 0,53 punktu. Szansa, że zobaczy +0,3, wynosi 35%, więc do +0,3 potrzeba około 128 przypadków, a do +0,1 około 1133.
- Przypadki na wersję (95% ufności, 80% mocy): spadek awarii z 10% do 5% wymaga 474, z 1% do 0,5% wymaga 5065.
- Agent kodujący z problemami bezpieczeństwa 6/60 kontra 4/60: p = 0,74, moc 10%, potrzeba około 1138 zadań na wersję. Taki wynik powinien uruchomić więcej próbkowania, a nie świętowanie.
- Symulacja uruchamia prawdziwy efekt +0,3 2000 razy na 40 przypadkach. Tylko 37% przebiegów go zauważa.

Spróbuj `--cases 100 --effect 0.2 --sd 1.0` albo `--rate-from 0.02 --rate-to 0.01`.

### Wielokrotne porównania (`multiple_comparisons.py`)

- Przy 100 porównaniach szansa na co najmniej jeden fałszywy alarm to 1 − 0,95¹⁰⁰ = 99,4%.
- Przeszukiwanie konfiguracji agenta: 200 konfiguracji (prompt × model × uprawnienia narzędzi × rubryka sędziego), wszystkie na tych samych 200 zadaniach deweloperskich. Produkcja ma 84%, zwycięzca 91% (+7 punktów, p = 0,034, gdy patrzeć na niego osobno).
- Skrypt odpowiada na danych na pięć pytań z artykułu:
  - Zwycięzcę znaleziono, a nie wybrano z góry.
  - Na świeżym, odłożonym zbiorze ma 82%, a produkcja 83%.
  - 5 jego zaliczeń osłabiło test.
  - W 5 powtórzeniach: 82,7% kontra 82,9%.
- Dashboard z 40 segmentami: bez korekty 4 są „istotne”, z czego 2 to fałszywe alarmy. Holm i Benjamini-Hochberg zostawiają tylko 2 zaplanowane.

### Precyzja, czułość, F-score (`precision_recall.py`)

Narzędzie do wykrywania błędów z artykułu: 40 trafnych zgłoszeń, 10 fałszywych alarmów, 20 przeoczeń, 30 słusznie pominiętych miejsc.

| | Wartość | Kiedy |
|---|---|---|
| precyzja | 0,80 | |
| czułość | 0,67 | |
| F0,5 | 0,77 | drogie fałszywe alarmy (komentarze w PR, blokady kont) |
| F1 | 0,73 | oba błędy kosztują podobnie |
| F2 | 0,69 | przeoczenie jest gorsze (wycieki prywatności, audyty bezpieczeństwa) |

Przegląd progów pokazuje, że to próg, a nie model, przesuwa balans. Każde F ma inny najlepszy próg: F0,5 przy 0,60, F2 przy 0,25.

### Ćwiczenie z artykułu

> Wybierz jedno porównanie, które masz przed sobą: dwa prompty, dwa modele, dwie polityki. Zapisz:
> - jakiego testu użyjesz i dlaczego,
> - na jakim założeniu ten test się opiera (np. niezależność przypadków, sparowanie),
> - jaką decyzję produktową wynik ma wspierać,
> - jaki minimalny efekt miałby dla ciebie znaczenie.
>
> A potem zapisz też, czego ten test nie może ci powiedzieć. Ta ostatnia lista często okazuje się najbardziej wartościowa.

1. Uruchom `python exercise/check_my_comparison.py`. W przykładzie test, założenie i decyzja są na miejscu. Ale 40 przypadków ma tylko 35% mocy dla +0,3, które ma znaczenie, więc potrzeba około 128. Skrypt proponuje też pozycje do listy „czego test nie powie”: koszt, rzadkie awarie, niezaplanowane przekroje, 13 porównań i jeden przebieg na przypadek.
2. Otwórz `exercise/my_comparison.json` i opisz swoje porównanie. Dla oceny liczbowej podaj spodziewane sd różnic między wersjami. Dla wskaźnika ustaw `"kind": "rate"`, `current_rate` i względny spadek jako `value` (0.2 = 20% mniej).
3. Najpierw napisz własną listę `cannot_tell`, potem porównaj ją z tym, co dopisze skrypt.

### Pliki

| Plik | Rola |
|---|---|
| `stats_tools.py` | Dwie proporcje (CI Wilsona/Newcombe'a), dwie średnie, Fisher, wielkość próby i moc, Holm, Benjamini-Hochberg, precyzja, czułość, F-beta |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `minimum_effect.json` | Minimalny znaczący efekt i ograniczenia, zapisane przed wynikami |
| `ship_it_slow_down.py` | Nagłówek o polityce zwrotów i jego przekroje |
| `two_significances.py` | Istotność statystyczna a praktyczna, trzy przykłady |
| `power_analysis.py` | Co widzi próbka, wielkości prób, agent kodujący, symulacja |
| `multiple_comparisons.py` | 1 − 0,95ᵐ, przeszukiwanie agenta, świeży zbiór, korekty dla dashboardu |
| `precision_recall.py` | Precyzja, czułość, F0,5/F1/F2 i próg |
| `exercise/` | Ćwiczenie: Twoje porównanie i skrypt sprawdzający |
| `test_significance.py` | Testy jednostkowe |
