# 02 — Properties, Not Sentences

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**One Run Is Not Proof (Part 2): Test Properties, Not Sentences**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-202).

If the model answers in different words every time, a test can’t compare sentences. It should check the **properties** of the answer: what must be in it, what isn’t allowed, which limits are hard, and how you score the rest.

Runs without an API key and without installing any packages (Python 3.9+). The code, comments and console output are in Polish; the ideas carry over one to one.

### Run it

```bash
python zwroty.py                     # exact assertion vs evaluation criteria
python -m unittest -v test_zwroty    # the same as unit tests
python sedzia.py                     # two automated judges vs the rubric author's scores
python porownaj_oceny.py --sedziowie # ready-made example: two people + the judges
python bramka.py                     # release gate: the distribution, not just the mean
python ocen_na_slepo.py              # exercise: score the answers yourself (interactive)
python -m unittest -v test_regresje  # regression tests
```

### What each script shows

**`zwroty.py` and `test_zwroty.py`.** The question: *“I bought shoes 45 days ago, can I return them?”* A string comparison rejects two correct answers just because they used different words. The criteria (`rubryka.py`) let them through and reject the bad answers with a readable reason, for example *“suggested a non-existent policy exception”*. Blockers are hard limits. A missing “next step” is only a note and doesn’t stop the release.

**`sedzia.py`.** The example of a turkey thawed in the garage. The rule-based judge scores against an explicit rubric and agrees with the author. The “naive” judge rewards length and politeness, so it gives 9/10 to fluent-sounding nonsense. The lesson from the post: a judge is a measuring instrument, not the truth. You calibrate it against people first.

**`bramka.py`.** Systems scoring `8,8,8,8` and `10,10,4,8` have the same mean of 8.0. A system scoring `99 × 9 + one 0` has a mean of 8.91 and is dangerous. The release gate from the post (mean ≥ 8, ≥ 95% of scores ≥ 7, nothing below 4, zero critical failures) tells these cases apart. Your own data: `python bramka.py wyniki.json`.

### The exercise from the post

> Take one question your chatbot answers and write four sample answers for it: a 10, a 7, a 4 and a 0. Show them to someone on your team without the scores and ask them to rate them. If your scores diverge, you’ve just found the spot where your rubric needs sharpening.

1. **Try the example first.** Run `python ocen_na_slepo.py`. You’ll see 7 answers about the turkey in random order, without scores. Your ratings are saved to `oceny/<name>.json`.
2. **Compare.** `python porownaj_oceny.py oceny/your_name.json oceny/przyklad_bartek.json --sedziowie` shows gaps of 2 points or more and questions to discuss as a team.
3. **Now on your own product.** Fill in `moje_odpowiedzi.json`: the question and four answers for 10, 7, 4 and 0. Then each person runs:
   ```bash
   python ocen_na_slepo.py moje_odpowiedzi.json
   ```
   and finally:
   ```bash
   python porownaj_oceny.py oceny/you.json oceny/teammate.json
   ```

### Files

| File | Role |
|---|---|
| `rubryka.py` | “Requires / forbids” criteria, blockers and soft criteria |
| `zwroty.py`, `test_zwroty.py` | The shoe return example: script and `unittest` tests |
| `indyk.json` | The question, the 0–10 scale, four anchors (10/7/4/0) and three answers for blind scoring |
| `sedzia.py` | A rubric-based judge and a naive judge (instead of an LLM judge, so it runs offline) |
| `ocen_na_slepo.py`, `porownaj_oceny.py` | The exercise: blind scoring and spotting disagreements |
| `oceny/przyklad_*.json` | Ready-made ratings from two people to compare |
| `moje_odpowiedzi.json` | Template for the exercise on your own chatbot |
| `bramka.py` | A release gate based on the score distribution |
| `test_regresje.py` | Regression tests |

### Plugging in a real LLM judge (optional)

Write a function with the same signature as `sedzia_rubryka(tekst) -> (score, reasoning, critical)` that sends the rubric and anchors from `indyk.json` to a model, and add it as a column in `porownaj_oceny.py`. The comparison with people keeps working unchanged.

---

## Polski

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 2). Testuj właściwości, nie zdania**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-202).

Skoro model za każdym razem odpowiada innymi słowami, test nie może porównywać zdań. Powinien sprawdzać **właściwości** odpowiedzi: co musi się w niej znaleźć, czego nie wolno, które granice są twarde i jak oceniasz resztę.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

### Uruchom

