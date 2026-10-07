"""
Training set builder with entity-level splits and field dropout.
"""
from __future__ import annotations

import collections
import numpy as np
import pandas as pd
from typing import Sequence
from matchiq.features.builder import build_features


def get_connected_components(pairs: set[tuple[str, str]]) -> list[set[str]]:
    """
    Find connected components in the bipartite graph of pairs.
    Returns a list of sets of record IDs (both A and B).
    """
    adj = collections.defaultdict(list)
    for a, b in pairs:
        adj[a].append(b)
        adj[b].append(a)

    visited = set()
    components = []

    for node in adj:
        if node not in visited:
            comp = set()
            queue = [node]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    comp.add(curr)
                    queue.extend(adj[curr])
            components.append(comp)

    return components


def make_entity_splits(
    pairs: set[tuple[str, str]], 
    train_frac: float = 0.7, 
    val_frac: float = 0.15,
    seed: int = 42
) -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    """
    Splits pairs into Train, Val, Test sets based on connected components.
    Prevents record leakage across splits.
    """
    components = get_connected_components(pairs)
    
    rng = np.random.default_rng(seed)
    rng.shuffle(components)

    train_pairs = set()
    val_pairs = set()
    test_pairs = set()

    n = len(components)
    train_end = int(n * train_frac)
    val_end = train_end + int(n * val_frac)

    train_comps = components[:train_end]
    val_comps = components[train_end:val_end]
    test_comps = components[val_end:]

    # A quick way to check if a pair belongs to a component: 
    # Just check where the first element (id_A) went.
    # We map id_A to its split.
    node_to_split = {}
    for comp in train_comps:
        for node in comp:
            node_to_split[node] = "train"
    for comp in val_comps:
        for node in comp:
            node_to_split[node] = "val"
    for comp in test_comps:
        for node in comp:
            node_to_split[node] = "test"

    for a, b in pairs:
        split = node_to_split.get(a, "test")
        if split == "train":
            train_pairs.add((a, b))
        elif split == "val":
            val_pairs.add((a, b))
        else:
            test_pairs.add((a, b))

    return train_pairs, val_pairs, test_pairs


def apply_field_dropout(
    features_df: pd.DataFrame, 
    dropout_rate: float = 0.2, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Randomly masks all features for a specific field (e.g., phone) 
    to simulate missing data during training.
    """
    if dropout_rate <= 0.0 or features_df.empty:
        return features_df.copy()

    rng = np.random.default_rng(seed)
    df_out = features_df.copy()
    
    # Identify fields from column names (e.g., name_jaro -> name)
    # The prefix before '_' is the field name.
    fields = set(col.split('_')[0] for col in df_out.columns if '_' in col)

    for field in fields:
        field_cols = [c for c in df_out.columns if c.startswith(field + "_")]
        missing_col = field + "_missing"
        
        if not field_cols:
            continue
            
        # For each row, drop this field with probability `dropout_rate`
        mask = rng.random(size=len(df_out)) < dropout_rate
        
        if missing_col in df_out.columns:
            # Set the missing flag to 1
            df_out.loc[mask, missing_col] = 1
            
            # Set other features for this field to NaN
            other_cols = [c for c in field_cols if c != missing_col]
            if other_cols:
                df_out.loc[mask, other_cols] = np.nan
        else:
            df_out.loc[mask, field_cols] = np.nan

    return df_out


def build_training_set(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    candidate_pairs: set[tuple[str, str]], 
    true_pairs: set[tuple[str, str]],
    field_dropout: float = 0.2,
    seed: int = 42
) -> pd.DataFrame:
    """
    Builds a labeled dataset from candidate pairs.
    Includes feature computation and optional field dropout for robustness.
    """
    features_df = build_features(df_a, df_b, candidate_pairs)
    if features_df.empty:
        return pd.DataFrame()

    if field_dropout > 0:
        features_df = apply_field_dropout(features_df, dropout_rate=field_dropout, seed=seed)

    # Add label
    labels = []
    for a, b in features_df.index:
        labels.append(1 if (a, b) in true_pairs else 0)
    
    features_df["label"] = labels
    return features_df
