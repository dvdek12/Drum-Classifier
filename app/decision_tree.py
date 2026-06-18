
import numpy as np
from sklearn.tree import DecisionTreeClassifier as _SklearnDT
from sklearn.tree._tree import TREE_LEAF


# Mapowanie nazw kryteriów z UI na nazwy sklearn
_CRITERION_MAP = {
    "gini":             "gini",
    "information_gain": "entropy",
    "gain_ratio":       "entropy",  # sklearn nie ma gain_ratio — używamy entropy
}


class DecisionTreeClassifier:

    def __init__(
        self,
        criterion: str = "gini",
        max_depth: int = 5,
        min_example_count: int = 2,
        min_gain: float = 0.0,
    ):
        self.criterion          = criterion
        self.max_depth          = max_depth
        self.min_example_count  = min_example_count
        self.min_gain           = min_gain

        self.feature_names: list[str] = []
        self.classes_: list[str]      = []

        sklearn_criterion = _CRITERION_MAP.get(criterion, "gini")
        self._model = _SklearnDT(
            criterion=sklearn_criterion,
            max_depth=max_depth,
            min_samples_split=max(2, min_example_count),
            min_impurity_decrease=min_gain,
            random_state=42,
        )

    # ------------------------------------------------------------------ #
    #  Publiczny API                                                        #
    # ------------------------------------------------------------------ #

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] = None):
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self._model.fit(X, y)
        self.classes_ = [str(c) for c in self._model.classes_]
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> list[dict]:
        proba_matrix = self._model.predict_proba(X)
        result = []
        for row in proba_matrix:
            result.append({cls: float(p) for cls, p in zip(self.classes_, row)})
        return result

    def to_dict(self) -> dict:
        if not hasattr(self._model, "tree_"):
            return {}
        return {
            "params": {
                "criterion":         self.criterion,
                "max_depth":         self.max_depth,
                "min_example_count": self.min_example_count,
                "min_gain":          self.min_gain,
            },
            "feature_names": self.feature_names,
            "classes":       self.classes_,
            "tree":          self._node_to_dict(0, depth=0),
        }

    def count_nodes(self) -> dict:
        if not hasattr(self._model, "tree_"):
            return {"total": 0, "internal": 0, "leaves": 0}
        t = self._model.tree_
        leaves   = int(np.sum(t.children_left == TREE_LEAF))
        internal = int(t.node_count) - leaves
        return {"total": int(t.node_count), "internal": internal, "leaves": leaves}

    def get_depth(self) -> int:
        if not hasattr(self._model, "tree_"):
            return 0
        return int(self._model.get_depth())

    # ------------------------------------------------------------------ #
    #  Serializacja drzewa do formatu oczekiwanego przez frontend          #
    # ------------------------------------------------------------------ #

    def _node_to_dict(self, node_id: int, depth: int) -> dict:
        t = self._model.tree_
        left_child  = t.children_left[node_id]
        right_child = t.children_right[node_id]
        is_leaf     = bool(left_child == TREE_LEAF)

        # Rozkład klas w węźle (sklearn przechowuje ułamki — mnożymy przez n próbek)
        values   = t.value[node_id][0]
        n        = int(t.n_node_samples[node_id])
        dist     = {cls: int(round(float(v) * n)) for cls, v in zip(self.classes_, values)}
        majority = self.classes_[int(np.argmax(values))]

        d = {
            "node_id":            int(node_id),
            "depth":              int(depth),
            "samples":            int(t.n_node_samples[node_id]),
            "impurity":           round(float(t.impurity[node_id]), 4),
            "is_leaf":            is_leaf,
            "class_distribution": dist,
        }

        if is_leaf:
            d["predicted_class"] = majority
        else:
            feat_idx = int(t.feature[node_id])
            d["feature_index"] = feat_idx
            d["feature_name"]  = (
                self.feature_names[feat_idx]
                if feat_idx < len(self.feature_names)
                else f"feature_{feat_idx}"
            )
            d["threshold"] = round(float(t.threshold[node_id]), 4)
            d["left"]      = self._node_to_dict(int(left_child),  depth + 1)
            d["right"]     = self._node_to_dict(int(right_child), depth + 1)

        return d


