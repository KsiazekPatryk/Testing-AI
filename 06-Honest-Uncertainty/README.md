# 06 — Honest Uncertainty

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post **How to Talk About AI Quality with Honest Uncertainty**.

The previous post said that one run is an anecdote and a sample is the beginning of evidence. This one is about how to summarize that sample and how to talk about results without pretending they are more precise than they are.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. Every formula lives in `stats.py`, written out so you can read it.

### Run it

```bash
python six_numbers.py               # six numbers worth having in every report
python perplexity_vs_product.py     # perplexity is not product quality
python confidence_intervals.py      # "about", said with discipline
python compare_versions.py          # is B really better than A? compare in pairs
python calibration.py               # "I'm confident" is not a confidence interval
python exercise/add_uncertainty.py  # the exercise from the post
python -m unittest -v test_uncertainty
```

### Six numbers (`six_numbers.py`)

Mean, median, minimum, failure rate, standard deviation and percentiles: each answers a different question about the product. The script starts with the examples from the post (8, 8, 8, 8 vs 10, 10, 4, 8: the same mean, different products), then reports two datasets:

- **Answer scores** of a support assistant: instead of “average quality 8.3”, a strong report says “mean 8.3, median 9.0, worst score 3, failure rate 4%, lowest-scoring slice: policy_edge_cases (6.6)”.
- **“My groceries are late again. Is that normal?”** The mean delay is 6.5 minutes, the median is 2, but P95 is 42: one customer in twenty waits longer than that. The breakdown by neighborhood shows one district carrying 68% of all late minutes. The average makes the system look good. The tail explains why angry customers take screenshots.

### Perplexity is not product quality (`perplexity_vs_product.py`)

Model B has lower cross-entropy and perplexity on a reference text, and loses on every product metric: following the return policy, citing a current source, escalating medical questions. Treat perplexity as a background signal; decide on product metrics.

### Confidence intervals (`confidence_intervals.py`)

The calculation from the post, step by step:

- 92 of 100 passed: SE = √(0.92 × 0.08 / 100) ≈ 0.027, margin ≈ 0.053, so **87–97%**.
- Mean 8.1, standard deviation 1.4, n = 100: SE = 0.14, margin ≈ 0.27, so **7.8–8.4**.
- With a small sample the multiplier grows (t distribution). With 10 of 10 passed the simple formula collapses to 100–100%, so the script switches to the Wilson interval (72–100%).
- Resampling the same scores at n = 5, 20, 50, 200 and 1,000: the mean barely moves, the interval narrows.

Try your own numbers: `python confidence_intervals.py --passed 47 --total 50 --mean 7.9 --sd 1.8 --n 40`.

### Comparing two versions (`compare_versions.py`)

The same 600 test cases go through version A and two candidates.

| | Each version on its own | Paired, B minus A | Verdict |
|---|---|---|---|
| A vs B1 (prompt tweak) | 82% (79–85%) vs 84% (81–87%) | +2.0%, CI −0.8% to +4.8% | crosses zero: not settled |
| A vs B2 (retrieval fix) | 82% (79–85%) vs 90% (88–92%) | +8.0%, CI +5.3% to +10.7% | above zero: strong evidence |

A “maybe better” change still carries rollout risk. A small gain whose interval touches zero may not be worth it.

### Model confidence vs statistical confidence (`calibration.py`)

Two LLM judges report their confidence for 1,000 verdicts:

- **always_sure** says 0.95 every time and is right 79% of the time. It sounds certain and tells you nothing about which cases are safe.
- **calibrated** is honest in English: in every bucket (0.5–0.6 … 0.9–1.0) the share of correct verdicts matches what it says, within the 95% interval. The script reports the Brier score and the expected calibration error (ECE).
- **Action rules** for a low-risk support assistant: answer on its own above 0.90, ask a clarifying question between 0.70 and 0.90, hand over to a human below 0.70.
- **Calibration is local:** the same judge on Polish questions is overconfident in most buckets, and the “answer on its own” zone lets several times more errors through. After changing the model, the prompt, the tools or the language, check again.

### The exercise from the post

> Pick one metric you report today as a single number and add uncertainty to it:
> 1. How many examples are behind that number?
> 2. What is the spread: median, minimum, standard deviation?
> 3. What is the approximate 95% confidence interval?
> 4. Which single slice is the riskiest, and how does it score on its own?

