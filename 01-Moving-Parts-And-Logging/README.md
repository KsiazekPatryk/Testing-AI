# 01 — Ruchome elementy i logowanie

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 1). Skąd bierze się nieprzewidywalność AI**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz).

> „Czy potrafimy wyjaśnić, który ruchomy element zmienił odpowiedź?”

Klient pyta chatbota sklepu: *„Czy zdążycie dowieźć moje zakupy na piknik, zanim zacznie się burza?”* Odpowiedź zmienia się z uczciwych powodów: zmieniła się prognoza, ktoś kupił ostatnie lody, kierowca anulował kurs albo weszła nowa polityka dla produktów chłodzonych. Czasem jednak zmienia się, bo coś się zepsuło, a bot nadal brzmi pewnie.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

## Uruchom

```bash
python demo.py                         # cały przykład krok po kroku
python cwiczenie/sprawdz_pokrycie.py   # ćwiczenie z artykułu
python wyjasnij.py logi/rozmowy.jsonl 1 3   # porównaj dowolne dwa wpisy z logu
```

## Co pokazuje `demo.py`

1. **Logowanie samej odpowiedzi.** Cztery różne odpowiedzi i brak wiedzy, dlaczego się różnią.
2. **Logowanie pełnego kontekstu.** Dla każdej pary rozmów skrypt wypisuje, co się zmieniło, w podziale na trzy grupy z artykułu:
   - **LOSOWOŚĆ:** temperatura, seed,
   - **STAN:** pogoda, magazyn, kierowca, obietnica dostawy, polityka, lokalizacja, wyniki narzędzi,
   - **PLATFORMA:** id modelu, fingerprint, wersja promptu,
   - oraz **ŚCIEŻKA:** czy odpowiedź powstała ścieżką główną, czy zapasową.
3. **Ten sam świat, różne seedy.** Zmienia się tylko losowość, więc wolno zmienić się tylko sformułowaniu.
4. **Awaria, której nie widać.** API pogody nie odpowiada, a bot i tak pisze „spokojnie zdążymy”. Odpowiedź wygląda zdrowo. Problem widać dopiero w polu `sciezka` w logu.

## Ćwiczenie z artykułu

> Weź jedną funkcję AI, z którą pracujesz, i wypisz wszystkie ruchome elementy, które mogą zmienić jej odpowiedź: model, dane, narzędzia, stan użytkownika, czas. Potem sprawdź, ile z nich faktycznie logujesz.

1. Uruchom `python cwiczenie/sprawdz_pokrycie.py` i zobacz wzorcowy wynik dla bota burzowego. Pokrycie wynosi 16/21 elementów. Jeden element („liczba ponowień”) zespół uważał za logowany, a w logu go nie ma.
2. Otwórz `cwiczenie/moj_inwentarz.json` i wpisz ruchome elementy **swojej** funkcji. Dla każdego podaj ścieżkę klucza w swoim logu JSONL, na przykład `request.model`, albo `null`, jeśli go nie logujesz.
3. Sprawdź inwentarz na prawdziwym logu:
   ```bash
   python cwiczenie/sprawdz_pokrycie.py cwiczenie/moj_inwentarz.json sciezka/do/twojego_logu.jsonl
   ```
   Skrypt nie pyta, czy *myślisz*, że coś logujesz. Sprawdza, czy to naprawdę jest w logu.

## Pliki

| Plik | Rola |
|---|---|
| `swiat/t1…t4_*.json` | Migawki świata w różnych momentach soboty |
| `bot.py` | Chatbot: narzędzia, deterministyczny werdykt w kodzie, model ubiera werdykt w słowa, pełny wpis do logu |
| `model.py` | Lokalny, udawany LLM: niedeterministyczny, zależny od temperatury i seeda |
| `wyjasnij.py` | Porównuje dwa wpisy z logu i grupuje różnice: losowość / stan / platforma / ścieżka |
| `cwiczenie/` | Inwentarz ruchomych elementów i skrypt sprawdzający pokrycie logów |
| `logi/rozmowy.jsonl` | Tworzony przez `demo.py` |

## Podpięcie prawdziwego modelu (opcjonalnie)

Podmień ciało funkcji `zapytaj_model()` w `model.py`, tak żeby wysyłała `system` i `prompt` do Twojego API i zwracała `OdpowiedzModelu(tekst, model_id, system_fingerprint)`. Logowanie i porównywanie działają bez zmian.
