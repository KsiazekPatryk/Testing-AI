# 13 — The Score Went Up, the Product Did Not

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**The Score Went Up, but the Product Did Not Change**](https://paprico.substack.com/p/wynik-wzros-a-produkt-sie-nie-zmieni) (in English, also available in Polish).

The previous post said that a high benchmark score is not yet a product, and that you should build an evaluation that fits your own system. This one is about how that evaluation can fool the team that built it, and how to prevent it. The folder covers:

- red-teaming alongside random samples;
- versioning everything that makes up an evaluation;
- scores that are too beautiful;
- NDCG for ranking;
- why a record from many runs is a lead, not proof.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. The system under test is an offline stand-in (`assistant.py`), described by its defenses and how reliably each one holds.

### Run it

```bash
python red_team.py                        # random samples see the average, attacks see the edges
python score_went_up.py                   # 78 -> 86 overnight, and nothing was deployed
python too_good.py                        # 100% overnight: a system that knows the exam
python ndcg.py                            # not only what is on the list, but where
python record_is_a_lead.py                # the best of many runs is inflated by construction
python exercise/check_my_score_change.py  # the exercise from the post
python -m unittest -v test_score_up
```

### Red team (`red_team.py`)

The script first checks that the run is authorized: an approved environment, written rules, and people who know (`data/red_team_rules.json`). `--env production` is refused.

On ordinary traffic, v1 handles 97.8% of 500 conversations correctly. The 16 red-team cases tell a different story. They come from the post's families: jailbreak, role-play, multi-turn escalation, malicious context, conflicting policies, pressure and authority, plus agent cases for payments, irreversible actions, tool permissions and rollback. Run 5 times each, only 4 of 16 attacks fully hold, and 4 critical bypasses become blockers. The two results are reported side by side, never averaged.

After the fixes (v2), 14 of 16 hold. Then v3 makes "harmless" prompt changes for a warmer tone. Ordinary traffic rises to 98.8%, but three attacks that had been fixed (role-play, pressure, a payment) come back: `python red_team.py --version v2`.

### The score went up, the product did not change (`score_went_up.py`)

The search dashboard jumps from 78.3 to 86.1 overnight. The package manifests show no product change at all and seven measurement changes. Applied one at a time to the same product:

| Change | Score |
|---|---|
| package v14 | 78.3% |
| + replace stale expected results | 79.2% |
| + refresh the search-data snapshot | 80.0% |
| + update the judge model | 80.8% |
| + widen the rubric (weaker citations pass) | 82.5% |
| + remove 12 disputed hard queries | 86.1% |

The dashboard breaks its trend line where the package changes. The honest comparison runs both product versions on the same package, and they score the same. The script also flags the privacy gap: the new package holds real user queries, but nobody has set who can view it or how long it is kept, and anyone with repo access can edit it.

### Too beautiful (`too_good.py`)

- **Tuning against the test set.** Special cases for failing test queries take the test set from 78% to 100% in four nights, while fresh queries move from 78.0% to 79.1%. The system learned the exam.
- **Reusing one holdout.** Eight equally good prompt variants per round, and the best on the same holdout is kept each time. After 25 rounds the holdout shows 87%, and the chosen variant gets 78% on fresh data. The evaluation measures exposure, not generalization.

### NDCG (`ndcg.py`)

The post's example, "how do I turn off a feature on my child's school account":

| Order | NDCG@4 |
|---|---|
| 3, 2, 1, 0 (ideal) | 1.00 |
| 3, 2, 0, 1 (last two swapped) | 0.99 |
| 2, 3, 1, 0 (first two swapped) | 0.92 |
| 1, 0, 2, 3 (documentation last) | 0.69 |
| 0, 1, 2, 3 (reversed) | 0.61 |

The script shows the calculation step by step (`--order 2 3 1 0`). It then compares two rankers on 30 queries. Both have recall@10 = 1.00, but NDCG@3 is 1.00 vs 0.90, and the faster ranker is the worse one. That is a trade-off, not one number.

### A record is a lead, not proof (`record_is_a_lead.py`)

20 attempts at "improving" a prompt that really averages 8.0 produce a record of 8.60 at attempt 13. The expected best of n runs climbs from 8.00 at n = 1 to 8.56 at n = 20, with nothing improved. Keeping only the best three runs (mean 8.47) deletes the other 17. The recipe:

- report all runs: mean 8.02, sd 0.30, 95% CI 7.88–8.16;
- re-run the record's setup on a fresh holdout (7.86);
- set a stopping rule in advance.

### The exercise from the post

> Take the last score increase on your evaluation dashboard and write two lists: what changed in the product, and what changed in the measuring instrument (dataset, labels, rubric, judge, data). If the second list is not empty, the increase needs to be re-checked on a comparable package.

1. Run `python exercise/check_my_score_change.py`. In the example the team believes "the new ranking worked". The package manifests show that nothing was deployed and seven measurement items changed, so the increase is entirely the instrument.
2. Open `exercise/my_score_change.json` and write your two lists. If you have package manifests, point `packages` to them and the script compares your lists with the actual diff.

### Files

| File | Role |
|---|---|
| `evalkit.py` | Mean, 95% CI, NDCG, package fingerprint and diff (product vs measurement fields) |
| `assistant.py` | The offline system under test: defenses per version |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `red_team.py` | Authorization, ordinary vs red-team results, blockers, regressions |
| `score_went_up.py` | 78 → 86 without a product change, step by step; the broken trend line; privacy |
| `too_good.py` | Tuning against the test set; a reused holdout |
| `ndcg.py` | NDCG step by step, the post's example, two rankers |
| `record_is_a_lead.py` | The run log, best-of-n inflation, the recipe |
| `exercise/` | The exercise: your last score increase and the checker |
| `test_score_up.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Wynik wzrósł, a produkt się nie zmienił”**](https://paprico.substack.com/p/wynik-wzros-a-produkt-sie-nie-zmieni) (po angielsku, z wersją po polsku).

Poprzedni wpis mówił, że wysoki wynik w benchmarku to jeszcze nie produkt i że trzeba budować ewaluację dopasowaną do własnego systemu. Ten jest o tym, jak taka ewaluacja potrafi oszukać zespół, który ją zbudował, i jak temu zapobiec. Folder pokazuje:

- red-team obok losowych próbek;
- wersjonowanie wszystkiego, co składa się na ewaluację;
- zbyt piękne wyniki;
- NDCG dla rankingu;
- dlaczego rekord z wielu przebiegów to trop, a nie dowód.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Testowany system to zamiennik działający offline (`assistant.py`), opisany przez swoje zabezpieczenia i to, jak niezawodnie każde z nich działa.

### Uruchom

```bash
python red_team.py                        # losowe próbki widzą średnią, ataki widzą krawędzie
python score_went_up.py                   # 78 -> 86 w nocy, a nic nie wdrożono
python too_good.py                        # 100% z dnia na dzień: system, który zna egzamin
python ndcg.py                            # liczy się nie tylko co, ale gdzie
python record_is_a_lead.py                # najlepszy z wielu przebiegów jest z natury zawyżony
python exercise/check_my_score_change.py  # ćwiczenie z artykułu
python -m unittest -v test_score_up
```

### Red-team (`red_team.py`)

Skrypt najpierw sprawdza, czy przebieg jest autoryzowany: zatwierdzone środowisko, pisemne zasady i ludzie, którzy o nim wiedzą (`data/red_team_rules.json`). `--env production` zostaje odrzucone.

Na zwykłym ruchu v1 poprawnie obsługuje 97,8% z 500 rozmów. 16 przypadków red-teamu pokazuje co innego. Pochodzą z rodzin opisanych w artykule: jailbreak, odgrywanie ról, eskalacja w wielu turach, złośliwy kontekst, sprzeczne polityki, presja i autorytet, a do tego przypadki dla agentów: płatności, nieodwracalne działania, uprawnienia narzędzi i wycofywanie skutków. Przy 5 uruchomieniach każdego przypadku w pełni wytrzymują tylko 4 z 16 ataków, a 4 krytyczne obejścia stają się blokerami. Oba wyniki są raportowane obok siebie i nigdy nie są uśredniane.

Po poprawkach (v2) wytrzymuje 14 z 16. Potem v3 wprowadza „niewinne” zmiany promptu dla cieplejszego tonu. Zwykły ruch rośnie do 98,8%, ale wracają trzy naprawione wcześniej ataki (odgrywanie ról, presja, płatność): `python red_team.py --version v2`.

### Wynik wzrósł, a produkt się nie zmienił (`score_went_up.py`)

Dashboard wyszukiwarki skacze w nocy z 78,3 do 86,1. Manifesty pakietów nie pokazują żadnej zmiany w produkcie i siedem zmian w pomiarze. Zastosowane po jednej do tego samego produktu:

| Zmiana | Wynik |
|---|---|
| pakiet v14 | 78,3% |
| + zastąpienie nieaktualnych oczekiwanych wyników | 79,2% |
| + odświeżenie zrzutu danych wyszukiwania | 80,0% |
| + aktualizacja modelu sędziego | 80,8% |
| + rozszerzenie rubryki (słabsze cytowania przechodzą) | 82,5% |
| + usunięcie 12 spornych trudnych zapytań | 86,1% |

Dashboard przerywa linię trendu tam, gdzie zmienia się pakiet. Uczciwe porównanie uruchamia obie wersje produktu na tym samym pakiecie i obie dostają ten sam wynik. Skrypt wskazuje też lukę w prywatności: nowy pakiet zawiera prawdziwe zapytania użytkowników, ale nikt nie ustalił, kto może je oglądać ani jak długo są przechowywane, a edytować może każdy z dostępem do repozytorium.

### Zbyt piękny wynik (`too_good.py`)

- **Strojenie pod zestaw testowy.** Przypadki specjalne dla nieudanych zapytań testowych podnoszą zestaw testowy z 78% do 100% w cztery noce, a świeże zapytania rosną z 78,0% do 79,1%. System nauczył się egzaminu.
- **Ponowne użycie jednego zbioru odłożonego.** W każdej rundzie jest osiem równie dobrych wariantów promptu i za każdym razem zostaje ten najlepszy na tym samym zbiorze. Po 25 rundach zbiór odłożony pokazuje 87%, a wybrany wariant ma 78% na świeżych danych. Ewaluacja mierzy ekspozycję, a nie uogólnianie.

### NDCG (`ndcg.py`)

Przykład z artykułu: „jak wyłączyć funkcję na szkolnym koncie dziecka”.

| Kolejność | NDCG@4 |
|---|---|
| 3, 2, 1, 0 (idealna) | 1,00 |
| 3, 2, 0, 1 (zamienione dwa ostatnie) | 0,99 |
| 2, 3, 1, 0 (zamienione dwa pierwsze) | 0,92 |
| 1, 0, 2, 3 (dokumentacja na końcu) | 0,69 |
| 0, 1, 2, 3 (odwrotna) | 0,61 |

Skrypt pokazuje obliczenie krok po kroku (`--order 2 3 1 0`). Potem porównuje dwa rankery na 30 zapytaniach. Oba mają recall@10 = 1,00, ale NDCG@3 wynosi 1,00 wobec 0,90, a szybszy ranker jest tym gorszym. To kompromis, a nie jedna liczba.

### Rekord to trop, a nie dowód (`record_is_a_lead.py`)

20 prób „poprawienia” promptu, który naprawdę ma średnio 8,0, daje rekord 8,60 w 13. próbie. Oczekiwany najlepszy wynik z n przebiegów rośnie z 8,00 przy n = 1 do 8,56 przy n = 20, choć nic się nie poprawiło. Zostawienie tylko trzech najlepszych przebiegów (średnia 8,47) usuwa pozostałe 17. Recepta:

- raportuj wszystkie przebiegi: średnia 8,02, sd 0,30, 95% CI 7,88–8,16;
- uruchom ustawienia rekordu na świeżym zbiorze odłożonym (7,86);
- z góry ustal, kiedy przestajesz próbować.

### Ćwiczenie z artykułu

> Weź ostatni wzrost wyniku na waszym dashboardzie ewaluacyjnym i zapisz dwie listy: co zmieniło się w produkcie, a co w narzędziu pomiarowym (zbiór, etykiety, rubryka, sędzia, dane). Jeśli druga lista nie jest pusta, ten wzrost wymaga ponownego sprawdzenia na porównywalnym pakiecie.

1. Uruchom `python exercise/check_my_score_change.py`. W przykładzie zespół wierzy, że „zadziałał nowy ranking”. Manifesty pakietów pokazują, że nic nie wdrożono, a zmieniło się siedem elementów pomiaru, więc cały wzrost pochodzi z narzędzia pomiarowego.
2. Otwórz `exercise/my_score_change.json` i wpisz swoje dwie listy. Jeśli masz manifesty pakietów, wskaż je w `packages`, a skrypt porówna Twoje listy z rzeczywistymi różnicami.

### Pliki

| Plik | Rola |
|---|---|
| `evalkit.py` | Średnia, 95% CI, NDCG, odcisk pakietu i różnice (pola produktu a pola pomiaru) |
| `assistant.py` | Testowany system offline: zabezpieczenia w każdej wersji |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `red_team.py` | Autoryzacja, zwykły ruch a red-team, blokery, regresje |
| `score_went_up.py` | 78 → 86 bez zmiany produktu, krok po kroku; przerwana linia trendu; prywatność |
| `too_good.py` | Strojenie pod zestaw testowy; wielokrotnie używany zbiór odłożony |
| `ndcg.py` | NDCG krok po kroku, przykład z artykułu, dwa rankery |
| `record_is_a_lead.py` | Dziennik przebiegów, zawyżenie najlepszego z n, recepta |
| `exercise/` | Ćwiczenie: Twój ostatni wzrost wyniku i skrypt sprawdzający |
| `test_score_up.py` | Testy jednostkowe |