1. Run `python exercise/add_uncertainty.py` to see the four answers for the example metric (the support assistant score), and the honest sentence that replaces “Quality score: 8.3”. The result is saved to `output/my_metric_with_uncertainty.md`.
2. Open `exercise/my_metric.json` and point it to your own results: a JSONL file with one result per line (`results`, `value_field`, optional `slice_field`), or the numbers directly in `values`. Use `"kind": "pass_rate"` for 1/0 results and `"kind": "score"` for scores.
3. If the riskiest slice has only a handful of examples, the script says so. Often “it's fine” becomes “it's probably fine, but we need more data on X”. And that's okay.

### Files

| File | Role |
|---|---|
| `stats.py` | Every formula: percentiles, intervals for rates and means, Wilson, paired differences |
| `generate_data.py`, `data/` | Sample data used by every script (always the same content) |
| `six_numbers.py` | Six numbers for a report: scores and delivery delays |
| `perplexity_vs_product.py` | Lower perplexity, worse product |
| `confidence_intervals.py` | Confidence intervals step by step, and the effect of sample size |
| `compare_versions.py` | Unpaired vs paired comparison of two versions |
| `calibration.py` | Calibration buckets, Brier score, ECE, action rules, calibration by language |
| `exercise/` | The exercise: your metric and the script that adds uncertainty |
| `test_uncertainty.py` | Unit tests |
| `output/` | Created by the scripts |

---

## Polski

Przykład do wpisu **„Jak mówić o jakości AI z uczciwą niepewnością”**.

W poprzednim wpisie było o tym, że jeden przebieg to anegdota, a próbka to początek dowodu. Ten dotyczy tego, jak taką próbkę podsumować i jak mówić o wynikach, nie udając, że są bardziej precyzyjne, niż są.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Wszystkie wzory są w `stats.py`, rozpisane tak, żeby dało się je przeczytać.

### Uruchom

```bash
python six_numbers.py               # sześć liczb, które warto mieć w każdym raporcie
python perplexity_vs_product.py     # perpleksja to nie jakość produktu
python confidence_intervals.py      # „około” mówione z dyscypliną
python compare_versions.py          # czy B naprawdę jest lepsze od A? porównanie parowane
python calibration.py               # „jestem pewny” to nie przedział ufności
python exercise/add_uncertainty.py  # ćwiczenie z artykułu
python -m unittest -v test_uncertainty
```

### Sześć liczb (`six_numbers.py`)

Średnia, mediana, minimum, wskaźnik awarii, odchylenie standardowe i percentyle: każda odpowiada na inne pytanie o produkt. Skrypt zaczyna od przykładów z artykułu (8, 8, 8, 8 i 10, 10, 4, 8: ta sama średnia, różne produkty), a potem raportuje dwa zestawy danych:

- **Oceny odpowiedzi** asystenta wsparcia: zamiast „średnia jakość 8,3” mocny raport mówi „średnia 8,3, mediana 9,0, najgorsza ocena 3, wskaźnik awarii 4%, najniżej oceniany przekrój: policy_edge_cases (6,6)”.
- **„Moje zakupy znowu się spóźniają. Czy to normalne?”** Średnie opóźnienie to 6,5 minuty, mediana 2, ale P95 to 42: co dwudziesty klient czeka dłużej. Rozbicie na dzielnice pokazuje, że jedna z nich niesie 68% wszystkich minut opóźnienia. Średnia sprawia, że system wygląda dobrze. Ogon wyjaśnia, dlaczego źli klienci robią zrzuty ekranu.

### Perpleksja to nie jakość produktu (`perplexity_vs_product.py`)

Model B ma niższą entropię krzyżową i perpleksję na tekście referencyjnym, a przegrywa na każdej mierze produktowej: przestrzeganie polityki zwrotów, cytowanie aktualnego źródła, eskalacja pytań medycznych. Traktuj perpleksję jako sygnał tła, a decyzje opieraj na miarach produktowych.

### Przedziały ufności (`confidence_intervals.py`)

Obliczenia z artykułu krok po kroku:

- 92 na 100 zaliczonych: SE = √(0,92 × 0,08 / 100) ≈ 0,027, margines ≈ 0,053, czyli **87–97%**.
- Średnia 8,1, odchylenie 1,4, n = 100: SE = 0,14, margines ≈ 0,27, czyli **7,8–8,4**.
- Przy małej próbce mnożnik rośnie (rozkład t). Przy 10 na 10 zaliczonych prosty wzór zwraca 100–100%, więc skrypt przechodzi na przedział Wilsona (72–100%).
- Losowanie tych samych ocen przy n = 5, 20, 50, 200 i 1000: średnia prawie się nie zmienia, przedział się zwęża.

