"""
Blocking rules to generate candidate pairs efficiently.

Rules:
  - block_exact: Exact match on a column (e.g., phone, email).
  - block_name_key: Exact match on a derived phonetic key (e.g., last token metaphone + first initial + city).
  - block_token: Exact match on any token in specified columns, ignoring blocks larger than max_size.
  - block_tfidf_knn: Top-K nearest neighbors using character n-grams and TF-IDF (sparse cosine).
"""
from __future__ import annotations

import collections
import time
from typing import Sequence

import jellyfish
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


def block_exact(df_a: pd.DataFrame, df_b: pd.DataFrame, col: str) -> set[tuple[str, str]]:
    """Generate candidate pairs where df_a[col] == df_b[col], ignoring nulls."""
    if col not in df_a.columns or col not in df_b.columns:
        return set()

    a_idx_name = "id_a"
    b_idx_name = "id_b"

    a_subset = df_a.reset_index()[[df_a.index.name or "index", col]].dropna(subset=[col]).rename(columns={df_a.index.name or "index": a_idx_name})
    b_subset = df_b.reset_index()[[df_b.index.name or "index", col]].dropna(subset=[col]).rename(columns={df_b.index.name or "index": b_idx_name})

    merged = pd.merge(a_subset, b_subset, on=col)
    return set(zip(merged[a_idx_name], merged[b_idx_name]))


def _make_name_key(name: str | None, city: str | None) -> str | None:
    """Metaphone of last name token + first initial (+ city if present)."""
    if not name or pd.isna(name):
        return None
    name = str(name).strip()
    if not name:
        return None

    tokens = name.split()
    if len(tokens) == 0:
        return None

    last_token = tokens[-1]
    first_initial = tokens[0][0].lower()
    
    # Use Metaphone for the phonetic part
    phonetic = jellyfish.metaphone(last_token)

    key = f"{phonetic}_{first_initial}"
    if city and not pd.isna(city):
        city = str(city).strip().replace(" ", "").lower()
        if city:
            key += f"_{city}"
            
    return key


def block_name_key(df_a: pd.DataFrame, df_b: pd.DataFrame, name_col: str = "name", city_col: str | None = None) -> set[tuple[str, str]]:
    """Block on a phonetic key derived from name and optionally city."""
    if name_col not in df_a.columns or name_col not in df_b.columns:
        return set()

    def apply_key(df):
        series = []
        for idx, row in df.iterrows():
            name_val = row[name_col]
            city_val = row[city_col] if city_col and city_col in df.columns else None
            series.append(_make_name_key(name_val, city_val))
        return pd.Series(series, index=df.index, name="name_key")

    key_a = apply_key(df_a)
    key_b = apply_key(df_b)

    a_idx_name = "id_a"
    b_idx_name = "id_b"

    a_subset = pd.DataFrame({a_idx_name: df_a.index, "name_key": key_a.values}).dropna(subset=["name_key"])
    b_subset = pd.DataFrame({b_idx_name: df_b.index, "name_key": key_b.values}).dropna(subset=["name_key"])

    merged = pd.merge(a_subset, b_subset, on="name_key")
    return set(zip(merged[a_idx_name], merged[b_idx_name]))


def block_token(df_a: pd.DataFrame, df_b: pd.DataFrame, cols: Sequence[str], max_block_size: int = 1000) -> set[tuple[str, str]]:
    """Block on matching tokens across the specified columns, dropping blocks larger than max_block_size."""
    def extract_tokens(df):
        # returns dict of token -> set of record IDs
        token_to_ids = collections.defaultdict(set)
        for col in cols:
            if col not in df.columns:
                continue
            for idx, val in df[col].dropna().items():
                if pd.isna(val):
                    continue
                tokens = str(val).lower().split()
                for t in tokens:
                    if len(t) > 1:  # ignore 1-letter tokens for blocking
                        token_to_ids[t].add(idx)
        return token_to_ids

    tokens_a = extract_tokens(df_a)
    tokens_b = extract_tokens(df_b)

    common_tokens = set(tokens_a.keys()) & set(tokens_b.keys())

    pairs = set()
    for t in common_tokens:
        ids_a = tokens_a[t]
        ids_b = tokens_b[t]
        
        # Cap to prevent huge cross products (e.g. "kumar", "road")
        if len(ids_a) * len(ids_b) <= max_block_size:
            for i in ids_a:
                for j in ids_b:
                    pairs.add((i, j))

    return pairs


def block_tfidf_knn(df_a: pd.DataFrame, df_b: pd.DataFrame, cols: Sequence[str], k: int = 50, n_gram: int = 3) -> set[tuple[str, str]]:
    """Block using char-ngram TF-IDF and Approximate Nearest Neighbors (cosine similarity)."""
    def concat_cols(df):
        present_cols = [c for c in cols if c in df.columns]
        if not present_cols:
            return pd.Series("", index=df.index)
        # Fill NA, convert to string, concatenate with space
        return df[present_cols].fillna("").astype(str).agg(" ".join, axis=1)

    text_a = concat_cols(df_a)
    text_b = concat_cols(df_b)
    
    if text_a.empty or text_b.empty:
        return set()

    # Fit TF-IDF on A + B to share vocabulary
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(n_gram, n_gram), min_df=2)
    
    # Sparse matrices
    vec_b = vectorizer.fit_transform(text_b)
    vec_a = vectorizer.transform(text_a)

    # Use NearestNeighbors for fast sparse kNN search
    # metric='cosine' uses sparse arrays natively in scikit-learn
    nbrs = NearestNeighbors(n_neighbors=min(k, len(text_b)), metric="cosine", n_jobs=1)
    nbrs.fit(vec_b)
    
    # distances are cosine distance, i.e., 1 - cosine similarity
    distances, indices = nbrs.kneighbors(vec_a)
    
    pairs = set()
    a_ids = text_a.index.to_list()
    b_ids = text_b.index.to_list()
    
    for i, a_id in enumerate(a_ids):
        # We can apply a strict distance threshold if we want, or just take top k.
        # kNN takes top k directly. We'll stick to top k to guarantee bounded pairs per A-record.
        for j_idx in indices[i]:
            pairs.add((a_id, b_ids[j_idx]))

    return pairs


def combine_blocks(*blocks: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """Union multiple block sets."""
    if not blocks:
        return set()
    result = blocks[0].copy()
    for b in blocks[1:]:
        result.update(b)
    return result
