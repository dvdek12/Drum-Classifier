import numpy as np
from collections import defaultdict


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.array(y_true, dtype=str)
    y_pred = np.array(y_pred, dtype=str)
    return float(np.mean(y_true == y_pred))


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str]) -> np.ndarray:
    n = len(classes)
    class_to_idx = {c: i for i, c in enumerate(classes)}
    matrix = np.zeros((n, n), dtype=int)

    for true, pred in zip(y_true, y_pred):
        if str(true) in class_to_idx and str(pred) in class_to_idx:
            i = class_to_idx[str(true)]
            j = class_to_idx[str(pred)]
            matrix[i][j] += 1

    return matrix


def precision_recall_f1(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str]) -> dict:
    y_true = np.array(y_true, dtype=str)
    y_pred = np.array(y_pred, dtype=str)

    results = {}
    precisions, recalls, f1s = [], [], []

    for cls in classes:
        tp = int(np.sum((y_true == cls) & (y_pred == cls)))
        fp = int(np.sum((y_true != cls) & (y_pred == cls)))
        fn = int(np.sum((y_true == cls) & (y_pred != cls)))

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

        results[cls] = {
            "precision": round(p, 4),
            "recall":    round(r, 4),
            "f1":        round(f, 4),
            "support":   int(np.sum(y_true == cls)),
        }
        precisions.append(p)
        recalls.append(r)
        f1s.append(f)

    results["macro_avg"] = {
        "precision": round(np.mean(precisions), 4),
        "recall":    round(np.mean(recalls), 4),
        "f1":        round(np.mean(f1s), 4),
        "support":   len(y_true),
    }

    return results


def evaluate_full(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: list[str],
    tree_stats: dict,
    training_time_ms: float,
) -> dict:
    acc = accuracy(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, classes)
    prf = precision_recall_f1(y_true, y_pred, classes)

    return {
        # Jakość klasyfikatora
        "quality": {
            "accuracy": round(acc, 4),
            "accuracy_pct": round(acc * 100, 2),
            "per_class": prf,
            "confusion_matrix": {
                "matrix": cm.tolist(),
                "labels": classes,
            },
        },
        # Efektywność (koszt) — rozmiar i złożoność drzewa
        "efficiency": {
            "tree_nodes_total":    tree_stats.get("total", 0),
            "tree_nodes_internal": tree_stats.get("internal", 0),
            "tree_leaves":         tree_stats.get("leaves", 0),
            "tree_actual_depth":   tree_stats.get("depth", 0),
            "training_time_ms":    round(training_time_ms, 2),
            "n_features":          tree_stats.get("n_features", 0),
            "n_train_samples":     tree_stats.get("n_train", 0),
            "n_test_samples":      tree_stats.get("n_test", 0),
        },
    }
