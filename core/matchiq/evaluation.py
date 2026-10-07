"""
Evaluation: precision, recall, F1, and confusion matrix for record linkage.

Both predicted_pairs and true_pairs should be sets (or any iterables) of
2-tuples: (id_A, id_B).
"""
from __future__ import annotations


def evaluate(
    predicted_pairs: set[tuple],
    true_pairs: set[tuple],
) -> dict:
    """
    Compute precision, recall, F1, and confusion matrix components.

    Args:
        predicted_pairs: Set of (id_a, id_b) pairs predicted as matches.
        true_pairs:      Set of (id_a, id_b) pairs that are true matches.

    Returns:
        dict with keys: tp, fp, fn, precision, recall, f1
    """
    predicted = set(predicted_pairs)
    true = set(true_pairs)

    tp = len(predicted & true)
    fp = len(predicted - true)
    fn = len(true - predicted)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    return {
        "tp":        tp,
        "fp":        fp,
        "fn":        fn,
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    }
