"""
Implementacja drzewa decyzyjnego od podstaw (algorytm CART).
Bez użycia sklearn - własna implementacja wymagana przez zadanie.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """Węzeł drzewa decyzyjnego."""
    # Parametry węzła wewnętrznego (decyzja)
    feature_index: Optional[int] = None   # indeks cechy po której dzielimy
    threshold: Optional[float] = None     # próg podziału
    feature_name: Optional[str] = None    # nazwa cechy (do wizualizacji)

    # Parametry liścia (wynik)
    predicted_class: Optional[str] = None
    class_distribution: Optional[dict] = None  # ile próbek każdej klasy

    # Statystyki węzła
    samples: int = 0
    impurity: float = 0.0
    depth: int = 0

    # Dzieci
    left: Optional["Node"] = None   # <= threshold
    right: Optional["Node"] = None  # >  threshold

    # ID do wizualizacji
    node_id: int = 0

    def is_leaf(self) -> bool:
        return self.predicted_class is not None

    def to_dict(self) -> dict:
        """Serializacja węzła do JSON (dla frontendu)."""
        d = {
            "node_id": int(self.node_id),
            "depth": int(self.depth),
            "samples": int(self.samples),
            "impurity": round(float(self.impurity), 4),
            "is_leaf": self.is_leaf(),
            "class_distribution": {k: int(v) for k, v in (self.class_distribution or {}).items()},
        }
        if self.is_leaf():
            d["predicted_class"] = str(self.predicted_class)
        else:
            d["feature_index"] = int(self.feature_index)
            d["feature_name"] = str(self.feature_name)
            d["threshold"] = round(float(self.threshold), 4)
            d["left"] = self.left.to_dict() if self.left else None
            d["right"] = self.right.to_dict() if self.right else None
        return d


class DecisionTreeClassifier:
    """
    Klasyfikator drzewa decyzyjnego - implementacja CART.

    Parametry (ustawiane przez użytkownika w aplikacji):
        criterion     - kryterium podziału: 'gini' lub 'entropy'
        max_depth     - maksymalna głębokość drzewa
        min_samples_split - minimalna liczba próbek do podziału węzła
        min_samples_leaf  - minimalna liczba próbek w liściu
    """

    def __init__(
        self,
        criterion: str = "gini",
        max_depth: int = 5,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
    ):
        if criterion not in ("gini", "entropy"):
            raise ValueError("criterion musi być 'gini' lub 'entropy'")

        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf

        self.root: Optional[Node] = None
        self.feature_names: list[str] = []
        self.classes_: list[str] = []
        self._node_counter = 0

    # ------------------------------------------------------------------ #
    #  Miary nieczystości                                                  #
    # ------------------------------------------------------------------ #

    def _gini(self, y: np.ndarray) -> float:
        """Gini impurity: 1 - Σ p_i²"""
        n = len(y)
        if n == 0:
            return 0.0
        _, counts = np.unique(y, return_counts=True)
        probs = counts / n
        return 1.0 - float(np.sum(probs ** 2))

    def _entropy(self, y: np.ndarray) -> float:
        """Entropia informacyjna: -Σ p_i * log2(p_i)"""
        n = len(y)
        if n == 0:
            return 0.0
        _, counts = np.unique(y, return_counts=True)
        probs = counts / n
        # bezpieczny log2 — ignorujemy p=0
        return float(-np.sum(probs * np.log2(probs + 1e-12)))

    def _impurity(self, y: np.ndarray) -> float:
        if self.criterion == "gini":
            return self._gini(y)
        return self._entropy(y)

    # ------------------------------------------------------------------ #
    #  Szukanie najlepszego podziału                                       #
    # ------------------------------------------------------------------ #

    def _best_split(self, X: np.ndarray, y: np.ndarray):
        """
        Przegląda wszystkie cechy i progi, zwraca najlepszy podział
        jako (feature_index, threshold) lub (None, None) jeśli brak poprawy.
        """
        n_samples, n_features = X.shape
        best_gain = -np.inf
        best_feat = None
        best_thresh = None

        parent_impurity = self._impurity(y)

        for feat_idx in range(n_features):
            col = X[:, feat_idx]
            # Progi to unikalne wartości środkowe między sąsiednimi próbkami
            sorted_vals = np.unique(col)
            thresholds = (sorted_vals[:-1] + sorted_vals[1:]) / 2.0

            for thresh in thresholds:
                left_mask = col <= thresh
                right_mask = ~left_mask

                n_left = left_mask.sum()
                n_right = right_mask.sum()

                # Warunek minimalnej liczby próbek w liściu
                if n_left < self.min_samples_leaf or n_right < self.min_samples_leaf:
                    continue

                # Information Gain
                gain = parent_impurity - (
                    n_left  / n_samples * self._impurity(y[left_mask]) +
                    n_right / n_samples * self._impurity(y[right_mask])
                )

                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat_idx
                    best_thresh = thresh

        return best_feat, best_thresh

    # ------------------------------------------------------------------ #
    #  Budowa drzewa (rekurencja)                                          #
    # ------------------------------------------------------------------ #

    def _class_distribution(self, y: np.ndarray) -> dict:
        classes, counts = np.unique(y, return_counts=True)
        return {str(c): int(n) for c, n in zip(classes, counts)}

    def _majority_class(self, y: np.ndarray) -> str:
        classes, counts = np.unique(y, return_counts=True)
        return str(classes[np.argmax(counts)])

    def _build(self, X: np.ndarray, y: np.ndarray, depth: int) -> Node:
        self._node_counter += 1
        node_id = self._node_counter

        impurity = self._impurity(y)
        dist = self._class_distribution(y)

        node = Node(
            samples=len(y),
            impurity=impurity,
            depth=depth,
            node_id=node_id,
            class_distribution=dist,
        )

        # Warunki zatrzymania → liść
        if (
            depth >= self.max_depth
            or len(y) < self.min_samples_split
            or len(np.unique(y)) == 1
            or impurity == 0.0
        ):
            node.predicted_class = self._majority_class(y)
            return node

        # Szukamy najlepszego podziału
        feat_idx, threshold = self._best_split(X, y)

        if feat_idx is None:
            # Brak poprawy → liść
            node.predicted_class = self._majority_class(y)
            return node

        # Tworzymy węzeł wewnętrzny
        node.feature_index = feat_idx
        node.threshold = threshold
        node.feature_name = (
            self.feature_names[feat_idx]
            if feat_idx < len(self.feature_names)
            else f"feature_{feat_idx}"
        )

        mask = X[:, feat_idx] <= threshold
        node.left  = self._build(X[mask],  y[mask],  depth + 1)
        node.right = self._build(X[~mask], y[~mask], depth + 1)

        return node

    # ------------------------------------------------------------------ #
    #  Publiczny API                                                        #
    # ------------------------------------------------------------------ #

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] = None):
        """Trenuje drzewo na danych X, y."""
        self._node_counter = 0
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self.classes_ = [str(c) for c in np.unique(y)]
        self.root = self._build(X, y.astype(str), depth=0)
        return self

    def _predict_one(self, x: np.ndarray, node: Node) -> str:
        if node.is_leaf():
            return node.predicted_class
        if x[node.feature_index] <= node.threshold:
            return self._predict_one(x, node.left)
        return self._predict_one(x, node.right)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predykcja klas dla tablicy próbek."""
        if self.root is None:
            raise RuntimeError("Drzewo nie zostało wytrenowane. Wywołaj fit() najpierw.")
        return np.array([self._predict_one(x, self.root) for x in X])

    def predict_proba(self, X: np.ndarray) -> list[dict]:
        """Zwraca rozkład klas dla każdej próbki (do wizualizacji pewności)."""
        results = []
        for x in X:
            node = self.root
            while not node.is_leaf():
                if x[node.feature_index] <= node.threshold:
                    node = node.left
                else:
                    node = node.right
            total = sum(node.class_distribution.values())
            proba = {k: v / total for k, v in node.class_distribution.items()}
            results.append(proba)
        return results

    def to_dict(self) -> dict:
        """Pełna serializacja drzewa do JSON."""
        if self.root is None:
            return {}
        return {
            "params": {
                "criterion": self.criterion,
                "max_depth": self.max_depth,
                "min_samples_split": self.min_samples_split,
                "min_samples_leaf": self.min_samples_leaf,
            },
            "feature_names": self.feature_names,
            "classes": self.classes_,
            "tree": self.root.to_dict(),
        }

    def count_nodes(self) -> dict:
        """Liczy węzły w drzewie (efektywność)."""
        total = internal = leaves = 0

        def _count(node):
            nonlocal total, internal, leaves
            if node is None:
                return
            total += 1
            if node.is_leaf():
                leaves += 1
            else:
                internal += 1
                _count(node.left)
                _count(node.right)

        _count(self.root)
        return {"total": total, "internal": internal, "leaves": leaves}

    def get_depth(self) -> int:
        """Zwraca rzeczywistą głębokość drzewa."""
        def _depth(node):
            if node is None or node.is_leaf():
                return 0
            return 1 + max(_depth(node.left), _depth(node.right))
        return _depth(self.root)
