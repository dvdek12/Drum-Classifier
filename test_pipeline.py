"""
Test całego pipeline'u bez FastAPI — sprawdza czy wszystkie moduły działają.
"""

import sys
sys.path.insert(0, "app")

import numpy as np
from pathlib import Path
from audio_features import extract_features, get_feature_names
from decision_tree import DecisionTreeClassifier
from metrics import evaluate_full, accuracy
import json

SAMPLES_DIR = Path("samples")

print("=" * 60)
print("TEST PIPELINE — Klasyfikator Sampli Perkusyjnych")
print("=" * 60)

# 1. Ekstrakcja cech
print("\n[1] Ekstrakcja cech audio...")
X_list, y_list = [], []
labels = ["kick", "snare", "hihat", "clap", "tom"]

for label in labels:
    files = sorted(SAMPLES_DIR.glob(f"{label}_*.wav"))
    for f in files:
        feat = extract_features(str(f))
        X_list.append(feat)
        y_list.append(label)
        print(f"  ✓ {f.name:20s} → {len(feat)} cech")

X = np.array(X_list)
y = np.array(y_list)
print(f"\n  Dataset: {X.shape[0]} próbek × {X.shape[1]} cech")
print(f"  Klasy: {np.unique(y).tolist()}")

# 2. Podział train/test
print("\n[2] Podział danych...")
np.random.seed(42)
idx = np.random.permutation(len(X))
n_test = max(1, int(len(X) * 0.3))
X_train, y_train = X[idx[n_test:]], y[idx[n_test:]]
X_test,  y_test  = X[idx[:n_test]], y[idx[:n_test]]
print(f"  Trening: {len(X_train)} | Test: {len(X_test)}")

# 3. Trenowanie drzewa
print("\n[3] Trenowanie drzewa decyzyjnego (CART)...")
import time

for criterion in ["gini", "entropy"]:
    t0 = time.time()
    tree = DecisionTreeClassifier(
        criterion=criterion,
        max_depth=5,
        min_samples_split=2,
        min_samples_leaf=1,
    )
    tree.fit(X_train, y_train, feature_names=get_feature_names())
    elapsed = (time.time() - t0) * 1000

    y_pred = tree.predict(X_test)
    acc = accuracy(y_test, y_pred)
    nodes = tree.count_nodes()

    print(f"\n  Kryterium: {criterion.upper()}")
    print(f"  Accuracy:  {acc:.1%}")
    print(f"  Głębokość: {tree.get_depth()}")
    print(f"  Węzły: {nodes['total']} (wewnętrzne: {nodes['internal']}, liście: {nodes['leaves']})")
    print(f"  Czas trenowania: {elapsed:.1f} ms")

# 4. Test serializacji do JSON
print("\n[4] Serializacja drzewa do JSON...")
tree_dict = tree.to_dict()
json_str = json.dumps(tree_dict, ensure_ascii=False, indent=2)
print(f"  Rozmiar JSON: {len(json_str)} znaków")
print(f"  Klasy: {tree_dict['classes']}")
print(f"  Parametry: {tree_dict['params']}")

# 5. Zapis do pliku
out_path = Path("exports/test_tree.json")
out_path.parent.mkdir(exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(tree_dict, f, ensure_ascii=False, indent=2)
print(f"\n  Zapisano drzewo do: {out_path}")

# 6. Predykcja na jednej próbce
print("\n[5] Predykcja pojedynczej próbki...")
sample_path = SAMPLES_DIR / "kick_01.wav"
feat = extract_features(str(sample_path))
pred = tree.predict(feat.reshape(1, -1))[0]
proba = tree.predict_proba(feat.reshape(1, -1))[0]
print(f"  Plik: kick_01.wav")
print(f"  Predykcja: {pred}")
print(f"  Prawdopodobieństwa: {proba}")

print("\n" + "=" * 60)
print("WSZYSTKIE TESTY PRZESZŁY ✓")
print("=" * 60)
