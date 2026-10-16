# 02 — Testuj właściwości, nie zdania

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 2). Testuj właściwości, nie zdania**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-202).

Skoro model za każdym razem odpowiada innymi słowami, test nie może porównywać zdań. Powinien sprawdzać **właściwości** odpowiedzi: co musi się w niej znaleźć, czego nie wolno, które granice są twarde i jak oceniasz resztę.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

## Uruchom

```bash
python zwroty.py                     # dokładna asercja vs kryteria oceny
python -m unittest -v test_zwroty    # to samo jako testy jednostkowe
python sedzia.py                     # dwóch automatycznych sędziów vs ocena autora rubryki
python porownaj_oceny.py --sedziowie # gotowy przykład: dwie osoby + sędziowie
python bramka.py                     # bramka wydania: rozkład, nie tylko średnia
python ocen_na_slepo.py              # ćwiczenie: oceń odpowiedzi sam (interaktywnie)
```

## Co pokazuje każdy skrypt

**`zwroty.py` i `test_zwroty.py`.** Pytanie: *„Kupiłem buty 45 dni temu, czy mogę je zwrócić?”* Porównanie ciągów znaków odrzuca dwie poprawne odpowiedzi tylko dlatego, że użyły innych słów. Kryteria (`rubryka.py`) przepuszczają je i odrzucają złe odpowiedzi z czytelnym powodem, na przykład *„zasugerowała nieistniejący wyjątek od polityki”*. Blokery to twarde granice. Brak „następnego kroku” to tylko uwaga i nie zatrzymuje wydania.

**`sedzia.py`.** Przykład z indykiem rozmrażanym w garażu. Sędzia regułowy punktuje według jawnej rubryki i zgadza się z autorem. Sędzia „naiwny” nagradza długość i uprzejmość, więc daje 9/10 płynnie brzmiącej bzdurze. Wniosek z artykułu: sędzia to przyrząd pomiarowy, a nie prawda. Najpierw kalibrujesz go na ludziach.

**`bramka.py`.** Systemy z ocenami `8,8,8,8` i `10,10,4,8` mają tę samą średnią 8,0. System z wynikiem `99 × 9 + jedno 0` ma średnią 8,91, a jest niebezpieczny. Bramka z artykułu (średnia ≥ 8, ≥ 95% ocen ≥ 7, nic poniżej 4, zero błędów krytycznych) rozróżnia te przypadki. Własne dane: `python bramka.py wyniki.json`.

## Ćwiczenie z artykułu

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

## Pliki

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

## Podpięcie prawdziwego sędziego LLM (opcjonalnie)

Napisz funkcję o tej samej sygnaturze co `sedzia_rubryka(tekst) -> (ocena, uzasadnienie, krytyczny)`, która wysyła rubrykę i kotwice z `indyk.json` do modelu, i dodaj ją jako kolumnę w `porownaj_oceny.py`. Porównanie z ludźmi działa bez zmian.
