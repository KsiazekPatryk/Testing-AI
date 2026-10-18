# 02 — Properties, Not Sentences

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**One Run Is Not Proof (Part 2): Test Properties, Not Sentences**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-202).

If the model answers in different words every time, a test can’t compare sentences. It should check the **properties** of the answer: what must be in it, what isn’t allowed, which limits are hard, and how you score the rest.

Runs without an API key and without installing any packages (Python 3.9+). The code, comments and console output are in Polish; the ideas carry over one to one.

### Run it

```bash
python shoe_returns.py                    # exact assertion vs evaluation criteria
python -m unittest -v test_shoe_returns   # the same as unit tests
python judge.py                           # two automated judges vs the rubric author's scores
python compare_ratings.py --sedziowie     # ready-made example: two people + the judges
python release_gate.py                    # release gate: the distribution, not just the mean
python blind_rating.py                    # exercise: score the answers yourself (interactive)
python -m unittest -v test_regressions    # regression tests
```

### What each script shows

**`shoe_returns.py` and `test_shoe_returns.py`.** The question: *“I bought shoes 45 days ago, can I return them?”* A string comparison rejects two correct answers just because they used different words. The criteria (`rubric.py`) let them through and reject the bad answers with a readable reason, for example *“suggested a non-existent policy exception”*. Blockers are hard limits. A missing “next step” is only a note and doesn’t stop the release.

**`judge.py`.** The example of a turkey thawed in the garage. The rule-based judge scores against an explicit rubric and agrees with the author. The “naive” judge rewards length and politeness, so it gives 9/10 to fluent-sounding nonsense. The lesson from the post: a judge is a measuring instrument, not the truth. You calibrate it against people first.

**`release_gate.py`.** Systems scoring `8,8,8,8` and `10,10,4,8` have the same mean of 8.0. A system scoring `99 × 9 + one 0` has a mean of 8.91 and is dangerous. The release gate from the post (mean ≥ 8, ≥ 95% of scores ≥ 7, nothing below 4, zero critical failures) tells these cases apart. Your own data: `python release_gate.py wyniki.json`.

### The exercise from the post

> Take one question your chatbot answers and write four sample answers for it: a 10, a 7, a 4 and a 0. Show them to someone on your team without the scores and ask them to rate them. If your scores diverge, you’ve just found the spot where your rubric needs sharpening.

1. **Try the example first.** Run `python blind_rating.py`. You’ll see 7 answers about the turkey in random order, without scores. Your ratings are saved to `ratings/<name>.json`.
2. **Compare.** `python compare_ratings.py ratings/your_name.json ratings/example_bartek.json --sedziowie` shows gaps of 2 points or more and questions to discuss as a team.
3. **Now on your own product.** Fill in `my_answers.json`: the question and four answers for 10, 7, 4 and 0. Then each person runs:
   ```bash
   python blind_rating.py my_answers.json
   ```
   and finally:
   ```bash
   python compare_ratings.py ratings/you.json ratings/teammate.json
   ```

### Files

| File | Role |
|---|---|
| `rubric.py` | “Requires / forbids” criteria, blockers and soft criteria |
| `shoe_returns.py`, `test_shoe_returns.py` | The shoe return example: script and `unittest` tests |
| `turkey.json` | The question, the 0–10 scale, four anchors (10/7/4/0) and three answers for blind scoring |
| `judge.py` | A rubric-based judge and a naive judge (instead of an LLM judge, so it runs offline) |
| `blind_rating.py`, `compare_ratings.py` | The exercise: blind scoring and spotting disagreements |
| `ratings/example_*.json` | Ready-made ratings from two people to compare |
| `my_answers.json` | Template for the exercise on your own chatbot |
| `release_gate.py` | A release gate based on the score distribution |
| `test_regressions.py` | Regression tests |

### Plugging in a real LLM judge (optional)

Write a function with the same signature as `sedzia_rubryka(tekst) -> (score, reasoning, critical)` that sends the rubric and anchors from `turkey.json` to a model, and add it as a column in `compare_ratings.py`. The comparison with people keeps working unchanged.

---

## Polski

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 2). Testuj właściwości, nie zdania**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-202).

Skoro model za każdym razem odpowiada innymi słowami, test nie może porównywać zdań. Powinien sprawdzać **właściwości** odpowiedzi: co musi się w niej znaleźć, czego nie wolno, które granice są twarde i jak oceniasz resztę.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

### Uruchom

