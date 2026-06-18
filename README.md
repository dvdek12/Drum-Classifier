# Klasyfikator Sampli Perkusyjnych 

Aplikacja dydaktyczna do klasyfikacji sampli perkusyjnych (kick, snare, hi-hat, clap, tom)
przy użyciu **drzewa decyzyjnego CART** zaimplementowanego od podstaw.



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



