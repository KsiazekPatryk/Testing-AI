# 14 — A Metric Compresses Judgment

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**A Quality Metric Compresses Judgment, It Does Not Replace It**](https://paprico.substack.com/p/metryka-jakosci-to-kompresja-osadu).

The previous two posts were about reading benchmarks and keeping an evaluation honest. This one is about turning many observations into a number you can make decisions with, and about what that number will not tell you. The folder covers:

- a weighted metric with weights frozen before the results, and blockers outside the average;
- what a metric leaves out, and why it needs a measurement model, not just a chart;
- why correct but ugly is a failure too;
- the curve that bends;
- why quality is relative, and why competitors are not the truth;
- why even exams need testing.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. All products, companies and numbers are simulated; the Zillow part uses simulated data to show the lesson, not Zillow's figures.

### Run it

```bash
python weighted_metric.py               # 0.84, weights before results, the allergy blocker
python what_metric_misses.py            # same accuracy, different business; the dwell-time spike
python correct_but_ugly.py              # seven correct outputs, not seven good ones
python taste_at_scale.py                # pairwise vs absolute, the demo slice, human effort
python bending_curve.py                 # the straight line you are tempted to draw
python quality_is_relative.py           # 4.2 s sounds fine until the peers load in 1.1 s
python exams_need_testing.py            # 92% on the exam, and what the exam measures
python exercise/audit_my_eval_suite.py  # the exercise from the post
python -m unittest -v test_metric
```

### A weighted metric with blockers (`weighted_metric.py`)

The shop chatbot example from the post (`data/metric_spec.json`, `data/candidates.json`):

| Criterion | Weight | Candidate A |
|---|---|---|
| correctness | 0.30 | 0.90 |
| grounding in sources | 0.20 | 0.80 |
| policy compliance | 0.20 | 1.00 |
| tone | 0.10 | 0.70 |
| escalation quality | 0.10 | 0.60 |
| resolution | 0.10 | 0.80 |
| **weighted score** | | **0.84** |

- **Weights before results.** The weights were frozen on 2026-11-02 with a fingerprint; the run was on 2026-11-09. With the frozen weights A beats B (0.840 vs 0.827). With the "tone matters more" weights proposed the day after the run, B wins (0.857 vs 0.810). Same answers, a different winner.
- **The blocker.** A parent must cancel nut snacks because their child has an allergy, and the order ships in 12 minutes (`data/allergy_case.json`). A helpfulness judge prefers the warm reply (8/10 vs 6/10), and its weighted score is 0.79. The script reads the trace instead: the warm reply did not recognize the risk, did not look up the order, did not use the remove tool and did not confirm the final state. The nuts stay in the order.
- **Outside the average.** Put the blocker checks into the average with weight 0.10 and the warm reply still scores 0.73, above the 0.70 threshold. Kept outside, the gate says: candidate A (0.84) **BLOCKED**, candidate B (0.83) **GO**.

### What the metric misses (`what_metric_misses.py`)

**Same accuracy, different business.** Two valuation models for a home-flipping business, both with 4.0% mean absolute error, over 8 quarters while the market turns:

| Model | MAPE | Total profit | Worst quarter | Losing homes |
|---|---|---|---|---|
| independent errors | 4.0% | +3.15 M | +0.07 M | 90/320 |
| momentum (correlated errors) | 4.0% | −0.35 M | −1.60 M | 123/320 |

The momentum model overvalues every home at once when the market turns. How fast the business can stop matters as much: stopping one quarter after the first loss keeps +1.42 M, stopping three quarters later ends at −0.72 M.

**A measurement model, not just a chart.** "Satisfaction" as time on the results page: the histogram has a spike at "60+" because everything above the cap is one bucket. Of the 1,320 sessions counted as satisfied, 35% are slow pages, switched tabs and emails. Instrumenting load time and hidden-tab time removes 404 of them; 53 are still not satisfaction. The script ends with a prompt that asks an LLM to attack your metric.

### Correct but ugly (`correct_but_ugly.py`)

Seven outputs, all passing the fact check (`data/style_outputs.json`). The rubric (`data/style_rubric.json`) names the dimensions, the anchors (10 publish as is, 7 solid but bland, 4 understandable but off-brand, 1 embarrassing or harmful) and the negative examples (generic, salesy, overconfident, alarming, too dense). A checker cannot give a 10; it can stop a 4 from being rated a 7:

| Output | Context | Highest possible score | Why |
|---|---|---|---|
| refund_plain | consumer | no ceiling | — |
| refund_salesy | consumer | 1 | generic, overconfident, exclamations |
| refund_dense | consumer | 7 | 70 words in one sentence |
| ldl_alarming | medical | 1 | causes panic |
| ldl_soothing | medical | 1 | "nothing to worry about": more certainty than the model has |
| ldl_warm | medical | 7 (no ceiling as a consumer reply) | one exclamation mark |
| ldl_calm | medical | no ceiling | — |

Accessibility: dashboard v1 has the right numbers and six problems (text contrast 2.6:1, 1.9:1 and 2.1:1 where 4.5:1 is needed, nine series colours, skipped heading levels, two charts without alt text). Taste does not override usability.

### Taste at scale (`taste_at_scale.py`)

- **Pairwise beats absolute.** One rater, 60 equally good outputs: the mean absolute score drops from 6.65 (first 20) to 5.50 (last 20). In 32% of the pairs where a late output is clearly better, the absolute scores rank the early one higher. Pairwise judgments agree with the hidden quality 85% of the time in both halves of the session.
- **Sample widely.** Demo slice 8.8, long documents 6.2, Polish 7.0, dense data 5.2, health topics 6.9.
- **Distance from human effort.** Writing by hand takes about 35 minutes. The demo slice needs a 2-minute edit; every other slice needs 13–22 minutes and a full rewrite in 22–35% of cases: a first-draft generator, not a system that produces finished work.

### The curve that bends (`bending_curve.py`)

- Your 8 releases with 95% bands: the r4 "regression" is noise, and the points look like a straight line.
- A straight line (+3.8% per release) reaches the leader's 92% in about 2 releases. A saturating curve fits your points just as well and says 85% (in 2) and 88% (in 4). Your data cannot tell them apart; the leader's history can.
- The leader: underlying gain per release falls from +0.8% to +0.2% while the effort rises from 2 to 28 person-weeks (from 2 to 175 person-weeks per point). Almost every single-release change is within the noise of 400 cases.
- The last release per segment: returns 81% → 90%, shipping 88% → 85%, billing 86% → 82%; the headline barely moves.
- Instead of "perfect AI", an acceptable level of measured risk: the leader's failure rate (8.2%, interval up to 11.4%) meets the 12% target; yours (18.2%) does not yet.

### Quality is relative (`quality_is_relative.py`)

The method comes first: the peer group, the tasks, the measurement and what is not controlled (`data/peer_group.json`). Without it (`--no-method`) the script refuses to compare.

| Measure | Us | Peers (median) | We beat |
|---|---|---|---|
| login screen load time | 4.2 s | 1.1 s (n=20) | 0% |
| refund cases resolved | 72% | 88% (n=10) | 0% |
| tool calls for a small order change | 12 | 4 (n=5) | 0% |

All 20 peers show a clear error message and a visible way to reach a person; we do not. The dictionary app's cold start (6.8 s vs 0.6–1.1 s, because it loads the whole 38 MB dictionary) is the chart that changes the mood. And competitors are not the truth: 17 of 20 use pre-ticked marketing consent, which is not valid consent under the GDPR. Keep "competitors do it", "users need it" and "the law requires it" apart.

### Even exams need testing (`exams_need_testing.py`)

A model scores 11/12 (92%) on a certification-style exam written for this example (`data/exam_questions.json`). Testing the exam: 6 items appear word for word in a public question bank (`data/training_snippets.txt`), 1 is ambiguous, 2 have a second defensible answer, and on q09 the key marks the better answer for an LLM system as wrong. On the 5 items that survive, the score is 4/5 or 5/5 with intervals of 38–96% and 57–100%: too small to say anything. The exam has 5 terminology, 4 syllabus and 3 format items, and 0 items on defining risk, building a rubric, choosing a sample, interpreting uncertainty, questioning benchmarks or defending a release decision. The script points to the folders of this repository where each of those is practised.

### The exercise from the post

> Treat your evaluation suite like a product and check: who owns it; whether the data, labels, rubric and judge are versioned; which cases are out of date; whether the cases could have leaked into training data or been used for tuning again and again; whether the metric matches how users experience the product; whether the result can change the release decision. If the answer to the last question is "no", you have decoration, not an evaluation.

1. Run `python exercise/audit_my_eval_suite.py`. The example suite has no owner, an unversioned rubric and judge, half of its cases unreviewed for over a year, 31 tuning rounds without a holdout, and a metric that is not what users experience. Its result cannot change a release: decoration.
2. Open `exercise/my_eval_suite.json` and write your own answers. A "yes" on the last question only counts with the last time it actually changed a decision.

### Nine principles, and where they live in this repository

| Principle from the post | Where |
|---|---|
| Read benchmarks by asking what they measure and what they do not | 12 `what_benchmarks_measure.py`, `six_questions.py` |
| Copy the measurement idea, not the score | 12 `copy_the_idea.py` |
| Keep random samples apart from red-teaming | 13 `red_team.py` |
| Version everything that makes up an evaluation | 13 `score_went_up.py` |
| Measure ranking where order matters | 13 `ndcg.py` |
| Report all runs, not the record | 13 `record_is_a_lead.py` |
| Build an explicit metric with blockers outside the average | 14 `weighted_metric.py` |
| Do not forget aesthetic quality | 14 `correct_but_ugly.py`, `taste_at_scale.py` |
| Treat comparison with competitors as a lens | 14 `quality_is_relative.py` |

### Files

| File | Role |
|---|---|
| `metrickit.py` | Weighted score, fingerprint, Wilson interval, WCAG contrast, percentile rank, n-gram overlap |
| `generate_data.py`, `data/` | Example data used by every script (always the same content) |
| `weighted_metric.py` | The 0.84 metric, weights before results, the allergy blocker, the release gate |
| `what_metric_misses.py` | Same accuracy, different business; stopping speed; the dwell-time measurement model |
| `correct_but_ugly.py` | Negative examples, context, anchors and ceilings, accessibility |
| `taste_at_scale.py` | Pairwise vs absolute ratings, wide sampling, distance from human effort |
| `bending_curve.py` | Uncertainty bands, line vs curve, diminishing returns, segments, acceptable risk |
| `quality_is_relative.py` | The peer group method, relative numbers, absence as evidence, competitors vs users vs law |
| `exams_need_testing.py` | An exam tested as an evaluation: leaks, ambiguity, the oracle, skill coverage |
| `exercise/` | The exercise: audit your evaluation suite |
| `test_metric.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Metryka jakości to kompresja osądu, nie jego zamiennik”**](https://paprico.substack.com/p/metryka-jakosci-to-kompresja-osadu).

Dwa poprzednie wpisy były o czytaniu benchmarków i o tym, jak utrzymać ewaluację w uczciwości. Ten jest o tym, jak zamienić wiele obserwacji w liczbę, na podstawie której można podejmować decyzje, i czego ta liczba nie powie. Folder pokazuje:

- metrykę ważoną z wagami zamrożonymi przed wynikami i blokery poza średnią;
- co metryka pomija i dlaczego potrzebuje modelu pomiaru, a nie tylko wykresu;
- dlaczego poprawne, ale brzydkie to też awaria;
- krzywą, która się wygina;
- dlaczego jakość jest względna i dlaczego konkurenci to nie prawda;
- dlaczego nawet egzaminy wymagają testowania.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Wszystkie produkty, firmy i liczby są symulowane; część o Zillow pokazuje lekcję na danych symulowanych, a nie na danych Zillow.

### Uruchom

```bash
python weighted_metric.py               # 0,84, wagi przed wynikami, bloker z alergią
python what_metric_misses.py            # ta sama dokładność, inny biznes; skok w czasie na stronie
python correct_but_ugly.py              # siedem poprawnych wyników, a nie siedem dobrych
python taste_at_scale.py                # pary a skala bezwzględna, wycinek z demo, wysiłek człowieka
python bending_curve.py                 # prosta, którą kusi narysować
python quality_is_relative.py           # 4,2 s brzmi dobrze, dopóki konkurenci nie ładują się w 1,1 s
python exams_need_testing.py            # 92% na egzaminie i co ten egzamin mierzy
python exercise/audit_my_eval_suite.py  # ćwiczenie z artykułu
python -m unittest -v test_metric
```

### Metryka ważona z blokerami (`weighted_metric.py`)

Przykład chatbota sklepu z artykułu (`data/metric_spec.json`, `data/candidates.json`):

| Kryterium | Waga | Kandydat A |
|---|---|---|
| poprawność | 0,30 | 0,90 |
| ugruntowanie w źródłach | 0,20 | 0,80 |
| zgodność z polityką | 0,20 | 1,00 |
| ton | 0,10 | 0,70 |
| jakość eskalacji | 0,10 | 0,60 |
| rozwiązanie sprawy | 0,10 | 0,80 |
| **wynik ważony** | | **0,84** |

- **Wagi przed wynikami.** Wagi zamrożono 2026-11-02 razem z odciskiem (hashem), a przebieg odbył się 2026-11-09. Przy zamrożonych wagach A wygrywa z B (0,840 wobec 0,827). Przy wagach „ton jest ważniejszy”, zaproponowanych dzień po przebiegu, wygrywa B (0,857 wobec 0,810). Te same odpowiedzi, inny zwycięzca.
- **Bloker.** Rodzic musi anulować przekąski orzechowe, bo dziecko ma alergię, a zamówienie wychodzi za 12 minut (`data/allergy_case.json`). Sędzia pomocności woli ciepłą odpowiedź (8/10 wobec 6/10), a jej wynik ważony to 0,79. Skrypt czyta zamiast tego ślad działań: ciepła odpowiedź nie rozpoznała ryzyka, nie sprawdziła zamówienia, nie użyła narzędzia do usunięcia pozycji i nie potwierdziła stanu końcowego. Orzechy zostają w zamówieniu.
- **Poza średnią.** Po wrzuceniu sprawdzeń blokera do średniej z wagą 0,10 ciepła odpowiedź nadal ma 0,73, powyżej progu 0,70. Trzymane osobno dają werdykt bramki: kandydat A (0,84) **ZABLOKOWANY**, kandydat B (0,83) **GO**.

### Czego metryka nie widzi (`what_metric_misses.py`)

**Ta sama dokładność, inny biznes.** Dwa modele wyceny w biznesie skupu i odsprzedaży domów, oba ze średnim błędem bezwzględnym 4,0%, przez 8 kwartałów, w których rynek się odwraca:

| Model | MAPE | Zysk łącznie | Najgorszy kwartał | Domy ze stratą |
|---|---|---|---|---|
| błędy niezależne | 4,0% | +3,15 mln | +0,07 mln | 90/320 |
| momentum (błędy skorelowane) | 4,0% | −0,35 mln | −1,60 mln | 123/320 |

Model momentum przeszacowuje wszystkie domy naraz, gdy rynek się odwraca. Równie ważne jest to, jak szybko firma potrafi się zatrzymać: zatrzymanie zakupów kwartał po pierwszej stracie daje +1,42 mln, trzy kwartały po niej −0,72 mln.

**Model pomiaru, nie tylko wykres.** „Satysfakcja” mierzona czasem na stronie wyników: histogram ma skok przy „60+”, bo wszystko powyżej progu trafia do jednego przedziału. Z 1320 sesji uznanych za udane 35% to wolne strony, przełączone karty i odpisywanie na maile. Pomiar czasu ładowania i czasu ukrytej karty usuwa 404 z nich; 53 nadal nie są satysfakcją. Na koniec skrypt podaje prompt, w którym prosisz LLM o atak na własną metrykę.

### Poprawne, ale brzydkie (`correct_but_ugly.py`)

Siedem wyników, wszystkie przechodzą sprawdzenie faktów (`data/style_outputs.json`). Rubryka (`data/style_rubric.json`) nazywa wymiary, kotwice skali (10 można publikować bez poprawek, 7 solidne, ale nijakie, 4 zrozumiałe, ale nie w stylu marki, 1 żenujące lub szkodzące marce) i przykłady negatywne (generyczny, sprzedażowy, zbyt pewny siebie, alarmujący, zbyt gęsty). Automat nie da 10; może powstrzymać czwórkę przed oceną 7:

| Wynik | Kontekst | Najwyższa możliwa ocena | Dlaczego |
|---|---|---|---|
| refund_plain | konsumencki | bez sufitu | — |
| refund_salesy | konsumencki | 1 | generyczny, zbyt pewny siebie, wykrzykniki |
| refund_dense | konsumencki | 7 | 70 słów w jednym zdaniu |
| ldl_alarming | medyczny | 1 | wywołuje panikę |
| ldl_soothing | medyczny | 1 | „nothing to worry about”: więcej pewności, niż ma model |
| ldl_warm | medyczny | 7 (bez sufitu jako odpowiedź konsumencka) | jeden wykrzyknik |
| ldl_calm | medyczny | bez sufitu | — |

Dostępność: dashboard v1 ma poprawne liczby i sześć problemów (kontrast tekstu 2,6:1, 1,9:1 i 2,1:1 przy wymaganym 4,5:1, dziewięć kolorów serii, pominięte poziomy nagłówków, dwa wykresy bez tekstu alternatywnego). Smak nie uchyla użyteczności.

### Ocena estetyki na większą skalę (`taste_at_scale.py`)

- **Pary wygrywają ze skalą bezwzględną.** Jeden oceniający, 60 równie dobrych wyników: średnia ocena spada z 6,65 (pierwsze 20) do 5,50 (ostatnie 20). W 32% par, w których późniejszy wynik jest wyraźnie lepszy, oceny bezwzględne stawiają wyżej wcześniejszy. Porównania parami zgadzają się z ukrytą jakością w 85% przypadków w obu połowach sesji.
- **Próbkuj szeroko.** Wycinek z demo 8,8, długie dokumenty 6,2, polski 7,0, gęste dane 5,2, tematy zdrowotne 6,9.
- **Dystans od ludzkiego wysiłku.** Ręczne napisanie zajmuje około 35 minut. Wycinek z demo wymaga 2 minut poprawek; każdy inny 13–22 minut i całkowitego przepisania w 22–35% przypadków: to generator pierwszego szkicu, a nie system, który oddaje gotową pracę.

### Krzywa, która się wygina (`bending_curve.py`)

- Twoje 8 wydań z pasmami 95%: „regresja” w r4 to szum, a punkty układają się w prostą.
- Prosta (+3,8% na wydanie) dogania 92% lidera w około 2 wydania. Krzywa nasycenia pasuje do Twoich punktów równie dobrze i mówi 85% (za 2) oraz 88% (za 4). Twoje dane ich nie rozróżnią; historia lidera tak.
- Lider: rzeczywisty zysk na wydanie spada z +0,8% do +0,2%, a nakład rośnie z 2 do 28 osobotygodni (z 2 do 175 osobotygodni na punkt). Prawie każda zmiana między wydaniami mieści się w szumie 400 przypadków.
- Ostatnie wydanie w podziale na segmenty: zwroty 81% → 90%, wysyłka 88% → 85%, płatności 86% → 82%; wynik zbiorczy prawie stoi.
- Zamiast „idealnego AI” akceptowalny poziom zmierzonego ryzyka: odsetek błędów lidera (8,2%, przedział do 11,4%) spełnia cel 12%; Twój (18,2%) jeszcze nie.

### Jakość jest względna (`quality_is_relative.py`)

Najpierw metoda: grupa porównawcza, zadania, sposób pomiaru i to, czego nie kontrolujemy (`data/peer_group.json`). Bez niej (`--no-method`) skrypt odmawia porównania.

| Miara | My | Konkurenci (mediana) | Wyprzedzamy |
|---|---|---|---|
| czas ładowania ekranu logowania | 4,2 s | 1,1 s (n=20) | 0% |
| rozwiązane sprawy zwrotów | 72% | 88% (n=10) | 0% |
| wywołania narzędzi przy małej zmianie zamówienia | 12 | 4 (n=5) | 0% |

Wszystkich 20 konkurentów pokazuje jasny komunikat o błędzie i widoczny kontakt z człowiekiem; my nie. Zimny start aplikacji słownikowej (6,8 s wobec 0,6–1,1 s, bo wczytuje cały słownik o rozmiarze 38 MB) to wykres, który zmienia atmosferę w zespole. A konkurenci to nie prawda: 17 z 20 używa domyślnie zaznaczonej zgody marketingowej, która według RODO nie jest ważną zgodą. Oddzielaj „konkurenci tak robią”, „użytkownicy tego potrzebują” i „przepisy tego wymagają”.

### Nawet egzaminy wymagają testowania (`exams_need_testing.py`)

Model zdobywa 11/12 (92%) na egzaminie w stylu certyfikacyjnym, napisanym na potrzeby tego przykładu (`data/exam_questions.json`). Testowanie egzaminu: 6 pytań występuje słowo w słowo w publicznej bazie pytań (`data/training_snippets.txt`), 1 jest niejednoznaczne, 2 mają drugą uzasadnioną odpowiedź, a w q09 klucz uznaje za błędną odpowiedź lepszą dla systemu opartego na LLM. Na 5 pytaniach, które przetrwały przegląd, wynik to 4/5 albo 5/5, z przedziałami 38–96% i 57–100%: za mało, żeby cokolwiek powiedzieć. Egzamin ma 5 pytań z terminologii, 4 z sylabusa i 3 sprawdzające format, a 0 pytań o definiowanie ryzyka, budowę rubryki, dobór próbki, interpretację niepewności, kwestionowanie benchmarków czy obronę decyzji o wydaniu. Skrypt wskazuje foldery tego repozytorium, w których ćwiczy się każdą z tych umiejętności.

### Ćwiczenie z artykułu

> Potraktuj swój zestaw ewaluacyjny jak produkt i sprawdź: kto jest jego właścicielem; czy dane, etykiety, rubryka i sędzia są wersjonowane; które przypadki są już nieaktualne; czy przypadki mogły wyciec do danych treningowych lub być wielokrotnie użyte do strojenia; czy metryka odpowiada temu, jak użytkownicy doświadczają produktu; czy wynik może zmienić decyzję o wydaniu. Jeśli odpowiedź na ostatnie pytanie brzmi „nie”, masz dekorację, a nie ewaluację.

1. Uruchom `python exercise/audit_my_eval_suite.py`. Przykładowy zestaw nie ma właściciela, rubryka i sędzia nie są wersjonowane, połowa przypadków nie była przeglądana od ponad roku, był użyty 31 razy do strojenia bez zbioru odłożonego, a metryka nie mierzy tego, czego doświadczają użytkownicy. Jego wynik nie może zmienić decyzji o wydaniu: to dekoracja.
2. Otwórz `exercise/my_eval_suite.json` i wpisz własne odpowiedzi. „Tak” w ostatnim pytaniu liczy się dopiero z datą, kiedy wynik faktycznie zmienił decyzję.

### Dziewięć zasad i gdzie je znaleźć w repozytorium

| Zasada z artykułu | Gdzie |
|---|---|
| Czytać benchmarki, pytając, co mierzą, a czego nie | 12 `what_benchmarks_measure.py`, `six_questions.py` |
| Kopiować ideę pomiaru, nie wynik | 12 `copy_the_idea.py` |
| Oddzielać losowe próbki od red-teamu | 13 `red_team.py` |
| Wersjonować wszystko, co składa się na ewaluację | 13 `score_went_up.py` |
| Mierzyć ranking tam, gdzie kolejność ma znaczenie | 13 `ndcg.py` |
| Raportować wszystkie przebiegi, nie rekord | 13 `record_is_a_lead.py` |
| Budować jawną metrykę z blokerami poza średnią | 14 `weighted_metric.py` |
| Nie zapominać o jakości estetycznej | 14 `correct_but_ugly.py`, `taste_at_scale.py` |
| Traktować porównanie z konkurencją jako soczewkę | 14 `quality_is_relative.py` |

### Pliki

| Plik | Rola |
|---|---|
| `metrickit.py` | Wynik ważony, odcisk, przedział Wilsona, kontrast WCAG, ranga percentylowa, nakładanie się n-gramów |
| `generate_data.py`, `data/` | Przykładowe dane używane przez wszystkie skrypty (zawsze ta sama treść) |
| `weighted_metric.py` | Metryka 0,84, wagi przed wynikami, bloker z alergią, bramka wydania |
| `what_metric_misses.py` | Ta sama dokładność, inny biznes; szybkość zatrzymania; model pomiaru czasu na stronie |
| `correct_but_ugly.py` | Przykłady negatywne, kontekst, kotwice i sufity, dostępność |
| `taste_at_scale.py` | Oceny parami a bezwzględne, szerokie próbkowanie, dystans od ludzkiego wysiłku |
| `bending_curve.py` | Pasma niepewności, prosta a krzywa, malejące zwroty, segmenty, akceptowalne ryzyko |
| `quality_is_relative.py` | Metoda grupy porównawczej, liczby względne, brak jako dowód, konkurenci a użytkownicy a prawo |
| `exams_need_testing.py` | Egzamin przetestowany jak ewaluacja: wycieki, niejednoznaczność, wyrocznia, pokrycie umiejętności |
| `exercise/` | Ćwiczenie: audyt Twojego zestawu ewaluacyjnego |
| `test_metric.py` | Testy jednostkowe |
