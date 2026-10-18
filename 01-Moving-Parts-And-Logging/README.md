# 01 — Moving Parts and Logging

**[English](#english) · [Polski](#polski)**

---

## English

Companion code for the post [**One Run Is Not Proof (Part 1): Where AI Unpredictability Comes From**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz).

> “Can we explain which moving part changed the answer?”

A customer asks a grocery store chatbot: *“Will you get my groceries to me for the picnic before the storm starts?”* The answer changes for honest reasons: the forecast was updated, someone bought the last ice cream, the driver cancelled, or a new policy for chilled goods kicked in. Sometimes, though, it changes because something broke and the bot still sounds confident.

Runs without an API key and without installing any packages (Python 3.9+). The code, comments and console output are in Polish; the ideas carry over one to one.

### Run it

```bash
python demo.py                                   # the whole example, step by step
python exercise/check_coverage.py                # the exercise from the post
python explain.py logs/conversations.jsonl 1 3   # compare any two log entries
python -m unittest -v test_regressions           # regression tests
```

### What `demo.py` shows

1. **Logging only the answer.** Four different answers and no way to tell why they differ.
2. **Logging the full context.** For each pair of conversations, the script prints what changed, split into the three groups from the post:
   - **RANDOMNESS (`losowosc`):** temperature, seed,
   - **STATE (`stan`):** weather, inventory, driver, delivery promise, policy, location, tool results,
   - **PLATFORM (`platforma`):** model id, fingerprint, prompt version,
   - plus the **PATH (`sciezka`):** whether the answer came from the main path or the fallback.
3. **Same world, different seeds.** Only randomness changes, so only the wording is allowed to change.
4. **The failure you can’t see.** The weather API is down, and the bot still says “no problem, we’ll make it”. The answer looks healthy. Only the `sciezka` field in the log shows the problem.

### The exercise from the post

> Take one AI feature you work on and list every moving part that could change its answer: model, data, tools, user state, time. Then check how many of them you actually log.

1. Run `python exercise/check_coverage.py` and look at the reference result for the storm bot. Coverage is 16/21 elements. One element (“number of retries”) was believed to be logged, but it isn’t in the log.
2. Open `exercise/my_inventory.json` and list the moving parts of **your** feature. For each one, give the key path in your JSONL log, for example `request.model`, or `null` if you don’t log it.
3. Check the inventory against a real log:
   ```bash
   python exercise/check_coverage.py exercise/my_inventory.json path/to/your_log.jsonl
   ```
   The script doesn’t ask whether you *think* you log something. It checks whether it’s actually in the log.

### Files

| File | Role |
|---|---|
| `world/t1…t4_*.json` | Snapshots of the world at different moments of the Saturday |
| `bot.py` | The chatbot: tools, a deterministic verdict in code, the model puts the verdict into words, a full log entry |
| `model.py` | A local fake LLM: non-deterministic, driven by temperature and seed |
| `explain.py` | Compares two log entries and groups the differences: randomness / state / platform / path |
| `exercise/` | The moving-parts inventory and the log coverage checker |
| `test_regressions.py` | Regression tests |
| `logs/conversations.jsonl` | Created by `demo.py` |

### Plugging in a real model (optional)

Replace the body of `zapytaj_model()` in `model.py` so it sends `system` and `prompt` to your API and returns `OdpowiedzModelu(tekst, model_id, system_fingerprint)`. Logging and comparison keep working unchanged.

---

## Polski

Przykład do wpisu [**Jedno uruchomienie to nie dowód (cz. 1). Skąd bierze się nieprzewidywalność AI**](https://paprico.substack.com/p/jedno-uruchomienie-to-nie-dowod-cz).

> „Czy potrafimy wyjaśnić, który ruchomy element zmienił odpowiedź?”

Klient pyta chatbota sklepu: *„Czy zdążycie dowieźć moje zakupy na piknik, zanim zacznie się burza?”* Odpowiedź zmienia się z uczciwych powodów: zmieniła się prognoza, ktoś kupił ostatnie lody, kierowca anulował kurs albo weszła nowa polityka dla produktów chłodzonych. Czasem jednak zmienia się, bo coś się zepsuło, a bot nadal brzmi pewnie.

Działa bez klucza API i bez instalowania pakietów (Python 3.9+).

### Uruchom

```bash
python demo.py                                   # cały przykład krok po kroku
python exercise/check_coverage.py                # ćwiczenie z artykułu
python explain.py logs/conversations.jsonl 1 3   # porównaj dowolne dwa wpisy z logu
python -m unittest -v test_regressions           # testy regresyjne
```

### Co pokazuje `demo.py`

1. **Logowanie samej odpowiedzi.** Cztery różne odpowiedzi i brak wiedzy, dlaczego się różnią.
2. **Logowanie pełnego kontekstu.** Dla każdej pary rozmów skrypt wypisuje, co się zmieniło, w podziale na trzy grupy z artykułu:
   - **LOSOWOŚĆ:** temperatura, seed,
   - **STAN:** pogoda, magazyn, kierowca, obietnica dostawy, polityka, lokalizacja, wyniki narzędzi,
   - **PLATFORMA:** id modelu, fingerprint, wersja promptu,
   - oraz **ŚCIEŻKA:** czy odpowiedź powstała ścieżką główną, czy zapasową.
3. **Ten sam świat, różne seedy.** Zmienia się tylko losowość, więc wolno zmienić się tylko sformułowaniu.
4. **Awaria, której nie widać.** API pogody nie odpowiada, a bot i tak pisze „spokojnie zdążymy”. Odpowiedź wygląda zdrowo. Problem widać dopiero w polu `sciezka` w logu.

### Ćwiczenie z artykułu

> Weź jedną funkcję AI, z którą pracujesz, i wypisz wszystkie ruchome elementy, które mogą zmienić jej odpowiedź: model, dane, narzędzia, stan użytkownika, czas. Potem sprawdź, ile z nich faktycznie logujesz.

1. Uruchom `python exercise/check_coverage.py` i zobacz wzorcowy wynik dla bota burzowego. Pokrycie wynosi 16/21 elementów. Jeden element („liczba ponowień”) zespół uważał za logowany, a w logu go nie ma.
2. Otwórz `exercise/my_inventory.json` i wpisz ruchome elementy **swojej** funkcji. Dla każdego podaj ścieżkę klucza w swoim logu JSONL, na przykład `request.model`, albo `null`, jeśli go nie logujesz.
3. Sprawdź inwentarz na prawdziwym logu:
   ```bash
   python exercise/check_coverage.py exercise/my_inventory.json sciezka/do/twojego_logu.jsonl
   ```
   Skrypt nie pyta, czy *myślisz*, że coś logujesz. Sprawdza, czy to naprawdę jest w logu.

### Pliki

| Plik | Rola |
|---|---|
| `world/t1…t4_*.json` | Migawki świata w różnych momentach soboty |
| `bot.py` | Chatbot: narzędzia, deterministyczny werdykt w kodzie, model ubiera werdykt w słowa, pełny wpis do logu |
| `model.py` | Lokalny, udawany LLM: niedeterministyczny, zależny od temperatury i seeda |
| `explain.py` | Porównuje dwa wpisy z logu i grupuje różnice: losowość / stan / platforma / ścieżka |
| `exercise/` | Inwentarz ruchomych elementów i skrypt sprawdzający pokrycie logów |
| `test_regressions.py` | Testy regresyjne |
| `logs/conversations.jsonl` | Tworzony przez `demo.py` |

### Podpięcie prawdziwego modelu (opcjonalnie)

Podmień ciało funkcji `zapytaj_model()` w `model.py`, tak żeby wysyłała `system` i `prompt` do Twojego API i zwracała `OdpowiedzModelu(tekst, model_id, system_fingerprint)`. Logowanie i porównywanie działają bez zmian.
