# KONTEKST PROJEKTU — Klasyfikator Sampli Perkusyjnych
# Wygenerowano z rozmowy na claude.ai
# Wrzuć ten plik do folderu projektu i powiedz Claude Code: "przeczytaj CONTEXT.md"

---

## Co to jest

Aplikacja dydaktyczna na zaliczenie przedmiotu **Sztuczna Inteligencja** (Politechnika Białostocka).
Klasyfikuje sample perkusyjne (kick, snare, hi-hat, clap, tom) przy użyciu **drzewa decyzyjnego CART
zaimplementowanego od podstaw** (bez sklearn).

---

## Struktura projektu

```
drum_classifier/
├── app/
│   ├── main.py              # FastAPI — REST API + serwuje static/index.html
│   ├── decision_tree.py     # Własna implementacja CART (wymagane przez zadanie!)
│   ├── audio_features.py    # Ekstrakcja 43 cech audio przez librosa
│   └── metrics.py           # Accuracy, F1, macierz konfuzji — też własne
├── static/
│   └── index.html           # Cały frontend — vanilla JS + D3.js, single file
├── samples/                 # 30 syntetycznych sampli .wav do testowania
├── uploads/                 # Wgrane przez użytkownika pliki (runtime)
├── exports/                 # Eksportowane wyniki JSON (runtime)
├── generate_test_samples.py # Generator syntetycznych sampli
├── test_pipeline.py         # Test całego pipeline bez FastAPI
└── requirements.txt
```

---

## Jak uruchomić

```bash
cd drum_classifier/app
python -m uvicorn main:app --reload --port 8000
# Otwórz: http://localhost:8000
```

---

## API Endpointy

| Method | Endpoint         | Opis                                          |
|--------|------------------|-----------------------------------------------|
| GET    | /                | Serwuje frontend (static/index.html)          |
| GET    | /health          | Status serwera                                |
| POST   | /upload          | Upload 1 pliku audio + label                  |
| POST   | /upload-batch    | Upload WIELU plików naraz (równolegle, 4 wątki) |
| GET    | /files           | Lista wgranych plików                         |
| DELETE | /files/{id}      | Usuń plik                                     |
| GET    | /files/{id}/waveform | Dane fali do wizualizacji                 |
| GET    | /dataset         | Statystyki datasetu                           |
| POST   | /train           | Trenuj drzewo (parametry w body JSON)         |
| GET    | /tree            | Pobierz strukturę drzewa jako JSON            |
| POST   | /predict         | Klasyfikuj nowy plik audio                    |
| GET    | /export          | Eksportuj wyniki do pliku JSON                |

---

## Parametry trenowania (POST /train)

```json
{
  "criterion": "gini",         // "gini" lub "entropy"
  "max_depth": 5,              // 1-15
  "min_samples_split": 2,      // 2-20
  "min_samples_leaf": 1,       // 1-10
  "test_split": 0.2            // 0.1-0.4
}
```

---

## Cechy audio (43 cechy w wektorze)

Ekstraktor: `audio_features.py` → `extract_features(path)`

- spectral_centroid mean/std
- spectral_bandwidth mean/std
- spectral_rolloff mean/std
- spectral_flatness mean/std
- rms mean/std
- zero_crossing_rate mean/std
- mfcc_1..13 mean/std (26 cech)
- onset_strength mean/std
- tempo
- chroma mean/std

---

## Stan aplikacji (in-memory, resetuje się po restarcie)

```python
state = {
    "uploaded_files": {},    # file_id -> {file_id, filename, path, label, features, waveform}
    "model": None,           # DecisionTreeClassifier po fit()
    "last_evaluation": None, # wyniki evaluate_full()
    "tree_params": {...},    # ostatnio użyte parametry
}
```

---

## Co jest zaimplementowane samodzielnie (wymóg zadania)

