# Testing AI

*[English](#english) · [Polski](#polski)*

---

## English

Hands-on companion code for a blog series about **testing AI systems and
large language models (LLMs)**. Every article in the series comes with
small, runnable exercises that let you see the ideas in practice instead
of just reading about them.

> The code is illustrative. It is meant to show the idea behind each
> exercise, not to be a production-ready testing framework.

### Who it is for

- Testers and QA engineers moving into AI and LLM quality work
- Developers building features on top of LLMs
- Anyone who wants to understand why "it worked once" is not enough for AI

No machine learning background is needed. Beginner tasks require only
basic Python; intermediate tasks add a bit of statistics and automation.

### What you will find here

Each article has its own directory, and each exercise lives in its own
task directory with:

- a single Python file with **step-by-step instructions in the comments**,
- a short `README.md` explaining what the task teaches and how to run it,
- any extra files the task needs (e.g. sample data).

Tasks run out of the box with a **fake model** that behaves
non-deterministically, just like a real one. No API key is required.
When you are ready, you can connect a real model in one place
(`common/model_client.py`).

### Planned topics

The repository grows together with the series. Planned areas include:

| Area | What the exercises cover |
|------|--------------------------|
| Non-determinism | Why the same prompt gives different answers, what to log, one run vs. many runs |
| Evaluation criteria | Rubrics instead of exact matches, hard blockers, 0–10 scoring with anchor examples |
| Variance and determinism | Harmless vs. blocking differences, temperature, top-p, top-k, seeds |
| Evidence and release gates | Metamorphic testing, golden sets vs. live sampling, risk-based sampling, layered reporting |
| Statistics for AI testing | Confidence intervals, comparing two versions, sample sizes |
| LLM as a judge | Calibrating an automated judge against human ratings |
| Benchmarks and metrics | Choosing metrics that reflect real product risk |
| Releases and monitoring | Canary releases, regression checks, rollback triggers |
| Agents and tools | Testing trajectories, tool calls and permissions, not just final answers |
| Observability and incidents | Traces, logs and reproducible failure reports |
| RAG and data | Retrieval quality, stale documents, synthetic data |
| AI-generated code | Validating code and tests written by AI |
| Anti-patterns | Habits that create false confidence: pass rates, averages, one-off demos |

Topics and their order may change as the series evolves.

### Repository structure

```text
Testing-AI/
├── README.md              # this file
├── requirements.txt       # dependencies (none by default)
├── common/                # shared helpers: model client, run logging
├── templates/             # template for a new task
├── articles/
│   └── NN-article-name/   # one directory per article
│       ├── README.md      # article summary and list of tasks
│       └── task_NN_name/  # one directory per task
│           ├── README.md
│           └── task_NN_name.py
└── results/               # task outputs (JSONL logs), ignored by git
```

### Getting started

Requirements: Python 3.10 or newer.

```bash
git clone https://github.com/KsiazekPatryk/Testing-AI.git
cd Testing-AI
python articles/<article_dir>/<task_dir>/<task_file>.py
```

Open the task file first: the comment at the top explains the goal,
the steps and the questions to think about.

### Contributing

Found a bug, have an idea for an exercise or a better example?
Open an issue or a pull request.

---

## Polski

Praktyczny kod do serii wpisów na blogu o **testowaniu systemów AI
i dużych modeli językowych (LLM)**. Każdy artykuł ma dołączone małe,
gotowe do uruchomienia ćwiczenia, dzięki którym zobaczysz opisane
zjawiska w praktyce, a nie tylko o nich przeczytasz.

> Kod jest poglądowy. Ma pokazać ideę każdego ćwiczenia, a nie być
> gotowym frameworkiem testowym do produkcji.

### Dla kogo

- Testerzy i inżynierowie QA, którzy wchodzą w świat jakości AI i LLM
- Programiści budujący funkcje oparte na LLM
- Każdy, kto chce zrozumieć, dlaczego „raz zadziałało” to za mało w AI

Nie potrzebujesz wiedzy z uczenia maszynowego. Zadania podstawowe
wymagają tylko podstaw Pythona; średnio zaawansowane dokładają trochę
statystyki i automatyzacji.

### Co tu znajdziesz

Każdy artykuł ma swój katalog, a każde ćwiczenie własny katalog zadania, w którym jest:

- jeden plik Pythona z **instrukcjami krok po kroku w komentarzach**,
- krótki `README.md` z opisem, czego uczy zadanie i jak je uruchomić,
- ewentualne dodatkowe pliki potrzebne do zadania (np. przykładowe dane).

Zadania działają od razu dzięki **atrapie modelu**, która zachowuje się
niedeterministycznie, tak jak prawdziwy model. Klucz API nie jest
potrzebny. Prawdziwy model podłączysz w jednym miejscu
(`common/model_client.py`).

### Planowane tematy

Repozytorium rośnie razem z serią. Planowane obszary:

| Obszar | Czego dotyczą ćwiczenia |
|--------|-------------------------|
| Niedeterminizm | Dlaczego ten sam prompt daje różne odpowiedzi, co logować, jedno uruchomienie kontra wiele |
| Kryteria oceny | Rubryki zamiast dokładnego porównania, twarde blokery, skala 0–10 z przykładami kotwiczącymi |
| Wariancja i determinizm | Różnice nieszkodliwe i blokujące, temperatura, top-p, top-k, seed |
| Dowody i bramki wydania | Testowanie metamorficzne, złote zbiory i próbki na żywo, próbkowanie według ryzyka, raportowanie warstwowe |
| Statystyka w testowaniu AI | Przedziały ufności, porównanie dwóch wersji, wielkość próby |
| LLM jako sędzia | Kalibracja automatycznego sędziego względem ocen ludzi |
| Benchmarki i metryki | Dobór metryk, które odzwierciedlają realne ryzyko produktu |
| Wydania i monitoring | Wydania canary, testy regresji, warunki wycofania zmian |
| Agenci i narzędzia | Testowanie ścieżek działania, wywołań narzędzi i uprawnień, a nie tylko odpowiedzi końcowej |
| Obserwowalność i incydenty | Trace'y, logi i odtwarzalne zgłoszenia awarii |
| RAG i dane | Jakość wyszukiwania, nieaktualne dokumenty, dane syntetyczne |
| Kod pisany przez AI | Weryfikacja kodu i testów wygenerowanych przez AI |
| Antywzorce | Nawyki, które dają fałszywą pewność: procent przejść, średnie, jednorazowe demo |

Tematy i ich kolejność mogą się zmieniać wraz z rozwojem serii.

### Struktura repozytorium

```text
Testing-AI/
├── README.md              # ten plik
├── requirements.txt       # zależności (domyślnie brak)
├── common/                # wspólne narzędzia: klient modelu, logowanie uruchomień
├── templates/             # szablon nowego zadania
├── articles/
│   └── NN-nazwa-artykulu/ # jeden katalog na artykuł
│       ├── README.md      # opis artykułu i lista zadań
│       └── task_NN_nazwa/ # jeden katalog na zadanie
│           ├── README.md
│           └── task_NN_nazwa.py
└── results/               # wyniki zadań (logi JSONL), ignorowane przez git
```

### Jak zacząć

Wymagania: Python 3.10 lub nowszy.

```bash
git clone https://github.com/KsiazekPatryk/Testing-AI.git
cd Testing-AI
python articles/<katalog_artykulu>/<katalog_zadania>/<plik_zadania>.py
```

Zacznij od otwarcia pliku zadania: komentarz na początku wyjaśnia cel,
kolejne kroki i pytania do przemyślenia.

### Współpraca

Znalazłeś błąd, masz pomysł na ćwiczenie albo lepszy przykład?
Otwórz issue albo pull request.