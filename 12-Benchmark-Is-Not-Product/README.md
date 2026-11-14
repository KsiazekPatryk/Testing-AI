# 12 — A Benchmark Is Not a Product

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**A High Benchmark Score Is Not Yet a Product**](https://paprico.substack.com/p/wysoki-wynik-w-benchmarku-to-jeszcze) (in English, also available in Polish).

New model, new leaderboard record, new wave of excitement, and the same question every time: what does it mean for my product? This folder covers:

- what popular benchmarks actually measure;
- why they go stale;
- six questions to ask every result;
- how to carry the measurement idea, not the score, into your own evaluation;
- what to record about every run.

Runs without an API key and without installing any packages (Python 3.9+). Everything here (files, code, output) is in English. The models and benchmark results are simulated. The metrics (accuracy, pass@k, Bradley-Terry ranking, NDCG, MRR) are written out in `evals.py`.

### Run it

```bash
python what_benchmarks_measure.py      # eight benchmarks, eight different questions
python benchmarks_rot.py               # contamination and brittle agent benchmarks
python six_questions.py                # six questions for every result
python copy_the_idea.py                # copy the measurement idea, not the score
python patch_passed_failed.py          # passed in the repository, failed in the company
python run_manifest.py                 # record the shape of the system, not just the model name
python exercise/check_my_benchmark.py  # the exercise from the post
python -m unittest -v test_benchmarks
```

### What benchmarks measure (`what_benchmarks_measure.py`)

The eight benchmarks from the post (MMLU, GPQA, HumanEval, SWE-bench, Chatbot Arena, HELM, TruthfulQA, ARC-AGI) are each described by unit of work, oracle, metric and blind spot (`data/benchmarks.json`). Then three of their metrics are computed on simulated results:

- **Multiple choice:** 85.1% overall, but professional law gets 58% and computer security 64%.
- **pass@k:** pass@1 is 70.0% and pass@10 is 97.5% for the same model on the same problems.
- **Pairwise preference:** 2,400 votes, and the longer answer wins 71% of them. The top-rated model is correct 75% of the time, the lowest-rated one 90%.

### Benchmarks go stale (`benchmarks_rot.py`)

- **Contamination.** 59 of 150 public questions appear verbatim in scraped training data. On those, the model gets 97% on the original wording, 75% on a paraphrase and 68% on fresh questions of the same kind. That 22-point gap is knowledge of the exam, not skill.
- **A brittle agent benchmark.** 60 browser tasks are graded by the one expected click path or by the final state: 65% vs 90% success. 19 runs completed the task but fail the path check (a cookie dialog, the settings search), and 4 pass it although the page had changed and nothing happened.

### Six questions (`six_questions.py`)

The script asks the six questions of all eight benchmarks for one of your products. For the support chatbot, 7 benchmarks are decoration and 1 is a weak signal, useful for shortlisting models but not for shipping one. Also try `--product coding_agent` and `--product search`.

### Copy the idea, not the score (`copy_the_idea.py`)

The script lists the pattern each public evaluation teaches, then builds three product evaluations:

- **Search.** Ranker B has more "relevant" results in its top 10, but puts the perfect answer at rank 9, shows stale listings and a duplicate. NDCG is 0.73 vs 1.00 and MRR is 0.11 vs 1.00.
- **Support chatbot.** People prefer `model-friendly` in 64% of pairwise comparisons, but it has 18 policy violations and fails the release gate.
- **Home robot and medical image app.** 100% on the safety quiz, but 85% of real trials go without knocking anything over. A medical app needs image quality checks, an uncertainty signal and a safe fallback.

### Passed in the repository, failed in the company (`patch_passed_failed.py`)

The certificate migration in the payment service, simulated. Both 12-line patches pass the tests: a perfect benchmark score. Then the product evaluation runs:

- On Friday 00:01 the old certificate expires. With patch A the handshake fails, because the test environment's certificate never expires.
- During the staged rollout, a timed-out token exchange is retried. Patch A authorizes the payment twice.
- The work around the patch is graded too: dependencies found, access requested, `PAYMENTS.md` respected, evidence for the reviewer. Patch A does 1 of 4, patch B 4 of 4.

### The run manifest (`run_manifest.py`)

Two runs of "the same model" score 84% and 79%. The manifest shows that the index, the reranker and the cache all changed, and only the index change was documented. It writes `output/run_manifest.json` with every field from the post: the model, the prompt and policy pack, context building, retrieval and the index version, the output schema, tools with their permissions, the cache and limits, the judge, the rubric and the release gate.

### The exercise from the post

> Take one public result that recently came up when your team discussed choosing a model, and answer the six questions from this post. Then write in one sentence which case from your product should replace this benchmark in your evaluation.

1. Run `python exercise/check_my_benchmark.py`. The example is "Model Y: 72% on SWE-bench Verified" for a coding agent on a payment service. It has 3 gaps and 2 unknowns (contamination, and whether the result would change the decision), plus a concrete replacement case.
2. Open `exercise/my_benchmark_result.json` and describe your own result. Answer the six questions, use `matches_product` (true/false) for questions 1–4, leave unknown answers as `null`, and write the `replacement_case` in one sentence.

### Files

| File | Role |
|---|---|
| `evals.py` | pass@k, Bradley-Terry, NDCG, MRR, a contamination check |
| `generate_data.py`, `data/` | Simulated results and descriptions used by every script (always the same content) |
| `what_benchmarks_measure.py` | Eight benchmarks; accuracy by subject, pass@k, pairwise ranking |
| `benchmarks_rot.py` | Contamination; path-based vs outcome-based grading |
| `six_questions.py` | The six questions, asked for each benchmark and product |
| `copy_the_idea.py` | Measurement patterns; search, support and robot evaluations |
| `patch_passed_failed.py` | The certificate migration, simulated |
| `run_manifest.py` | The system's shape, a diff between runs, `output/run_manifest.json` |
| `exercise/` | The exercise: your benchmark result and the checker |
| `test_benchmarks.py` | Unit tests |

---

## Polski

Przykład do wpisu [**„Wysoki wynik w benchmarku to jeszcze nie produkt”**](https://paprico.substack.com/p/wysoki-wynik-w-benchmarku-to-jeszcze) (po angielsku, z wersją po polsku).

Nowy model, nowy rekord w rankingu, nowa fala zachwytów i za każdym razem to samo pytanie: co z tego wynika dla mojego produktu? Ten folder pokazuje:

- co naprawdę mierzą popularne benchmarki;
- dlaczego się starzeją;
- sześć pytań do każdego wyniku;
- jak przenieść do własnej ewaluacji ideę pomiaru, a nie wynik;
- co zapisywać przy każdym przebiegu.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+). Wszystko w tym folderze (pliki, kod, komunikaty) jest po angielsku. Modele i wyniki benchmarków są symulowane. Metryki (dokładność, pass@k, ranking Bradleya-Terry'ego, NDCG, MRR) są rozpisane w `evals.py`.

### Uruchom

```bash
python what_benchmarks_measure.py      # osiem benchmarków, osiem różnych pytań
python benchmarks_rot.py               # zanieczyszczenie i kruche benchmarki agentów
python six_questions.py                # sześć pytań do każdego wyniku
python copy_the_idea.py                # kopiuj ideę pomiaru, nie wynik
python patch_passed_failed.py          # przeszło w repozytorium, padło w firmie
python run_manifest.py                 # zapisuj kształt systemu, nie tylko nazwę modelu
python exercise/check_my_benchmark.py  # ćwiczenie z artykułu
python -m unittest -v test_benchmarks
```

### Co mierzą benchmarki (`what_benchmarks_measure.py`)

Osiem benchmarków z artykułu (MMLU, GPQA, HumanEval, SWE-bench, Chatbot Arena, HELM, TruthfulQA, ARC-AGI) jest opisanych przez jednostkę pracy, wyrocznię, metrykę i to, czego nie widzą (`data/benchmarks.json`). Potem trzy z ich metryk są liczone na symulowanych wynikach:

- **Pytania wielokrotnego wyboru:** 85,1% ogółem, ale prawo zawodowe ma 58%, a bezpieczeństwo IT 64%.
- **pass@k:** pass@1 wynosi 70,0%, a pass@10 97,5% dla tego samego modelu na tych samych zadaniach.
- **Preferencje parami:** 2400 głosów, w których dłuższa odpowiedź wygrywa w 71% przypadków. Model z najwyższym rankingiem ma rację w 75% przypadków, a ten z najniższym w 90%.

### Benchmarki gniją (`benchmarks_rot.py`)

- **Zanieczyszczenie.** 59 ze 150 publicznych pytań występuje dosłownie w danych zebranych z sieci do treningu. Na nich model ma 97% przy oryginalnym brzmieniu, 75% przy parafrazie i 68% na świeżych pytaniach tego samego rodzaju. Ta różnica 22 punktów to znajomość egzaminu, a nie umiejętność.
- **Kruchy benchmark agentów.** 60 zadań w przeglądarce jest ocenianych według jednej oczekiwanej ścieżki kliknięć albo według stanu końcowego: 65% kontra 90% sukcesów. 19 przebiegów wykonało zadanie, a mimo to nie przechodzi kontroli ścieżki (okno cookies, wyszukiwarka ustawień). 4 ją przechodzą, choć strona się zmieniła i nic się nie stało.

### Sześć pytań (`six_questions.py`)

Skrypt zadaje sześć pytań wszystkim ośmiu benchmarkom dla jednego z twoich produktów. Dla chatbota wsparcia 7 benchmarków to dekoracja, a 1 to słaby sygnał, przydatny do zawężenia listy modeli, ale nie do wydania. Spróbuj też `--product coding_agent` i `--product search`.

### Kopiuj ideę, nie wynik (`copy_the_idea.py`)

Skrypt wypisuje wzorce, których uczy każda publiczna ewaluacja, a potem buduje trzy ewaluacje produktowe:

- **Wyszukiwarka.** Ranker B ma w top 10 więcej „trafnych” wyników, ale idealną odpowiedź stawia na 9. miejscu, pokazuje przestarzałe oferty i duplikat. NDCG wynosi 0,73 wobec 1,00, a MRR 0,11 wobec 1,00.
- **Chatbot wsparcia.** Ludzie wolą `model-friendly` w 64% porównań parami, ale ma on 18 naruszeń polityki i nie przechodzi bramki wydania.
- **Robot domowy i aplikacja medyczna.** 100% w quizie bezpieczeństwa, ale tylko 85% prawdziwych prób bez strącenia czegokolwiek. Aplikacja medyczna potrzebuje kontroli jakości obrazu, sygnału niepewności i bezpiecznej ścieżki awaryjnej.

### Przeszło w repozytorium, padło w firmie (`patch_passed_failed.py`)

Migracja biblioteki certyfikatów w serwisie płatności, w symulacji. Obie 12-liniowe poprawki przechodzą testy, co daje idealny wynik w benchmarku. Potem rusza ewaluacja produktu:

- W piątek o 00:01 wygasa stary certyfikat. Przy poprawce A handshake pada, bo certyfikat w środowisku testowym nigdy nie wygasa.
- Podczas wdrożenia stopniowego wymiana tokenu, która przekroczyła czas, jest ponawiana. Poprawka A autoryzuje płatność dwa razy.
- Ocenia się też pracę wokół poprawki: znalezione zależności, prośba o dostęp, uszanowanie `PAYMENTS.md`, dowody dla recenzenta. Poprawka A spełnia 1 z 4 punktów, poprawka B 4 z 4.

### Manifest przebiegu (`run_manifest.py`)

Dwa przebiegi „tego samego modelu” mają wyniki 84% i 79%. Manifest pokazuje, że zmieniły się indeks, reranker i cache, a udokumentowano tylko zmianę indeksu. Skrypt zapisuje `output/run_manifest.json` ze wszystkimi polami z artykułu: model, prompt i pakiet polityk, budowanie kontekstu, wyszukiwanie i wersja indeksu, schemat wyjścia, narzędzia z uprawnieniami, cache i limity, sędzia, rubryka i bramka wydania.

### Ćwiczenie z artykułu

> Weź jeden publiczny wynik, który ostatnio pojawił się w rozmowie o wyborze modelu w twoim zespole, i odpowiedz na sześć pytań z tego wpisu. Potem zapisz jednym zdaniem, jaki przypadek z twojego produktu powinien zastąpić ten benchmark w ewaluacji.

1. Uruchom `python exercise/check_my_benchmark.py`. Przykład to „Model Y: 72% w SWE-bench Verified” dla agenta kodującego w serwisie płatności. Ma 3 luki i 2 niewiadome (zanieczyszczenie oraz to, czy wynik zmieniłby decyzję), a także konkretny przypadek zastępczy.
2. Otwórz `exercise/my_benchmark_result.json` i opisz swój wynik. Odpowiedz na sześć pytań, przy pytaniach 1–4 zaznacz `matches_product` (true/false), nieznane odpowiedzi zostaw jako `null` i jednym zdaniem napisz `replacement_case`.

### Pliki

| Plik | Rola |
|---|---|
| `evals.py` | pass@k, Bradley-Terry, NDCG, MRR, kontrola zanieczyszczenia |
| `generate_data.py`, `data/` | Symulowane wyniki i opisy używane przez wszystkie skrypty (zawsze ta sama treść) |
| `what_benchmarks_measure.py` | Osiem benchmarków; dokładność według dziedzin, pass@k, ranking parami |
| `benchmarks_rot.py` | Zanieczyszczenie; ocena według ścieżki a według wyniku |
| `six_questions.py` | Sześć pytań zadanych każdemu benchmarkowi dla wybranego produktu |
| `copy_the_idea.py` | Wzorce pomiaru; ewaluacje wyszukiwarki, wsparcia i robota |
| `patch_passed_failed.py` | Symulacja migracji certyfikatów |
| `run_manifest.py` | Kształt systemu, różnice między przebiegami, `output/run_manifest.json` |
| `exercise/` | Ćwiczenie: Twój wynik z benchmarku i skrypt sprawdzający |
| `test_benchmarks.py` | Testy jednostkowe |
