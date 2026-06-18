# Klasyfikator Sampli Perkusyjnych 

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



