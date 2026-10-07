"""
Tests for T4.1: Similarity functions and feature builder.
"""
import numpy as np
import pandas as pd
import pytest

from matchiq.features.similarity import (
    exact_equal, jaro_winkler, norm_levenshtein, token_sort_ratio,
    token_set_ratio, token_jaccard, phonetic_equal, length_diff,
    initial_compatible, phone_edit_dist_le_1, phone_last_7_equal,
    email_local_jaro, email_domain_equal, house_number_equal,
    pincode_first_3_equal
)
from matchiq.features.builder import build_features


def test_exact_equal():
    assert exact_equal("hello", "hello") == 1.0
    assert exact_equal("hello ", " hello") == 1.0
    assert exact_equal("hello", "world") == 0.0
    assert np.isnan(exact_equal("hello", None))
    assert np.isnan(exact_equal(np.nan, "world"))


def test_initial_compatible():
    assert initial_compatible("r kumar", "rahul kumar") == 1.0
    assert initial_compatible("rahul kumar", "r kumar") == 1.0
    assert initial_compatible("rahul k", "r kumar") == 1.0
    assert initial_compatible("r k", "rahul kumar") == 1.0
    assert initial_compatible("r k", "rohit kumar") == 1.0
    assert initial_compatible("s kumar", "rahul kumar") == 0.0
    assert initial_compatible("rahul", "rahul kumar") == 0.0
    assert np.isnan(initial_compatible(None, "rahul"))


def test_house_number_equal():
    assert house_number_equal("123 main st", "123 main street") == 1.0
    assert house_number_equal("apt 4b", "4b apartment") == 1.0
    assert house_number_equal("12 main st", "123 main st") == 0.0
    assert house_number_equal("main st", "main street") == 0.0
    assert np.isnan(house_number_equal("123", None))


def test_pincode_first_3_equal():
    assert pincode_first_3_equal("560001", "560002") == 1.0
    assert pincode_first_3_equal("110001", "560001") == 0.0
    assert pincode_first_3_equal("12", "12") == 0.0  # length < 3
    assert np.isnan(pincode_first_3_equal(None, "560001"))


def test_build_features():
    df_a = pd.DataFrame([
        {"id": "a1", "_norm_name": "rahul kumar", "_norm_phone": "9876543210"},
        {"id": "a2", "_norm_name": "priya singh", "_norm_phone": None},
    ]).set_index("id")

    df_b = pd.DataFrame([
        {"id": "b1", "_norm_name": "r kumar", "_norm_phone": "9876543211"},
        {"id": "b2", "_norm_name": "priya singh", "_norm_phone": "1112223334"},
    ]).set_index("id")

    candidate_pairs = {("a1", "b1"), ("a2", "b2")}
    
    features = build_features(df_a, df_b, candidate_pairs)
    
    assert len(features) == 2
    assert features.index.names == ["id_A", "id_B"]
    
    # Check some feature values
    a1_b1 = features.loc[("a1", "b1")]
    assert a1_b1["name_initial_comp"] == 1.0
    assert a1_b1["name_missing"] == 0
    assert a1_b1["phone_edit_dist_le_1"] == 1.0  # 9876543210 vs 9876543211
    
    a2_b2 = features.loc[("a2", "b2")]
    assert a2_b2["name_exact"] == 1.0
    assert a2_b2["name_missing"] == 0
    assert np.isnan(a2_b2["phone_exact"])  # because df_a phone is missing
    assert a2_b2["phone_missing"] == 1