- `decision_tree.py` — klasa `DecisionTreeClassifier` z metodami:
  - `fit(X, y, feature_names)` — buduje drzewo CART
  - `predict(X)` — predykcja
  - `predict_proba(X)` — rozkład klas w liściu
  - `to_dict()` — serializacja całego drzewa do JSON (dla D3.js)
  - `count_nodes()` — statystyki węzłów
  - `get_depth()` — rzeczywista głębokość
  - Wewnętrznie: `_gini()`, `_entropy()`, `_best_split()`, `_build()` (rekurencja)

- `metrics.py` — własne:
  - `accuracy(y_true, y_pred)`
  - `confusion_matrix(...)`
  - `precision_recall_f1(...)`
  - `evaluate_full(...)` — łączy wszystko + statystyki drzewa

---

## Frontend (static/index.html)

Vanilla JS + D3.js (bez Vue, bez buildu). Single file.

**Zakładki:**
1. **Wizualizacja danych** — fala dźwiękowa canvas + 43 cechy jako słupki
2. **Drzewo decyzyjne** — D3.js SVG, węzły klikalne, tooltip z detalami
3. **Ocena modelu** — karty metryk, macierz konfuzji, F1 per klasa
4. **Predykcja** — upload nowego pliku → wynik + prawdopodobieństwa

**Sidebar:**
- Wybór etykiety (kick/snare/hihat/clap/tom)
- Upload zone (drag & drop, multi-select)
- Lista plików z możliwością usuwania
- 4 parametry drzewa jako suwaki
- Przyciski: Trenuj / Eksportuj JSON

---

## Co JESZCZE TRZEBA ZROBIĆ / Known issues

1. **Frontend używa starego `/upload` w pętli** zamiast nowego `/upload-batch`
   - W `static/index.html` funkcja uploadowania plików wysyła je jeden po jednym
   - Trzeba zmienić na `/upload-batch` który przyjmuje `files[]` + `label`
   - Endpoint `/upload-batch` już istnieje w `main.py` i działa
   - Przy 100 plikach obecne rozwiązanie jest wolne bo każdy plik = osobny request

2. **Brak progress bara dla batch upload**
   - Przy wgrywaniu 100 plików user nie widzi postępu
   - Można dodać SSE (Server-Sent Events) lub po prostu spinner z licznikiem

3. **Historia budowy drzewa (opcjonalne)**
   - Zadanie mówi o "wizualizacji kroków pośrednich"
   - Teraz drzewo wyświetla się od razu w całości
   - Można dodać animację węzeł po węźle ale to nice-to-have

---

## Zależności (requirements.txt)

```
fastapi>=0.100.0
uvicorn>=0.23.0
librosa>=0.10.0
numpy>=1.24.0
soundfile>=0.12.0
python-multipart>=0.0.6
aiofiles>=23.0.0
```

---

## Klasy sampli

| Label  | Kolor w UI | Opis              |
|--------|------------|-------------------|
| kick   | czerwony   | stopa             |
| snare  | pomarańcz  | werbel            |
| hihat  | cyan       | talerz            |
| clap   | zielony    | klaskanie         |
| tom    | fioletowy  | bęben tom         |

---

## Najpilniejsze zadanie dla Claude Code

Napraw upload w `static/index.html` żeby używał `/upload-batch`:

1. Znajdź funkcję która uploaduje pliki (obsługuje `fileInput` change event i drop event)
2. Zamiast pętli z pojedynczymi requestami do `/upload` — zrób jeden request do `/upload-batch`
   z `FormData` zawierającym `files[]` (wiele plików) i `label`
3. Dodaj progress bar / licznik podczas uploadu (np. "Przetwarzanie 47/100...")
4. Backend zwraca `{ uploaded: N, errors: M, files: [...] }` — użyj tego do aktualizacji listy

Przykład jak zbudować FormData dla batch:
```javascript
const fd = new FormData();
fd.append('label', selectedLabel);
for (const file of files) {
  fd.append('files', file);  // klucz to 'files' (lista)
}
const r = await fetch(API + '/upload-batch', { method: 'POST', body: fd });
const data = await r.json();
// data.files = [{file_id, filename, label}, ...]
```
