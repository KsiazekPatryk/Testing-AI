# 03 — Variance Under Control

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**One Run Is Not Proof (Part 3): Variance Under Control**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-b44).

Which differences between runs are fine, and which ones block a release? When is it worth dialing down randomness, and what does it cost?

Runs without an API key and without installing any packages (Python 3.9+). The code, comments and console output are in Polish; the ideas carry over one to one.

### A model with real knobs

`token_model.py` is a tiny language model. It answers the question *“When will my order arrive, and until when can I cancel it?”*. Store policy: cancellation up to 24 hours before shipping, and a mandatory warning about chilled goods.

At each slot of the answer, the model picks a text fragment based on **logits**. The knobs work in the same order as in real models: logit bias → temperature → softmax → top-k → top-p. Bad fragments (“48 hours”, “we guarantee it”, a missing warning) have low logits. They’re rare, but possible. That’s why a single run usually doesn’t show them.

### Run it

```bash
python knobs.py                          # how temperature, top-p, top-k, logit bias and seed change the distribution
python five_runs.py                      # EXERCISE: five runs and three lists
python two_runs.py                       # stable vs production run, variance split by dimension
python -m unittest -v test_regressions   # regression tests
```

### The exercise from the post

> Run the same input five times. Then write down three lists: harmless differences; differences that change what the user experiences; settings that could reduce variance.

`five_runs.py` does this automatically and saves a Markdown report to `reports/`:

- **List 1:** different wording, a paragraph instead of a list, a different closing line. Acceptable variance.
- **List 2:** a wrong cancellation limit, the promise “we guarantee it”, a missing warning. Plus the probability that 5 runs **show nothing at all**. With production settings it’s about 50%.
- **List 3:** for each problematic slot, the computed effect of each knob, for example “top_p 0.9: risk 8.0% → 0.0%”, plus a structural fix that is usually better: the fact comes from code, not from the model.

Try:

```bash
python five_runs.py --seed 3          # a series where a problem shows up
python five_runs.py --n 50            # more runs = more visible
python five_runs.py --top-p 0.9       # did the knob help?
python five_runs.py --bias 48=-100 --bias 12=-100
python five_runs.py --temperatura 0   # stable, but no variety
```

Each series prints the exact command to reproduce it (`--seed`).

> In this simplified model, `top_p 0.9` removes the bad fragments entirely. In a real LLM, the knobs reduce the risk but don’t eliminate it. That’s why you need tests on a larger sample, not just different settings.

### Two runs instead of one

`two_runs.py` runs the same set of 300 queries twice:

- **stable:** temperature 0, fixed seed, a frozen data snapshot, stubbed tools,
- **production:** temperature 0.9, live data (the router moves delivery to Saturday mid-run), latency with retries.

The result is a variance table **for each dimension separately**: wording, structure, facts, promises, warnings, data changes and latency (p50/p95/p99). Rates come with a 95% confidence interval. It shows that:

- the stable run is clean, so production failures come from sampling, not from the test case,
- moving delivery to Saturday is a legitimate change in the world, not a model error. You can only see that thanks to the data snapshot in the envelope,
- median latency looks fine, but p99 doesn’t.

### The full envelope

`envelope.py` records for every run: the model, the prompt and its version, tool definitions, the data snapshot, decoding parameters, seed, schema, judge, timestamp and infrastructure. `porownaj_koperty()` tells you whether you’re comparing the same test or something else already.

### Files

| File | Role |
|---|---|
| `token_model.py` | Mini-model with logits and sampling (temperature, top-p, top-k, seed, logit bias) |
| `knobs.py` | The knobs cheat sheet, computed live |
| `five_runs.py` | The exercise: five runs and three lists, Markdown report |
| `two_runs.py` | Stable and production runs, variance by dimension, confidence intervals |
| `envelope.py` | The full evaluation envelope and envelope comparison |
| `test_regressions.py` | Regression tests |
| `reports/` | Created by the scripts |

---

## Polski

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 3). Zmienność pod kontrolą**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-b44).

Które różnice między uruchomieniami są w porządku, a które blokują wydanie? Kiedy warto przykręcić losowość i ile to kosztuje?

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

### Model z prawdziwymi pokrętłami

`token_model.py` to miniaturowy model językowy. Odpowiada na pytanie *„Kiedy dotrze moje zamówienie i do kiedy mogę je anulować?”*. Polityka sklepu: anulowanie do 24 godzin przed wysyłką i obowiązkowe ostrzeżenie o produktach chłodzonych.