# ============================================================
# WŁASNA IMPLEMENTACJA CART (zakomentowana)
# ============================================================

# import numpy as np
# from dataclasses import dataclass, field
# from typing import Optional
#
#
# @dataclass
# class Node:
#     """Węzeł drzewa decyzyjnego."""
#     feature_index: Optional[int] = None
#     threshold: Optional[float] = None
#     feature_name: Optional[str] = None
#     predicted_class: Optional[str] = None
#     class_distribution: Optional[dict] = None
#     samples: int = 0
#     impurity: float = 0.0
#     depth: int = 0
#     left: Optional["Node"] = None
#     right: Optional["Node"] = None
#     node_id: int = 0
#
#     def is_leaf(self) -> bool:
#         return self.predicted_class is not None
#
#     def to_dict(self) -> dict:
#         d = {
#             "node_id": int(self.node_id),
#             "depth": int(self.depth),
#             "samples": int(self.samples),
#             "impurity": round(float(self.impurity), 4),
#             "is_leaf": self.is_leaf(),
#             "class_distribution": {k: int(v) for k, v in (self.class_distribution or {}).items()},
#         }
#         if self.is_leaf():
#             d["predicted_class"] = str(self.predicted_class)
#         else:
#             d["feature_index"] = int(self.feature_index)
#             d["feature_name"] = str(self.feature_name)
#             d["threshold"] = round(float(self.threshold), 4)
#             d["left"] = self.left.to_dict() if self.left else None
#             d["right"] = self.right.to_dict() if self.right else None
#         return d
#
#
# class DecisionTreeClassifier:
#     def __init__(self, criterion="gini", max_depth=5, min_example_count=2, min_gain=0.0):
#         if criterion not in ("gini", "information_gain", "gain_ratio"):
#             raise ValueError("criterion musi być 'gini', 'information_gain' lub 'gain_ratio'")
#         self.criterion = criterion
#         self.max_depth = max_depth
#         self.min_example_count = min_example_count
#         self.min_gain = min_gain
#         self.root: Optional[Node] = None
#         self.feature_names: list[str] = []
#         self.classes_: list[str] = []
#         self._node_counter = 0
#
#     def _gini(self, y):
#         n = len(y)
#         if n == 0: return 0.0
#         _, counts = np.unique(y, return_counts=True)
#         probs = counts / n
#         return 1.0 - float(np.sum(probs ** 2))
#
#     def _entropy(self, y):
#         n = len(y)
#         if n == 0: return 0.0
#         _, counts = np.unique(y, return_counts=True)
#         probs = counts / n
#         return float(-np.sum(probs * np.log2(probs + 1e-12)))
#
#     def _information_gain(self, y, y_left, y_right):
#         n = len(y)
#         n_left, n_right = len(y_left), len(y_right)
#         return self._entropy(y) - (n_left/n * self._entropy(y_left) + n_right/n * self._entropy(y_right))
#
#     def _gain_ratio(self, y, y_left, y_right):
#         ig = self._information_gain(y, y_left, y_right)
#         n = len(y)
#         p_left, p_right = len(y_left)/n, len(y_right)/n
#         split_info = -(p_left*np.log2(p_left+1e-12) + p_right*np.log2(p_right+1e-12))
#         if split_info < 1e-12: return 0.0
#         return ig / split_info
#
#     def _impurity(self, y):
#         if self.criterion == "gini": return self._gini(y)
#         return self._entropy(y)
#
#     def _split_score(self, y, y_left, y_right):
#         n = len(y); n_left, n_right = len(y_left), len(y_right)
#         if self.criterion == "gini":
#             return self._gini(y) - (n_left/n*self._gini(y_left) + n_right/n*self._gini(y_right))
#         if self.criterion == "information_gain":
#             return self._information_gain(y, y_left, y_right)
#         return self._gain_ratio(y, y_left, y_right)
#
#     def _best_split(self, X, y):
#         n_samples, n_features = X.shape
#         best_gain, best_feat, best_thresh = -np.inf, None, None
#         for feat_idx in range(n_features):
#             col = X[:, feat_idx]
#             sorted_vals = np.unique(col)
#             thresholds = (sorted_vals[:-1] + sorted_vals[1:]) / 2.0
#             for thresh in thresholds:
#                 left_mask = col <= thresh
#                 score = self._split_score(y, y[left_mask], y[~left_mask])
#                 if score <= self.min_gain: continue
#                 if score > best_gain:
#                     best_gain = score; best_feat = feat_idx; best_thresh = thresh
#         return best_feat, best_thresh
#
#     def _class_distribution(self, y):
#         classes, counts = np.unique(y, return_counts=True)
#         return {str(c): int(n) for c, n in zip(classes, counts)}
#
#     def _majority_class(self, y):
#         classes, counts = np.unique(y, return_counts=True)
#         return str(classes[np.argmax(counts)])
#
#     def _build(self, X, y, depth):
#         self._node_counter += 1
#         node_id = self._node_counter
#         impurity = self._impurity(y)
#         dist = self._class_distribution(y)
#         node = Node(samples=len(y), impurity=impurity, depth=depth, node_id=node_id, class_distribution=dist)
#         if (depth >= self.max_depth or len(y) < self.min_example_count
#                 or len(np.unique(y)) == 1 or impurity == 0.0):
#             node.predicted_class = self._majority_class(y)
#             return node
#         feat_idx, threshold = self._best_split(X, y)
#         if feat_idx is None:
#             node.predicted_class = self._majority_class(y)
#             return node
#         node.feature_index = feat_idx
#         node.threshold = threshold
#         node.feature_name = (self.feature_names[feat_idx] if feat_idx < len(self.feature_names) else f"feature_{feat_idx}")
#         mask = X[:, feat_idx] <= threshold
#         node.left  = self._build(X[mask],  y[mask],  depth + 1)
#         node.right = self._build(X[~mask], y[~mask], depth + 1)
#         return node
#
#     def fit(self, X, y, feature_names=None):
#         self._node_counter = 0
#         self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
#         self.classes_ = [str(c) for c in np.unique(y)]
#         self.root = self._build(X, y.astype(str), depth=0)
#         return self
#
#     def _predict_one(self, x, node):
#         if node.is_leaf(): return node.predicted_class
#         if x[node.feature_index] <= node.threshold:
#             return self._predict_one(x, node.left)
#         return self._predict_one(x, node.right)
#
#     def predict(self, X):
#         if self.root is None: raise RuntimeError("Drzewo nie zostało wytrenowane.")
#         return np.array([self._predict_one(x, self.root) for x in X])
#
#     def predict_proba(self, X):
#         results = []
#         for x in X:
#             node = self.root
#             while not node.is_leaf():
#                 node = node.left if x[node.feature_index] <= node.threshold else node.right
#             total = sum(node.class_distribution.values())
#             results.append({k: v/total for k, v in node.class_distribution.items()})
#         return results
#
#     def to_dict(self):
#         if self.root is None: return {}
#         return {"params": {"criterion":self.criterion,"max_depth":self.max_depth,
#                            "min_example_count":self.min_example_count,"min_gain":self.min_gain},
#                 "feature_names": self.feature_names, "classes": self.classes_,
#                 "tree": self.root.to_dict()}
#
#     def count_nodes(self):
#         total = internal = leaves = 0
#         def _count(node):
#             nonlocal total, internal, leaves
#             if node is None: return
#             total += 1
#             if node.is_leaf(): leaves += 1
#             else: internal += 1; _count(node.left); _count(node.right)
#         _count(self.root)
#         return {"total": total, "internal": internal, "leaves": leaves}
#
#     def get_depth(self):
#         def _depth(node):
#             if node is None or node.is_leaf(): return 0
#             return 1 + max(_depth(node.left), _depth(node.right))
#         return _depth(self.root)