```bash
python shoe_returns.py                    # dokładna asercja vs kryteria oceny
python -m unittest -v test_shoe_returns   # to samo jako testy jednostkowe
python judge.py                           # dwóch automatycznych sędziów vs ocena autora rubryki
python compare_ratings.py --sedziowie     # gotowy przykład: dwie osoby + sędziowie
python release_gate.py                    # bramka wydania: rozkład, nie tylko średnia
python blind_rating.py                    # ćwiczenie: oceń odpowiedzi sam (interaktywnie)
python -m unittest -v test_regressions    # testy regresyjne
```

### Co pokazuje każdy skrypt

**`shoe_returns.py` i `test_shoe_returns.py`.** Pytanie: *„Kupiłem buty 45 dni temu, czy mogę je zwrócić?”* Porównanie ciągów znaków odrzuca dwie poprawne odpowiedzi tylko dlatego, że użyły innych słów. Kryteria (`rubric.py`) przepuszczają je i odrzucają złe odpowiedzi z czytelnym powodem, na przykład *„zasugerowała nieistniejący wyjątek od polityki”*. Blokery to twarde granice. Brak „następnego kroku” to tylko uwaga i nie zatrzymuje wydania.

**`judge.py`.** Przykład z indykiem rozmrażanym w garażu. Sędzia regułowy punktuje według jawnej rubryki i zgadza się z autorem. Sędzia „naiwny” nagradza długość i uprzejmość, więc daje 9/10 płynnie brzmiącej bzdurze. Wniosek z artykułu: sędzia to przyrząd pomiarowy, a nie prawda. Najpierw kalibrujesz go na ludziach.

**`release_gate.py`.** Systemy z ocenami `8,8,8,8` i `10,10,4,8` mają tę samą średnią 8,0. System z wynikiem `99 × 9 + jedno 0` ma średnią 8,91, a jest niebezpieczny. Bramka z artykułu (średnia ≥ 8, ≥ 95% ocen ≥ 7, nic poniżej 4, zero błędów krytycznych) rozróżnia te przypadki. Własne dane: `python release_gate.py wyniki.json`.

### Ćwiczenie z artykułu

> Weź jedno pytanie, na które odpowiada twój chatbot, i napisz dla niego cztery przykładowe odpowiedzi: na 10, 7, 4 i 0. Pokaż je komuś z zespołu bez ocen i poproś, żeby je ocenił. Jeśli wasze oceny się rozjadą, właśnie znalazłeś miejsce, w którym rubryka wymaga doprecyzowania.

1. **Najpierw spróbuj na przykładzie.** Uruchom `python blind_rating.py`. Zobaczysz 7 odpowiedzi o indyku w losowej kolejności, bez ocen. Twoje oceny trafią do `ratings/<imie>.json`.
2. **Porównaj.** `python compare_ratings.py ratings/twoje_imie.json ratings/example_bartek.json --sedziowie` pokaże rozjazdy o 2 lub więcej punktów i pytania do omówienia w zespole.
3. **Teraz na swoim produkcie.** Wypełnij `my_answers.json`: pytanie i cztery odpowiedzi na 10, 7, 4 i 0. Potem każda osoba robi:
   ```bash
   python blind_rating.py my_answers.json
   ```
   a na koniec:
   ```bash
   python compare_ratings.py ratings/ty.json ratings/kolega.json
   ```

### Pliki

| Plik | Rola |
|---|---|
| `rubric.py` | Kryteria „wymaga / zakazuje”, blokery i kryteria miękkie |
| `shoe_returns.py`, `test_shoe_returns.py` | Przykład zwrotu butów: skrypt i testy `unittest` |
| `turkey.json` | Pytanie, skala 0–10, cztery kotwice (10/7/4/0) i trzy odpowiedzi do oceny na ślepo |
| `judge.py` | Sędzia według rubryki i sędzia naiwny (zamiast sędziego LLM, żeby działało offline) |
| `blind_rating.py`, `compare_ratings.py` | Ćwiczenie: ocena bez podpowiedzi i wykrywanie rozjazdów |
| `ratings/example_*.json` | Gotowe oceny dwóch osób do porównania |
| `my_answers.json` | Szablon do ćwiczenia na własnym chatbocie |
| `release_gate.py` | Bramka wydania oparta na rozkładzie ocen |
| `test_regressions.py` | Testy regresyjne |

### Podpięcie prawdziwego sędziego LLM (opcjonalnie)

Napisz funkcję o tej samej sygnaturze co `sedzia_rubryka(tekst) -> (ocena, uzasadnienie, krytyczny)`, która wysyła rubrykę i kotwice z `turkey.json` do modelu, i dodaj ją jako kolumnę w `compare_ratings.py`. Porównanie z ludźmi działa bez zmian.
