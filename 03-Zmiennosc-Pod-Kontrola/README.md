# 03 — Zmienność pod kontrolą

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 3). Zmienność pod kontrolą**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz-b44).

Które różnice między uruchomieniami są w porządku, a które blokują wydanie? Kiedy warto przykręcić losowość i ile to kosztuje?

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

## Model z prawdziwymi pokrętłami

`model_tokenowy.py` to miniaturowy model językowy. Odpowiada na pytanie *„Kiedy dotrze moje zamówienie i do kiedy mogę je anulować?”*. Polityka sklepu: anulowanie do 24 godzin przed wysyłką i obowiązkowe ostrzeżenie o produktach chłodzonych.

W każdym miejscu odpowiedzi model wybiera fragment tekstu na podstawie **logitów**. Pokrętła działają w tej samej kolejności co w prawdziwych modelach: logit bias → temperatura → softmax → top-k → top-p. Złe fragmenty („48 godzin”, „gwarantujemy”, pominięte ostrzeżenie) mają niskie logity. Są rzadkie, ale możliwe. Dlatego jedno uruchomienie ich zwykle nie pokazuje.

## Uruchom

```bash
python pokretla.py           # jak temperatura, top-p, top-k, logit bias i seed zmieniają rozkład
python piec_uruchomien.py    # ĆWICZENIE: pięć uruchomień i trzy listy
python dwa_przebiegi.py      # przebieg stabilny vs produkcyjny, wariancja w podziale na wymiary
```

## Ćwiczenie z artykułu

> Uruchom te same dane wejściowe pięć razy. Potem zapisz trzy listy: różnice nieszkodliwe; różnice, które zmieniają to, czego doświadcza użytkownik; ustawienia, które mogłyby zmniejszyć wariancję.

`piec_uruchomien.py` robi to automatycznie i zapisuje raport w Markdown do `raporty/`:

- **Lista 1:** różne sformułowania, akapit zamiast listy, inne zakończenie. To wariancja akceptowalna.
- **Lista 2:** zły limit anulowania, obietnica „gwarantujemy”, pominięte ostrzeżenie. Do tego prawdopodobieństwo, że 5 uruchomień **niczego nie pokaże**. Przy ustawieniach produkcyjnych wynosi ono około 50%.
- **Lista 3:** dla każdego problematycznego miejsca policzony efekt pokręteł, na przykład „top_p 0.9: ryzyko 8,0% → 0,0%”, oraz rozwiązanie strukturalne, które zwykle jest lepsze: fakt z kodu, a nie z modelu.

Spróbuj:

```bash
python piec_uruchomien.py --seed 3                     # seria, w której wychodzi problem
python piec_uruchomien.py --n 50                       # więcej uruchomień = więcej widać
python piec_uruchomien.py --top-p 0.9                  # czy pokrętło pomogło?
python piec_uruchomien.py --bias 48=-100 --bias 12=-100
python piec_uruchomien.py --temperatura 0              # stabilnie, ale bez różnorodności
```

Każda seria wypisuje polecenie, którym można ją dokładnie odtworzyć (`--seed`).

> W tym uproszczonym modelu `top_p 0.9` usuwa złe fragmenty całkowicie. W prawdziwym LLM pokrętła zmniejszają ryzyko, ale go nie zerują. Dlatego potrzebujesz testów na większej próbie, a nie tylko zmiany ustawień.

## Dwa przebiegi zamiast jednego

`dwa_przebiegi.py` uruchamia ten sam zestaw 300 zapytań dwa razy:

- **stabilny:** temperatura 0, stały seed, zamrożona migawka danych, stuby narzędzi,
- **produkcyjny:** temperatura 0,9, dane na żywo (w trakcie router przesuwa dostawę na sobotę), opóźnienia z ponowieniami.

Wynik to tabela wariancji **osobno dla każdego wymiaru**: sformułowanie, struktura, fakty, obietnice, ostrzeżenia, zmiana danych i opóźnienie (p50/p95/p99). Odsetki mają 95% przedział ufności. Widać w niej, że:

- przebieg stabilny jest czysty, więc awarie w produkcji biorą się z próbkowania, a nie z przypadku testowego,
- przesunięcie dostawy na sobotę to zasadna zmiana świata, a nie błąd modelu. Widać to tylko dzięki migawce danych w kopercie,
- mediana opóźnienia wygląda dobrze, ale p99 już nie.

## Pełna koperta

`koperta.py` zapisuje przy każdym przebiegu: model, prompt i jego wersję, definicje narzędzi, migawkę danych, parametry dekodowania, seed, schemat, sędzię, znacznik czasu i infrastrukturę. `porownaj_koperty()` mówi, czy porównujesz ten sam test, czy już coś innego.

## Pliki

| Plik | Rola |
|---|---|
| `model_tokenowy.py` | Mini-model z logitami i próbkowaniem (temperatura, top-p, top-k, seed, logit bias) |
| `pokretla.py` | Ściąga z pokręteł policzona na żywo |
| `piec_uruchomien.py` | Ćwiczenie: pięć uruchomień i trzy listy, raport w Markdown |
| `dwa_przebiegi.py` | Przebieg stabilny i produkcyjny, wariancja w podziale na wymiary, przedziały ufności |
| `koperta.py` | Pełna koperta ewaluacji i porównywanie kopert |
| `raporty/` | Tworzone przez skrypty |
