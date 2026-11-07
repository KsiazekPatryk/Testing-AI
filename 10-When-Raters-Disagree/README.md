# 10 — When Raters Disagree

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**When Raters Disagree**](https://paprico.substack.com/p/gdy-oceniajacy-sie-nie-zgadzaja) (in English, also available in Polish).

The previous post said that a rater is a measuring instrument. This one is about what happens when well-chosen raters with a good rubric still disagree. Sometimes it signals an error. Sometimes it is valuable information about users. This folder shows how to tell the two apart, how to measure agreement with Cohen's kappa and Krippendorff's alpha, and how to check the value of the labelers themselves.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. Kappa and alpha are written out in `agreement.py`. The results match scikit-learn and the `krippendorff` package, which the unit tests check against reference values.

### Run it

```bash
python harmful_or_healthy.py          # disagreement is not always a defect
python topic_entropy.py               # many meanings: the best set is not the top-rated one
python start_simple.py                # all agree, two agree, nobody agrees
python cohen_kappa.py                 # how much agreement is left after chance
python krippendorff_alpha.py          # more raters, missing ratings, 0-10 scales
python why_not_whether.py             # 9, 5 and 2 for the same answer: the spoiled milk case
python labeler_value.py               # a labeler's value is not clicks per hour
python too_good_agreement.py          # when agreement is too beautiful
python exercise/check_my_agreement.py # the exercise from the post
python -m unittest -v test_disagreement
```

### Harmful or healthy (`harmful_or_healthy.py`)

Eight disagreements from one review round are sorted by what they revealed:

| Cause | Kind | What to do |
|---|---|---|
| a reviewer saw a blocker the others missed | harmful | treat it as a blocker, retrain |
| an LLM judge rewarded an unsafe answer | harmful | recalibrate the judge |
| the policy does not answer the question | harmful | clarify the policy |
| reviewers scored different dimensions | harmful | split the rubric |
| acceptable answers, different tastes | healthy | find the preference groups |
| the request itself is ambiguous | healthy | ask, or offer options |

Then a healthy disagreement up close. 300 users compare a concise and a detailed answer, and the averages (3.56 vs 3.41) look like a tie. Per user, 149 clearly prefer concise and 140 clearly prefer detailed. The average describes no real user. The fix is product design (short by default, "show details"), not a rubric fix.

### Topic entropy (`topic_entropy.py`)

"python list append" has an entropy of 0.47 bits. "Best agent framework to replace my QA team" has 2.26 bits, close to the 2.32 maximum for five readings.

| Result set | Mean rating | Users served (strong result in the top 5) | Official docs |
|---|---|---|---|
| vendor_wall: ten near-identical vendor pages | **7.7** | 22% | none |
| balanced: docs, comparison, benchmark, warning, case study | 7.3 | **78%** | rank 1 |
| lost: "diverse", but buried under hot takes | 5.0 | 22% | rank 8 |

The best result set does not have the highest average rating. Diversity is not a goal on its own either: each interpretation needs its strongest result.

### Start simple (`start_simple.py`)

Three reviewers label 100 answers. Under guideline v1, all three agree on 48, two agree on 45 and nobody agrees on 7. By category, all three agree on 74% of FAQ answers but only 16% of tone and 28% of safety answers. The script then lists the cases to discuss. Compare with `--guideline v2`: 72 / 27 / 1.

### Cohen's kappa (`cohen_kappa.py`)

The post's table is 50 / 30 / 10 / 10. Observed agreement is 0.80, chance agreement is 0.6 × 0.6 + 0.4 × 0.4 = 0.52, so **κ = 0.58**. The script also covers:

- What 0.58 is enough for: spot checks of low-risk style, yes; privacy, medicine and finance, no.
- The prevalence trap: 94% raw agreement but κ = 0.22 when almost everything is "acceptable".
- The same calculation on real data: κ goes from 0.40 to 0.63 after the new guideline.

Try `--table 90 2 4 4`.

### Krippendorff's alpha (`krippendorff_alpha.py`)

The post's example (3 reviewers, 5 outputs) is counted pair by pair. 4 of 15 pairs disagree, so the observed disagreement is 0.27. The expected disagreement, with 9 safe and 6 risky labels paired at random, is 0.51. That gives **α = 0.48**. On a 0–10 scale, ordinal and interval alpha treat 7 vs 8 more gently than 2 vs 9 (0.89 vs 0.19), while nominal alpha treats both alike. On 100 answers with 18 missing ratings, no item has to be thrown away.

### "Whether" vs "why" (`why_not_whether.py`)

"My child drank spoiled milk from yesterday's delivery." Three reviewers give the same answer 9, 5 and 2: one judged tone, one escalation, one medical-sounding advice. The mean of 5.3 says "mediocre". With the score split into dimensions and with blockers, all three agree on every dimension and the verdict is FAIL.

### What a labeler is worth (`labeler_value.py`)

The post's five questions, answered on the data:

1. **Do the labels predict outcomes?** Of 15 later complaints, the expert and ola had called 2 acceptable and kasia 4. piotr misses none, but flags 61 answers.
2. **Systematic biases?** piotr is stricter (mean 4.6). kasia puts 68% of her scores at 5–6 and calls 7 of 11 risky safety answers acceptable.
3. **Where is the disagreement?** α = 0.64 for FAQ, 0.11 for tone and 0.19 for safety. The overall 0.40 hides that.
4. **Does an extra rater help?** One rater matches the expert on 83% of answers. When two raters agree they match on 95%, and the 39 answers they disagree on go to the expert.
5. **Test the guideline itself.** Splitting the label into dimensions raises α for safety from 0.19 to 0.84.

### Too beautiful (`too_good_agreement.py`)

12 labeling accounts work through 200 items each. Four accounts agree with each other 100% of the time and submit their labels a second apart. Against gold they are right 55% of the time; honest accounts get 86–92%. The script ends with the ibuprofen example: the clearest page is not the safe one.

### The exercise from the post

> Take 20 examples rated by two people (or by a human and an LLM judge) and compute two things:
> - the raw agreement rate,
> - Cohen's kappa (a spreadsheet and the formula from this post are enough).
>
> Then read every disagreement and write one word next to each: "rubric", "policy", "preference" or "error". That split will tell you more than the number itself.

1. Run `python exercise/check_my_agreement.py`. The example compares a human with an LLM judge on 20 support answers. The result: 75% raw agreement, κ = 0.44, and 5 disagreements (2 rubric, 1 policy, 1 preference, 1 error).
2. Replace `exercise/my_pairs.csv` with your own 20 pairs. It needs the columns `rater_a`, `rater_b` and `reason`, and `question` and `note` are optional. Any labels work: pass/fail, acceptable/risky, 0–10. You can edit it in a spreadsheet.
3. Fill in `reason` for every disagreement. The script reports untagged ones and splits the rest into harmful and healthy.

### Files

| File | Role |
|---|---|
| `agreement.py` | Raw agreement, Cohen's kappa, Krippendorff's alpha (nominal, ordinal, interval, with missing data), entropy |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `harmful_or_healthy.py` | Triage of disagreements, preference groups |
| `topic_entropy.py` | Query entropy and three result sets |
| `start_simple.py` | All / two / none, by category |
| `cohen_kappa.py` | Kappa step by step, the prevalence trap |
| `krippendorff_alpha.py` | Alpha step by step, scales, missing ratings |
| `why_not_whether.py` | The spoiled milk case, before and after splitting the rubric |
| `labeler_value.py` | Five questions about the labelers' value |
| `too_good_agreement.py` | Suspicious agreement, and the ibuprofen example |
| `exercise/` | The exercise: your 20 pairs and the checker |
| `test_disagreement.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Gdy oceniający się nie zgadzają”**](https://paprico.substack.com/p/gdy-oceniajacy-sie-nie-zgadzaja) (po angielsku, z wersją po polsku).

Poprzedni wpis mówił, że oceniający to instrument pomiarowy. Ten jest o tym, co się dzieje, gdy nawet dobrze dobrani oceniający z dobrą rubryką się nie zgadzają. Czasem to sygnał błędu. Czasem cenna informacja o użytkownikach. Ten folder pokazuje, jak odróżnić jedno od drugiego, jak mierzyć zgodność kappą Cohena i alfą Krippendorffa i jak sprawdzić wartość samych etykietujących.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Kappa i alfa są rozpisane w `agreement.py`. Wyniki zgadzają się ze scikit-learn i pakietem `krippendorff`, co sprawdzają testy jednostkowe na wartościach referencyjnych.

### Uruchom

```bash
python harmful_or_healthy.py          # niezgodność nie zawsze jest wadą
python topic_entropy.py               # wiele znaczeń: najlepszy zestaw to nie ten z najwyższą oceną
python start_simple.py                # wszyscy się zgadzają, dwóch, nikt
python cohen_kappa.py                 # ile zgody zostaje po odjęciu przypadku
python krippendorff_alpha.py          # więcej oceniających, braki ocen, skale 0-10
python why_not_whether.py             # 9, 5 i 2 dla tej samej odpowiedzi: zepsute mleko
python labeler_value.py               # wartość etykietującego to nie liczba kliknięć na godzinę
python too_good_agreement.py          # gdy zgodność jest zbyt piękna
python exercise/check_my_agreement.py # ćwiczenie z artykułu
python -m unittest -v test_disagreement
```

### Szkodliwa czy zdrowa (`harmful_or_healthy.py`)

Osiem niezgodności z jednej rundy przeglądu jest posortowanych według tego, co ujawniły:

| Przyczyna | Rodzaj | Co robić |
|---|---|---|
| jeden recenzent zauważył bloker, który inni przeoczyli | szkodliwa | potraktować to jako bloker, doszkolić |
| sędzia LLM nagrodził niebezpieczną odpowiedź | szkodliwa | ponownie skalibrować sędziego |
| polityka nie odpowiada na pytanie | szkodliwa | doprecyzować politykę |
| recenzenci oceniali różne wymiary | szkodliwa | podzielić rubrykę |
| akceptowalne odpowiedzi, różne gusta | zdrowa | znaleźć grupy preferencji |
| samo zapytanie jest niejednoznaczne | zdrowa | dopytać albo pokazać opcje |

Potem zdrowa niezgodność z bliska. 300 użytkowników porównuje odpowiedź zwięzłą i szczegółową, a średnie (3,56 i 3,41) wyglądają na remis. Na poziomie użytkowników 149 wyraźnie woli zwięzłą, a 140 szczegółową. Średnia nie opisuje żadnego prawdziwego użytkownika. Rozwiązaniem jest projekt produktu (domyślnie krótko, opcja „pokaż szczegóły”), a nie poprawka rubryki.

### Entropia tematyczna (`topic_entropy.py`)

Zapytanie „python list append” ma entropię 0,47 bita. „Najlepszy framework agentowy do zastąpienia mojego zespołu QA” ma 2,26 bita, blisko maksimum 2,32 dla pięciu interpretacji.

| Zestaw wyników | Średnia ocena | Obsłużeni użytkownicy (mocny wynik w top 5) | Oficjalna dokumentacja |
|---|---|---|---|
| vendor_wall: dziesięć niemal identycznych stron dostawców | **7,7** | 22% | brak |
| balanced: dokumentacja, porównanie, benchmark, ostrzeżenie, case study | 7,3 | **78%** | pozycja 1 |
| lost: „różnorodny”, ale pogrzebany pod gorącymi opiniami | 5,0 | 22% | pozycja 8 |

Najlepszy zestaw nie ma najwyższej średniej oceny. Różnorodność też nie jest celem samym w sobie: każda interpretacja potrzebuje swojego najmocniejszego wyniku.

### Zacznij prosto (`start_simple.py`)

Trzech recenzentów ocenia 100 odpowiedzi. Według wytycznej v1 wszyscy trzej zgadzają się w 48 przypadkach, dwóch w 45, a nikt w 7. W podziale na kategorie wszyscy zgadzają się przy 74% pytań FAQ, ale tylko przy 16% odpowiedzi o tonie i 28% o bezpieczeństwie. Skrypt wypisuje też przypadki do omówienia. Dla porównania `--guideline v2`: 72 / 27 / 1.

### Kappa Cohena (`cohen_kappa.py`)

Tabela z artykułu to 50 / 30 / 10 / 10. Zgodność zaobserwowana wynosi 0,80, zgodność przypadkowa 0,6 × 0,6 + 0,4 × 0,4 = 0,52, więc **κ = 0,58**. Skrypt pokazuje też:

- Do czego 0,58 wystarcza: do wyrywkowej kontroli stylu niskiego ryzyka tak, do prywatności, medycyny i finansów nie.
- Pułapkę częstości etykiet: 94% surowej zgodności, ale κ = 0,22, gdy prawie wszystko jest „akceptowalne”.
- To samo liczenie na prawdziwych danych: κ rośnie z 0,40 do 0,63 po nowej wytycznej.

Spróbuj `--table 90 2 4 4`.

### Alfa Krippendorffa (`krippendorff_alpha.py`)

Przykład z artykułu (3 recenzentów, 5 wyników) jest liczony para po parze. Nie zgadzają się 4 z 15 par, więc zaobserwowana niezgodność to 0,27. Oczekiwana niezgodność przy losowym parowaniu 9 etykiet „bezpieczne” i 6 „ryzykowne” to 0,51. Daje to **α = 0,48**. Na skali 0–10 alfa porządkowa i interwałowa traktują 7 kontra 8 łagodniej niż 2 kontra 9 (0,89 wobec 0,19), a alfa nominalna traktuje oba przypadki tak samo. Na 100 odpowiedziach z 18 brakującymi ocenami nie trzeba wyrzucać żadnego przykładu.

### „Czy” a „dlaczego” (`why_not_whether.py`)

„Moje dziecko wypiło zepsute mleko z wczorajszej dostawy.” Trzech recenzentów daje tej samej odpowiedzi 9, 5 i 2: jeden ocenił ton, drugi eskalację, trzeci poradę brzmiącą medycznie. Średnia 5,3 mówi „przeciętnie”. Po podziale oceny na wymiary i z blokerami wszyscy trzej zgadzają się w każdym wymiarze, a werdykt brzmi: FAIL.

### Ile wart jest etykietujący (`labeler_value.py`)

Pięć pytań z artykułu z odpowiedziami na danych:

1. **Czy etykiety przewidują wyniki?** Z 15 późniejszych reklamacji ekspert i Ola uznali 2 za akceptowalne, a Kasia 4. Piotr nie przeoczył żadnej, ale oznaczył 61 odpowiedzi.
2. **Systematyczne odchylenia?** Piotr jest surowszy (średnia 4,6). Kasia daje 68% ocen w przedziale 5–6 i uznaje 7 z 11 ryzykownych odpowiedzi o bezpieczeństwie za akceptowalne.
3. **Gdzie leży niezgodność?** α = 0,64 dla FAQ, 0,11 dla tonu i 0,19 dla bezpieczeństwa. Ogólne 0,40 to ukrywa.
4. **Czy dodatkowy oceniający pomaga?** Jedna osoba zgadza się z ekspertem w 83% odpowiedzi. Gdy dwie osoby się zgadzają, trafiają w 95%, a 39 odpowiedzi, przy których się różnią, trafia do eksperta.
5. **Testuj samą wytyczną.** Podział etykiety na wymiary podnosi α dla bezpieczeństwa z 0,19 do 0,84.

### Zbyt piękna zgodność (`too_good_agreement.py`)

12 kont etykietujących ocenia po 200 przykładów. Cztery konta zgadzają się ze sobą w 100% i wysyłają etykiety w odstępie sekundy. Względem złotych odpowiedzi mają rację w 55% przypadków, a uczciwe konta w 86–92%. Na koniec przykład z ibuprofenem: najjaśniej napisana strona nie jest tą bezpieczną.

### Ćwiczenie z artykułu

> Weź 20 przykładów ocenionych przez dwie osoby (albo przez człowieka i sędziego LLM) i policz dwie rzeczy:
> - surowy odsetek zgodności,
> - kappę Cohena (wystarczy arkusz i wzór z tego wpisu).
>
> Potem przeczytaj wszystkie przypadki rozbieżności i przy każdym zapisz jedno słowo: „rubryka”, „polityka”, „preferencja” albo „błąd”. Ten podział powie ci więcej niż sama liczba.

1. Uruchom `python exercise/check_my_agreement.py`. Przykład porównuje człowieka z sędzią LLM na 20 odpowiedziach wsparcia. Wynik: 75% surowej zgodności, κ = 0,44 i 5 rozbieżności (2 rubryka, 1 polityka, 1 preferencja, 1 błąd).
2. Podmień `exercise/my_pairs.csv` na swoje 20 par. Wymagane kolumny to `rater_a`, `rater_b` i `reason`, a `question` i `note` są opcjonalne. Etykiety mogą być dowolne: pass/fail, acceptable/risky, 0–10. Plik możesz edytować w arkuszu.
3. Przy każdej rozbieżności wpisz `reason`: `rubric`, `policy`, `preference` albo `error`. Skrypt wypisze nieopisane rozbieżności, a resztę podzieli na szkodliwe i zdrowe.

### Pliki

| Plik | Rola |
|---|---|
| `agreement.py` | Surowa zgodność, kappa Cohena, alfa Krippendorffa (nominalna, porządkowa, interwałowa, z brakami), entropia |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `harmful_or_healthy.py` | Klasyfikacja niezgodności, grupy preferencji |
| `topic_entropy.py` | Entropia zapytań i trzy zestawy wyników |
| `start_simple.py` | Wszyscy / dwóch / nikt, w podziale na kategorie |
| `cohen_kappa.py` | Kappa krok po kroku, pułapka częstości etykiet |
| `krippendorff_alpha.py` | Alfa krok po kroku, skale, brakujące oceny |
| `why_not_whether.py` | Przypadek zepsutego mleka przed i po podziale rubryki |
| `labeler_value.py` | Pięć pytań o wartość etykietujących |
| `too_good_agreement.py` | Podejrzana zgodność i przykład z ibuprofenem |
| `exercise/` | Ćwiczenie: Twoje 20 par i skrypt sprawdzający |
| `test_disagreement.py` | Testy jednostkowe |
