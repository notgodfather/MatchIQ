"""
Tests for T4.2: Training set builder (entity split and field dropout).
"""
import pandas as pd
import numpy as np
import pytest

from matchiq.features.training import (
    get_connected_components, make_entity_splits, apply_field_dropout
)

def test_get_connected_components():
    pairs = {
        ("a1", "b1"),
        ("a1", "b2"),
        ("a2", "b3"),
        ("a3", "b4"),
        ("a3", "b5"),
        ("a4", "b5")
    }
    
    comps = get_connected_components(pairs)
    assert len(comps) == 3
    # Component 1
    assert {"a1", "b1", "b2"} in comps
    # Component 2
    assert {"a2", "b3"} in comps
    # Component 3
    assert {"a3", "a4", "b4", "b5"} in comps


def test_make_entity_splits_no_leakage():
    # Build a graph with 100 components
    pairs = set()
    for i in range(100):
        # each component has 2 pairs sharing an a_node
        pairs.add((f"a_{i}", f"b_{i}_1"))
        pairs.add((f"a_{i}", f"b_{i}_2"))
        
    train_pairs, val_pairs, test_pairs = make_entity_splits(pairs, train_frac=0.7, val_frac=0.15, seed=42)
    
    assert len(train_pairs) + len(val_pairs) + len(test_pairs) == 200
    
    # Check no leakage of a_nodes or b_nodes
    def get_nodes(p_set):
        nodes = set()
        for a, b in p_set:
            nodes.add(a)
            nodes.add(b)
        return nodes
        
    train_nodes = get_nodes(train_pairs)
    val_nodes = get_nodes(val_pairs)
    test_nodes = get_nodes(test_pairs)
    
    assert train_nodes.isdisjoint(val_nodes)
    assert train_nodes.isdisjoint(test_nodes)
    assert val_nodes.isdisjoint(test_nodes)


def test_apply_field_dropout():
    df = pd.DataFrame({
        "name_exact": [1.0, 1.0, 1.0],
        "name_jaro": [0.9, 0.8, 0.95],
        "name_missing": [0, 0, 0],
        "phone_exact": [1.0, 0.0, 1.0],
        "phone_missing": [0, 0, 0]
    })
    
    # dropout_rate=1.0 means all features should be dropped out
    df_dropped = apply_field_dropout(df, dropout_rate=1.0, seed=42)
    
    assert (df_dropped["name_missing"] == 1).all()
    assert df_dropped["name_exact"].isna().all()
    assert df_dropped["name_jaro"].isna().all()
    
    assert (df_dropped["phone_missing"] == 1).all()
    assert df_dropped["phone_exact"].isna().all()
    
    # dropout_rate=0.0 means nothing should change
    df_kept = apply_field_dropout(df, dropout_rate=0.0, seed=42)
    pd.testing.assert_frame_equal(df, df_kept)
