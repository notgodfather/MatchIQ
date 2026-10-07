"""
Baselines for record linkage:

  B0: Exact match on normalized phone (or email if phone missing).
  B1: Single-field fuzzy match on normalized name (Jaro-Winkler >= threshold).
  B2: Weighted average of field similarities with a tuned threshold.

All baselines use brute-force comparison on candidate pairs.
For Febrl4 (5k x 5k = 25M pairs), we use rapidfuzz.process.cdist for
vectorized string comparison.
"""
from __future__ import annotations

import time
import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
from matchiq.evaluation import evaluate


def _pairs_from_mask(mask: np.ndarray, ids_a: pd.Index, ids_b: pd.Index) -> set[tuple]:
    """Return set of (id_a, id_b) pairs where mask is True."""
    rows, cols = np.where(mask)
    return {(ids_a[r], ids_b[c]) for r, c in zip(rows, cols)}


def baseline_b0(df_a: pd.DataFrame, df_b: pd.DataFrame, true_pairs: set[tuple]) -> dict:
    """B0: exact match on normalized phone, fallback to normalized email."""
    t0 = time.perf_counter()

    pairs: set[tuple] = set()

    for field in ("_norm_phone", "_norm_email"):
        if field not in df_a.columns or field not in df_b.columns:
            continue
        # Build lookup: value → list of ids in B
        b_lookup: dict[str, list] = {}
        for idx, val in df_b[field].items():
            if val and not pd.isna(val):
                b_lookup.setdefault(val, []).append(idx)
        for idx, val in df_a[field].items():
            if val and not pd.isna(val) and val in b_lookup:
                for b_idx in b_lookup[val]:
                    pairs.add((idx, b_idx))

    elapsed = time.perf_counter() - t0
    metrics = evaluate(pairs, true_pairs)
    metrics["baseline"] = "B0"
    metrics["runtime_s"] = round(elapsed, 3)
    metrics["n_predicted"] = len(pairs)
    return metrics


def baseline_b1(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    true_pairs: set[tuple],
    threshold: float = 0.92,
) -> dict:
    """
    B1: single-field fuzzy match on normalized name using Jaro-Winkler.
    Uses rapidfuzz.process.cdist for vectorized computation.
    """
    t0 = time.perf_counter()

    if "_norm_name" not in df_a.columns or "_norm_name" not in df_b.columns:
        return {"baseline": "B1", "error": "name field not mapped"}

    names_a = df_a["_norm_name"].fillna("").tolist()
    names_b = df_b["_norm_name"].fillna("").tolist()

    # cdist returns scores in [0, 100]; we normalise to [0, 1]
    scores = process.cdist(names_a, names_b, scorer=fuzz.WRatio, score_cutoff=0)
    scores = scores / 100.0

    mask = scores >= threshold
    ids_a = df_a.index
    ids_b = df_b.index
    pairs = _pairs_from_mask(mask, ids_a, ids_b)

    elapsed = time.perf_counter() - t0
    metrics = evaluate(pairs, true_pairs)
    metrics["baseline"] = "B1"
    metrics["threshold"] = threshold
    metrics["runtime_s"] = round(elapsed, 3)
    metrics["n_predicted"] = len(pairs)
    return metrics


def _safe_cdist(vals_a: list[str], vals_b: list[str], scorer=fuzz.WRatio) -> np.ndarray:
    """Vectorized similarity matrix normalized to [0, 1]. Empty → 0.5 (neutral)."""
    a_clean = [v if v else "" for v in vals_a]
    b_clean = [v if v else "" for v in vals_b]
    scores = process.cdist(a_clean, b_clean, scorer=scorer, score_cutoff=0)
    return scores / 100.0


def baseline_b2(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    true_pairs: set[tuple],
    threshold: float = 0.60,
) -> dict:
    """
    B2: weighted average of field similarities with a threshold.
    Weights are tuned heuristically; missing fields contribute 0.
    """
    t0 = time.perf_counter()

    field_weights = {
        "_norm_name":     0.40,
        "_norm_phone":    0.30,
        "_norm_email":    0.20,
        "_norm_address":  0.10,
    }

    n_a, n_b = len(df_a), len(df_b)
    score_matrix = np.zeros((n_a, n_b), dtype=np.float32)
    weight_matrix = np.zeros((n_a, n_b), dtype=np.float32)

    for field, weight in field_weights.items():
        if field not in df_a.columns or field not in df_b.columns:
            continue

        vals_a = df_a[field].fillna("").tolist()
        vals_b = df_b[field].fillna("").tolist()

        avail_a = np.array([1.0 if v else 0.0 for v in vals_a], dtype=np.float32)
        avail_b = np.array([1.0 if v else 0.0 for v in vals_b], dtype=np.float32)
        avail_mask = np.outer(avail_a, avail_b)

        sim = _safe_cdist(vals_a, vals_b).astype(np.float32)

        score_matrix  += sim * avail_mask * weight
        weight_matrix += avail_mask * weight

    # Normalize by total available weight per pair (avoid div-by-zero)
    with np.errstate(invalid='ignore', divide='ignore'):
        final_scores = np.where(weight_matrix > 0, score_matrix / weight_matrix, 0.0)

    mask = final_scores >= threshold
    ids_a = df_a.index
    ids_b = df_b.index
    pairs = _pairs_from_mask(mask, ids_a, ids_b)

    elapsed = time.perf_counter() - t0
    metrics = evaluate(pairs, true_pairs)
    metrics["baseline"] = "B2"
    metrics["threshold"] = threshold
    metrics["runtime_s"] = round(elapsed, 3)
    metrics["n_predicted"] = len(pairs)
    return metrics