```bash
python zwroty.py                     # dokładna asercja vs kryteria oceny
python -m unittest -v test_zwroty    # to samo jako testy jednostkowe
python sedzia.py                     # dwóch automatycznych sędziów vs ocena autora rubryki
python porownaj_oceny.py --sedziowie # gotowy przykład: dwie osoby + sędziowie
python bramka.py                     # bramka wydania: rozkład, nie tylko średnia
python ocen_na_slepo.py              # ćwiczenie: oceń odpowiedzi sam (interaktywnie)
python -m unittest -v test_regresje  # testy regresyjne
```

### Co pokazuje każdy skrypt

**`zwroty.py` i `test_zwroty.py`.** Pytanie: *„Kupiłem buty 45 dni temu, czy mogę je zwrócić?”* Porównanie ciągów znaków odrzuca dwie poprawne odpowiedzi tylko dlatego, że użyły innych słów. Kryteria (`rubryka.py`) przepuszczają je i odrzucają złe odpowiedzi z czytelnym powodem, na przykład *„zasugerowała nieistniejący wyjątek od polityki”*. Blokery to twarde granice. Brak „następnego kroku” to tylko uwaga i nie zatrzymuje wydania.

**`sedzia.py`.** Przykład z indykiem rozmrażanym w garażu. Sędzia regułowy punktuje według jawnej rubryki i zgadza się z autorem. Sędzia „naiwny” nagradza długość i uprzejmość, więc daje 9/10 płynnie brzmiącej bzdurze. Wniosek z artykułu: sędzia to przyrząd pomiarowy, a nie prawda. Najpierw kalibrujesz go na ludziach.

**`bramka.py`.** Systemy z ocenami `8,8,8,8` i `10,10,4,8` mają tę samą średnią 8,0. System z wynikiem `99 × 9 + jedno 0` ma średnią 8,91, a jest niebezpieczny. Bramka z artykułu (średnia ≥ 8, ≥ 95% ocen ≥ 7, nic poniżej 4, zero błędów krytycznych) rozróżnia te przypadki. Własne dane: `python bramka.py wyniki.json`.

### Ćwiczenie z artykułu

> Weź jedno pytanie, na które odpowiada twój chatbot, i napisz dla niego cztery przykładowe odpowiedzi: na 10, 7, 4 i 0. Pokaż je komuś z zespołu bez ocen i poproś, żeby je ocenił. Jeśli wasze oceny się rozjadą, właśnie znalazłeś miejsce, w którym rubryka wymaga doprecyzowania.

1. **Najpierw spróbuj na przykładzie.** Uruchom `python ocen_na_slepo.py`. Zobaczysz 7 odpowiedzi o indyku w losowej kolejności, bez ocen. Twoje oceny trafią do `oceny/<imie>.json`.
2. **Porównaj.** `python porownaj_oceny.py oceny/twoje_imie.json oceny/przyklad_bartek.json --sedziowie` pokaże rozjazdy o 2 lub więcej punktów i pytania do omówienia w zespole.
3. **Teraz na swoim produkcie.** Wypełnij `moje_odpowiedzi.json`: pytanie i cztery odpowiedzi na 10, 7, 4 i 0. Potem każda osoba robi:
   ```bash
   python ocen_na_slepo.py moje_odpowiedzi.json
   ```
   a na koniec:
   ```bash
   python porownaj_oceny.py oceny/ty.json oceny/kolega.json
   ```

### Pliki

| Plik | Rola |
|---|---|
| `rubryka.py` | Kryteria „wymaga / zakazuje”, blokery i kryteria miękkie |
| `zwroty.py`, `test_zwroty.py` | Przykład zwrotu butów: skrypt i testy `unittest` |
| `indyk.json` | Pytanie, skala 0–10, cztery kotwice (10/7/4/0) i trzy odpowiedzi do oceny na ślepo |
| `sedzia.py` | Sędzia według rubryki i sędzia naiwny (zamiast sędziego LLM, żeby działało offline) |
| `ocen_na_slepo.py`, `porownaj_oceny.py` | Ćwiczenie: ocena bez podpowiedzi i wykrywanie rozjazdów |
| `oceny/przyklad_*.json` | Gotowe oceny dwóch osób do porównania |
| `moje_odpowiedzi.json` | Szablon do ćwiczenia na własnym chatbocie |
| `bramka.py` | Bramka wydania oparta na rozkładzie ocen |
| `test_regresje.py` | Testy regresyjne |

### Podpięcie prawdziwego sędziego LLM (opcjonalnie)

Napisz funkcję o tej samej sygnaturze co `sedzia_rubryka(tekst) -> (ocena, uzasadnienie, krytyczny)`, która wysyła rubrykę i kotwice z `indyk.json` do modelu, i dodaj ją jako kolumnę w `porownaj_oceny.py`. Porównanie z ludźmi działa bez zmian.