W każdym miejscu odpowiedzi model wybiera fragment tekstu na podstawie **logitów**. Pokrętła działają w tej samej kolejności co w prawdziwych modelach: logit bias → temperatura → softmax → top-k → top-p. Złe fragmenty („48 godzin”, „gwarantujemy”, pominięte ostrzeżenie) mają niskie logity. Są rzadkie, ale możliwe. Dlatego jedno uruchomienie ich zwykle nie pokazuje.

### Uruchom

```bash
python knobs.py                          # jak temperatura, top-p, top-k, logit bias i seed zmieniają rozkład
python five_runs.py                      # ĆWICZENIE: pięć uruchomień i trzy listy
python two_runs.py                       # przebieg stabilny vs produkcyjny, wariancja w podziale na wymiary
python -m unittest -v test_regressions   # testy regresyjne
```

### Ćwiczenie z artykułu

> Uruchom te same dane wejściowe pięć razy. Potem zapisz trzy listy: różnice nieszkodliwe; różnice, które zmieniają to, czego doświadcza użytkownik; ustawienia, które mogłyby zmniejszyć wariancję.

`five_runs.py` robi to automatycznie i zapisuje raport w Markdown do `reports/`:

- **Lista 1:** różne sformułowania, akapit zamiast listy, inne zakończenie. To wariancja akceptowalna.
- **Lista 2:** zły limit anulowania, obietnica „gwarantujemy”, pominięte ostrzeżenie. Do tego prawdopodobieństwo, że 5 uruchomień **niczego nie pokaże**. Przy ustawieniach produkcyjnych wynosi ono około 50%.
- **Lista 3:** dla każdego problematycznego miejsca policzony efekt pokręteł, na przykład „top_p 0.9: ryzyko 8,0% → 0,0%”, oraz rozwiązanie strukturalne, które zwykle jest lepsze: fakt z kodu, a nie z modelu.

Spróbuj:

```bash
python five_runs.py --seed 3          # seria, w której wychodzi problem
python five_runs.py --n 50            # więcej uruchomień = więcej widać
python five_runs.py --top-p 0.9       # czy pokrętło pomogło?
python five_runs.py --bias 48=-100 --bias 12=-100
python five_runs.py --temperatura 0   # stabilnie, ale bez różnorodności
```

Każda seria wypisuje polecenie, którym można ją dokładnie odtworzyć (`--seed`).

> W tym uproszczonym modelu `top_p 0.9` usuwa złe fragmenty całkowicie. W prawdziwym LLM pokrętła zmniejszają ryzyko, ale go nie zerują. Dlatego potrzebujesz testów na większej próbie, a nie tylko zmiany ustawień.

### Dwa przebiegi zamiast jednego

`two_runs.py` uruchamia ten sam zestaw 300 zapytań dwa razy:

- **stabilny:** temperatura 0, stały seed, zamrożona migawka danych, stuby narzędzi,
- **produkcyjny:** temperatura 0,9, dane na żywo (w trakcie router przesuwa dostawę na sobotę), opóźnienia z ponowieniami.

Wynik to tabela wariancji **osobno dla każdego wymiaru**: sformułowanie, struktura, fakty, obietnice, ostrzeżenia, zmiana danych i opóźnienie (p50/p95/p99). Odsetki mają 95% przedział ufności. Widać w niej, że:

- przebieg stabilny jest czysty, więc awarie w produkcji biorą się z próbkowania, a nie z przypadku testowego,
- przesunięcie dostawy na sobotę to zasadna zmiana świata, a nie błąd modelu. Widać to tylko dzięki migawce danych w kopercie,
- mediana opóźnienia wygląda dobrze, ale p99 już nie.

### Pełna koperta

`envelope.py` zapisuje przy każdym przebiegu: model, prompt i jego wersję, definicje narzędzi, migawkę danych, parametry dekodowania, seed, schemat, sędzię, znacznik czasu i infrastrukturę. `porownaj_koperty()` mówi, czy porównujesz ten sam test, czy już coś innego.

### Pliki

| Plik | Rola |
|---|---|
| `token_model.py` | Mini-model z logitami i próbkowaniem (temperatura, top-p, top-k, seed, logit bias) |
| `knobs.py` | Ściąga z pokręteł policzona na żywo |
| `five_runs.py` | Ćwiczenie: pięć uruchomień i trzy listy, raport w Markdown |
| `two_runs.py` | Przebieg stabilny i produkcyjny, wariancja w podziale na wymiary, przedziały ufności |
| `envelope.py` | Pełna koperta ewaluacji i porównywanie kopert |
| `test_regressions.py` | Testy regresyjne |
| `reports/` | Tworzone przez skrypty |
