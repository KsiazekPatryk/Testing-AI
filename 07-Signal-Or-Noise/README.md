# 07 — Signal or Noise

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**The New Version Won. Are You Sure?**](https://paprico.substack.com/p/nowa-wersja-wygraa-na-pewno) (in English, also available in Polish).

Old prompt: mean 7.8. New prompt: 8.3. Is the difference real? And is it big enough to matter? This folder shows the null hypothesis, the t-test, chi-square and the p-value in practice. Statistics has one job here: to help tell signal from noise. It does not decide for you whether a change is worth shipping.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. Every test is written out with the standard library in `stats_tests.py`; the results match `scipy.stats`, which the unit tests check against reference values.

### Run it

```bash
python null_hypothesis.py          # start with the boring assumption, and write it down first
python t_test.py                   # is the difference bigger than the noise?
python choose_test.py              # pick the test from how the data was produced
python repeated_runs.py            # 2,000 results are not 2,000 pieces of evidence
python chi_square.py               # when quality is buckets, not a mean
python p_value_coins.py            # a p-value, counted with coins
python exercise/check_my_win.py    # the exercise from the post
python -m unittest -v test_signal_or_noise
```

### Start with the boring assumption (`null_hypothesis.py`)

H0: the new version is not meaningfully different. H1: it is, in the way we care about. You never prove H0; you either reject it or admit the evidence is too weak.

The script prints `preregistration.json`: the comparison, population, metric, sample, test and decision threshold, written before the evaluation. Then it shows why: two truly identical versions compared on 20 slices. One slice comes out “significant” (VIP customers, p = 0.04), and the after-the-fact story writes itself. That is p-hacking. Surprises are leads for the next test, not evidence from this one.

### The t-test (`t_test.py`)

The same 100 test cases go through both prompts.

| Analysis | Difference | p | 95% CI |
|---|---|---|---|
| Paired t-test (per case) | +0.50 | 0.003 | +0.17 to +0.83 |
| Same data, pairing ignored | +0.50 | 0.038 | +0.03 to +0.97 |

Pairing controls for case difficulty, so the same improvement is measured much more precisely. A t-test is still not a release gate: the pass rate barely moved (82% → 83%, McNemar p = 1.0) and the new prompt produced one policy failure the old one did not have. The script ends with an honest report sentence.

### Which test? (`choose_test.py`)

| Same cases? | Outcome | Test |
|---|---|---|
| yes | numeric score | paired t-test on the differences |
| no | numeric score | Welch's t-test |
| yes | pass/fail | McNemar (only cases where A and B differ count) |
| any | category counts | chi-square; Fisher's exact test for small counts |
| yes / no | ordinal (0–10 rubric) | Wilcoxon / Mann-Whitney |
| any | skewed, unusual | bootstrap or permutation test |

Every test is run on the example data. Try `python choose_test.py --paired yes --outcome pass_fail`.

### 2,000 results are not 2,000 pieces of evidence (`repeated_runs.py`)

100 prompts, each run 20 times per version. Counting every run as independent gives p = 0.005: a “clear win”. Summarizing each prompt first and comparing the 100 prompts gives p = 0.072, with an interval that crosses zero. Significance disappeared, so the original result counted related observations as independent.

### Chi-square (`chi_square.py`)

100 conversations per returns policy: resolved automatically 70 → 55, escalated 20 → 35, refused 10 → 10. The script computes the expected counts (62.5, 27.5, 10), χ² = 5.89 and p ≈ 0.053, step by step. Not a magic yes/no line: evidence that the distribution may have shifted. The next question is about the product: are more escalations acceptable, or is the new policy pushing work onto people? Try your own counts with `--old 70 20 10 --new 55 35 10`.

### The p-value (`p_value_coins.py`)

The new version wins 15 of 20 cases. Out of 1,048,576 possible sequences, 21,700 have 15 or more “heads”: p ≈ 0.021 one-sided, 0.041 two-sided. The script confirms it with 100,000 simulated worlds, lists what p = 0.02 does not mean, and shows that 0.049 and 0.051 carry almost the same information.

### The exercise from the post

> Take the last comparison of two versions that your team called a win, and answer three questions:
> 1. Were the hypothesis and the metric written down before the test, or chosen after seeing the results?
> 2. Were the cases paired, and did the test take that into account?
> 3. How many independent cases (not runs) stood behind the result?
>
> If you can't answer any of them, that “win” is, for now, a hypothesis.

1. Run `python exercise/check_my_win.py`. The example describes a typical announced win (“+0.11, p = 0.005”). All three answers fail, and recomputing the raw results per independent case gives p = 0.072.
2. Open `exercise/my_win.json` and describe your own win: when the hypothesis was written and when the results were first seen, whether the cases were paired and which test was used, and how many independent cases there were. Leave unknown fields as `null`.
3. If you have the raw results, point `results` to them (one line per run, with case, version and score fields). The script recomputes the comparison at the level of independent cases.

### Files

| File | Role |
|---|---|
| `stats_tests.py` | All tests: t, Welch, chi-square, McNemar, Fisher, Wilcoxon, Mann-Whitney, sign test, permutation, bootstrap |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `preregistration.json`, `null_hypothesis.py` | The hypothesis written before the test, and p-hacking |
| `t_test.py` | Paired vs unpaired t-test, Welch, and why a t-test is not a release gate |
| `choose_test.py` | Which test fits which data, each one run on examples |
| `repeated_runs.py` | Runs vs independent cases |
| `chi_square.py` | Chi-square step by step, and Fisher for small counts |
| `p_value_coins.py` | The p-value counted, simulated and interpreted |
| `exercise/` | The exercise: your “win” and the checker |
| `test_signal_or_noise.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Nowa wersja wygrała. Na pewno?”**](https://paprico.substack.com/p/nowa-wersja-wygraa-na-pewno) (po angielsku, z wersją po polsku).

Stary prompt: średnia 7,8. Nowy prompt: 8,3. Czy ta różnica jest prawdziwa? I czy jest na tyle duża, żeby miała znaczenie? Ten folder pokazuje w praktyce hipotezę zerową, test t, chi-kwadrat i wartość p. Statystyka ma tu jedno zadanie: pomóc odróżnić sygnał od szumu. Nie decyduje za ciebie, czy zmiana jest warta wdrożenia.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Każdy test jest napisany w `stats_tests.py` przy użyciu samej biblioteki standardowej. Wyniki zgadzają się z `scipy.stats`, co sprawdzają testy jednostkowe na wartościach referencyjnych.

### Uruchom

```bash
python null_hypothesis.py          # zacznij od nudnego założenia i zapisz je przed testem
python t_test.py                   # czy różnica jest większa od szumu?
python choose_test.py              # dobierz test do tego, jak powstały dane
python repeated_runs.py            # 2000 wyników to nie 2000 dowodów
python chi_square.py               # gdy jakość to kubełki, a nie średnia
python p_value_coins.py            # wartość p policzona na monetach
python exercise/check_my_win.py    # ćwiczenie z artykułu
python -m unittest -v test_signal_or_noise
```

### Zacznij od nudnego założenia (`null_hypothesis.py`)

H0: nowa wersja nie jest znacząco inna. H1: jest, w sposób, który nas interesuje. H0 nigdy nie udowadniasz: albo ją odrzucasz, albo przyznajesz, że dowody są za słabe.

Skrypt wypisuje `preregistration.json`: porównanie, populację, metrykę, próbkę, test i próg decyzji, zapisane przed ewaluacją. Potem pokazuje, dlaczego to ważne: dwie naprawdę identyczne wersje porównane w 20 przekrojach. Jeden przekrój wychodzi „istotny” (klienci VIP, p = 0,04), a historia po fakcie pisze się sama. To p-hacking. Niespodzianki to tropy do następnego testu, a nie dowód z tego.

### Test t (`t_test.py`)

Te same 100 przypadków testowych przechodzi przez oba prompty.

| Analiza | Różnica | p | 95% CI |
|---|---|---|---|
| Sparowany test t (przypadek po przypadku) | +0,50 | 0,003 | od +0,17 do +0,83 |
| Te same dane bez parowania | +0,50 | 0,038 | od +0,03 do +0,97 |

Parowanie kontroluje trudność przypadków, więc ta sama poprawa jest zmierzona dużo dokładniej. Test t to nadal nie bramka wydania: odsetek zaliczeń prawie się nie zmienił (82% → 83%, McNemar p = 1,0), a nowy prompt wyprodukował jedną awarię polityki, której stary nie miał. Skrypt kończy się uczciwym zdaniem do raportu.

### Który test? (`choose_test.py`)

| Te same przypadki? | Wynik | Test |
|---|---|---|
| tak | ocena liczbowa | sparowany test t na różnicach |
| nie | ocena liczbowa | test t Welcha |
| tak | zalicza/nie zalicza | McNemar (liczą się tylko przypadki, w których A i B się różnią) |
| dowolnie | liczebności kategorii | chi-kwadrat; przy małych liczbach dokładny test Fishera |
| tak / nie | porządkowy (rubryka 0–10) | Wilcoxon / Mann-Whitney |
| dowolnie | skośny, nietypowy | bootstrap albo test permutacyjny |

Każdy test jest uruchamiany na przykładowych danych. Spróbuj `python choose_test.py --paired yes --outcome pass_fail`.

### 2000 wyników to nie 2000 dowodów (`repeated_runs.py`)

100 promptów, każdy uruchomiony 20 razy na wersję. Liczenie każdego przebiegu jako niezależnego daje p = 0,005: „wyraźna wygrana”. Podsumowanie każdego promptu i porównanie 100 promptów daje p = 0,072, a przedział przecina zero. Istotność zniknęła, czyli pierwotny wynik liczył powiązane obserwacje jako niezależne.

### Chi-kwadrat (`chi_square.py`)

Po 100 rozmów na politykę zwrotów: rozwiązane automatycznie 70 → 55, eskalacje 20 → 35, odmowy 10 → 10. Skrypt liczy krok po kroku wartości oczekiwane (62,5, 27,5, 10), χ² = 5,89 i p ≈ 0,053. To nie jest magiczna granica tak/nie, tylko dowód, że rozkład mógł się przesunąć. Następne pytanie jest produktowe: czy więcej eskalacji jest w porządku, czy nowa polityka zrzuca pracę na ludzi? Własne liczby: `--old 70 20 10 --new 55 35 10`.

### Wartość p (`p_value_coins.py`)

Nowa wersja wygrywa w 15 z 20 przypadków. Na 1 048 576 możliwych wyników 21 700 ma 15 lub więcej „orłów”: p ≈ 0,021 jednostronnie, 0,041 dwustronnie. Skrypt potwierdza to symulacją 100 000 światów, wypisuje, czego p = 0,02 nie oznacza, i pokazuje, że 0,049 i 0,051 niosą prawie tę samą informację.

### Ćwiczenie z artykułu

> Weź ostatnie porównanie dwóch wersji, które uznaliście za wygraną, i odpowiedz na trzy pytania:
> 1. Czy hipoteza i metryka były zapisane przed testem, czy wybrane po obejrzeniu wyników?
> 2. Czy przypadki były sparowane i czy test to uwzględniał?
> 3. Ile niezależnych przypadków (nie przebiegów) stało za wynikiem?
>
> Jeśli na którekolwiek pytanie nie umiesz odpowiedzieć, ta „wygrana” jest na razie hipotezą.

1. Uruchom `python exercise/check_my_win.py`. Przykład opisuje typową ogłoszoną wygraną („+0,11, p = 0,005”). Wszystkie trzy odpowiedzi wypadają źle, a przeliczenie surowych wyników na poziomie niezależnych przypadków daje p = 0,072.
2. Otwórz `exercise/my_win.json` i opisz swoją wygraną: kiedy zapisano hipotezę, a kiedy po raz pierwszy zobaczono wyniki, czy przypadki były sparowane i jakiego testu użyto, ile było niezależnych przypadków. Nieznane pola zostaw jako `null`.
3. Jeśli masz surowe wyniki, wskaż je w `results` (jedna linia na przebieg, z polami przypadku, wersji i oceny). Skrypt przeliczy porównanie na poziomie niezależnych przypadków.

### Pliki

| Plik | Rola |
|---|---|
| `stats_tests.py` | Wszystkie testy: t, Welch, chi-kwadrat, McNemar, Fisher, Wilcoxon, Mann-Whitney, test znaków, permutacje, bootstrap |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `preregistration.json`, `null_hypothesis.py` | Hipoteza zapisana przed testem i p-hacking |
| `t_test.py` | Sparowany i niesparowany test t, Welch i dlaczego test t to nie bramka wydania |
| `choose_test.py` | Który test do jakich danych, każdy uruchomiony na przykładach |
| `repeated_runs.py` | Przebiegi a niezależne przypadki |
| `chi_square.py` | Chi-kwadrat krok po kroku i test Fishera dla małych liczb |
| `p_value_coins.py` | Wartość p policzona, zasymulowana i zinterpretowana |
| `exercise/` | Ćwiczenie: Twoja „wygrana” i skrypt sprawdzający |
| `test_signal_or_noise.py` | Testy jednostkowe |
