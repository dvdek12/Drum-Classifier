# Klasyfikator Sampli Perkusyjnych 🥁

Aplikacja dydaktyczna do klasyfikacji sampli perkusyjnych (kick, snare, hi-hat, clap, tom)
przy użyciu **drzewa decyzyjnego CART** zaimplementowanego od podstaw.

## Struktura projektu

```
drum_classifier/
├── app/
│   ├── main.py              # FastAPI — serwer REST API
│   ├── decision_tree.py     # Własna implementacja CART
│   ├── audio_features.py    # Ekstrakcja cech (MFCC, spektralne, itp.)
│   └── metrics.py           # Metryki oceny (accuracy, F1, macierz konfuzji)
├── samples/                 # Przykładowe sample (generowane)
├── uploads/                 # Wgrane przez użytkownika pliki
├── exports/                 # Eksportowane wyniki JSON
├── generate_test_samples.py # Generator syntetycznych sampli
├── test_pipeline.py         # Test całego pipeline'u
└── requirements.txt
```

## Instalacja

```bash
# Klonuj repo / wypakuj projekt
cd drum_classifier

# Utwórz wirtualne środowisko (zalecane)
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Zainstaluj zależności
pip install -r requirements.txt
```

## Uruchomienie

```bash
# Wygeneruj sample testowe (opcjonalne)
python generate_test_samples.py

# Uruchom backend
cd app
uvicorn main:app --reload --port 8000
```

API dostępne pod: http://localhost:8000
Dokumentacja Swagger: http://localhost:8000/docs

## Endpointy API

| Metoda | Endpoint           | Opis                                    |
|--------|--------------------|-----------------------------------------|
| GET    | /health            | Status serwera                          |
| POST   | /upload            | Wgraj plik audio z etykietą             |
| GET    | /files             | Lista wgranych plików                   |
| GET    | /files/{id}/waveform | Dane fali dźwiękowej                  |
| GET    | /files/{id}/features | Wektor cech                           |
| DELETE | /files/{id}        | Usuń plik z datasetu                    |
| GET    | /dataset           | Podsumowanie datasetu                   |
| POST   | /train             | Trenuj drzewo decyzyjne                 |
| GET    | /tree              | Pobierz strukturę drzewa (JSON)         |
| POST   | /predict           | Klasyfikuj nowy plik                    |
| GET    | /export            | Eksportuj wyniki do JSON                |

## Parametry drzewa (POST /train)

```json
{
  "criterion": "gini",        // "gini" lub "entropy"
  "max_depth": 5,             // maks. głębokość (1-20)
  "min_samples_split": 2,     // min. próbek do podziału (2-20)
  "min_samples_leaf": 1,      // min. próbek w liściu (1-10)
  "test_split": 0.2           // % danych testowych (0.1-0.5)
}
```

## Cechy audio (43 cechy)

- **Spektralne** (8): centroid, bandwidth, rolloff, flatness
- **Energia** (4): RMS, zero crossing rate
- **MFCC** (26): 13 współczynników × mean/std
- **Onset** (3): siła ataku × mean/std + tempo
- **Chroma** (2): średni profil harmoniczny

## Etykiety klas

- `kick` — stopa
- `snare` — werbel
- `hihat` — talerz zamknięty/otwarty
- `clap` — klaskanie
- `tom` — bęben tom