Własne liczby: `python confidence_intervals.py --passed 47 --total 50 --mean 7.9 --sd 1.8 --n 40`.

### Porównywanie dwóch wersji (`compare_versions.py`)

Te same 600 przypadków testowych przechodzi przez wersję A i dwóch kandydatów.

| | Każda wersja osobno | Parowo, B minus A | Werdykt |
|---|---|---|---|
| A vs B1 (poprawka promptu) | 82% (79–85%) vs 84% (81–87%) | +2,0%, CI −0,8% do +4,8% | przecina zero: nierozstrzygnięte |
| A vs B2 (poprawka wyszukiwania) | 82% (79–85%) vs 90% (88–92%) | +8,0%, CI +5,3% do +10,7% | powyżej zera: mocny dowód |

Zmiana „może lepsza” i tak niesie ryzyko wdrożenia. Mała poprawa, której przedział zahacza o zero, może nie być tego warta.

### Ufność modelu a ufność statystyczna (`calibration.py`)

Dwóch sędziów LLM podaje swoją pewność dla 1000 werdyktów:

- **always_sure** za każdym razem mówi 0,95, a ma rację w 79% przypadków. Brzmi pewnie i nie mówi nic o tym, które przypadki są bezpieczne.
- **calibrated** jest uczciwy po angielsku: w każdym przedziale (0,5–0,6 … 0,9–1,0) odsetek trafnych werdyktów zgadza się z deklaracją w granicach 95% przedziału ufności. Skrypt podaje Brier score i oczekiwany błąd kalibracji (ECE).
- **Reguły działania** dla asystenta wsparcia niskiego ryzyka: powyżej 0,90 odpowiada sam, między 0,70 a 0,90 dopytuje, poniżej 0,70 przekazuje sprawę człowiekowi.
- **Kalibracja jest lokalna:** ten sam sędzia na pytaniach po polsku jest zbyt pewny siebie w większości przedziałów, a strefa „odpowiada sam” przepuszcza kilka razy więcej błędów. Po zmianie modelu, promptu, narzędzi albo języka sprawdzasz ją od nowa.

### Ćwiczenie z artykułu

> Wybierz jedną metrykę, którą dziś raportujesz jako pojedynczą liczbę, i dodaj do niej niepewność:
> 1. Ile przykładów stoi za tą liczbą?
> 2. Jaki jest rozrzut: mediana, minimum, odchylenie?
> 3. Jaki jest przybliżony 95% przedział ufności?
> 4. Który jeden przekrój jest najbardziej ryzykowny i jak wypada osobno?

1. Uruchom `python exercise/add_uncertainty.py`, żeby zobaczyć cztery odpowiedzi dla przykładowej metryki (ocena asystenta wsparcia) i uczciwe zdanie, które zastępuje „Quality score: 8.3”. Wynik zapisuje się w `output/my_metric_with_uncertainty.md`.
2. Otwórz `exercise/my_metric.json` i wskaż własne wyniki: plik JSONL z jednym wynikiem na linię (`results`, `value_field`, opcjonalnie `slice_field`) albo liczby bezpośrednio w `values`. Użyj `"kind": "pass_rate"` dla wyników 1/0 i `"kind": "score"` dla ocen.
3. Jeśli najbardziej ryzykowny przekrój ma tylko garść przykładów, skrypt to powie. Często „jest dobrze” zamienia się w „prawdopodobnie jest dobrze, ale potrzebujemy więcej danych o przypadkach X”. I to jest w porządku.

### Pliki

| Plik | Rola |
|---|---|
| `stats.py` | Wszystkie wzory: percentyle, przedziały dla odsetków i średnich, Wilson, różnice parowane |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `six_numbers.py` | Sześć liczb do raportu: oceny i opóźnienia dostaw |
| `perplexity_vs_product.py` | Niższa perpleksja, gorszy produkt |
| `confidence_intervals.py` | Przedziały ufności krok po kroku i wpływ wielkości próby |
| `compare_versions.py` | Porównanie dwóch wersji: osobno i parowo |
| `calibration.py` | Przedziały kalibracji, Brier score, ECE, reguły działania, kalibracja według języka |
| `exercise/` | Ćwiczenie: Twoja metryka i skrypt, który dodaje do niej niepewność |
| `test_uncertainty.py` | Testy jednostkowe |
| `output/` | Tworzony przez skrypty |
