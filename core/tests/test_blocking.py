"""
Tests for T3.1: Individual blockers.
"""
import pandas as pd
import pytest
from matchiq.blocking.rules import (
    block_exact,
    block_name_key,
    block_token,
    block_tfidf_knn,
    combine_blocks,
    _make_name_key,
)


@pytest.fixture
def dummy_dfs():
    df_a = pd.DataFrame([
        {"id": "a1", "phone": "9876543210", "email": "test@example.com", "name": "Rahul Kumar", "city": "Bengaluru", "address": "123 main road"},
        {"id": "a2", "phone": "1112223334", "email": "other@test.com", "name": "Priya Singh", "city": "Mumbai", "address": "apt 4"},
        {"id": "a3", "phone": None, "email": "missing@test.com", "name": "John Doe", "city": None, "address": "unknown"},
    ]).set_index("id")

    df_b = pd.DataFrame([
        {"id": "b1", "phone": "9876543210", "email": "test@example.com", "name": "R. Kumar", "city": "Bengaluru", "address": "123 main rd"},
        {"id": "b2", "phone": "0000000000", "email": "diff@test.com", "name": "Priya S.", "city": "Mumbai", "address": "apt 4"},
        {"id": "b3", "phone": "1112223334", "email": "other@test.com", "name": "Priya Singh", "city": "Mumbai", "address": "apt 4b"},
    ]).set_index("id")
    
    return df_a, df_b


def test_block_exact_phone(dummy_dfs):
    df_a, df_b = dummy_dfs
    pairs = block_exact(df_a, df_b, "phone")
    # a1 matches b1 on phone, a2 matches b3 on phone
    assert pairs == {("a1", "b1"), ("a2", "b3")}


def test_block_exact_email(dummy_dfs):
    df_a, df_b = dummy_dfs
    pairs = block_exact(df_a, df_b, "email")
    # a1 matches b1, a2 matches b3
    assert pairs == {("a1", "b1"), ("a2", "b3")}


def test_block_exact_missing_col(dummy_dfs):
    df_a, df_b = dummy_dfs
    pairs = block_exact(df_a, df_b, "nonexistent")
    assert pairs == set()


def test_make_name_key():
    # Metaphone of 'Kumar' is 'KMR' -> key: 'KMR_r_bengaluru'
    assert _make_name_key("Rahul Kumar", "Bengaluru") == "KMR_r_bengaluru"
    assert _make_name_key("R Kumar", "Bengaluru") == "KMR_r_bengaluru"
    assert _make_name_key("Rahul", None) == "RHL_r"
    assert _make_name_key(None, "Bengaluru") is None


def test_block_name_key(dummy_dfs):
    df_a, df_b = dummy_dfs
    pairs = block_name_key(df_a, df_b, name_col="name", city_col="city")
    # a1 ("Rahul Kumar", "Bengaluru") -> 'KMR_r_bengaluru'
    # b1 ("R. Kumar", "Bengaluru") -> 'KMR_r_bengaluru'
    # a2 ("Priya Singh", "Mumbai") -> 'SNK_p_mumbai'
    # b2 ("Priya S.", "Mumbai") -> 'S_p_mumbai'
    # b3 ("Priya Singh", "Mumbai") -> 'SNK_p_mumbai'
    assert ("a1", "b1") in pairs
    assert ("a2", "b3") in pairs
    assert ("a2", "b2") not in pairs


def test_block_token(dummy_dfs):
    df_a, df_b = dummy_dfs
    pairs = block_token(df_a, df_b, cols=["name", "address"], max_block_size=100)
    # a1: "rahul", "kumar", "123", "main", "road"
    # b1: "r.", "kumar", "123", "main", "rd"
    # match on "kumar", "123", "main"
    assert ("a1", "b1") in pairs
    
    # a2: "priya", "singh", "apt"
    # b2: "priya", "s.", "apt"
    # match on "priya", "apt"
    assert ("a2", "b2") in pairs
    
    # a2 and b3 match on "priya", "singh", "apt"
    assert ("a2", "b3") in pairs


def test_block_token_max_size_cap():
    # Make a highly connected graph that exceeds the max size
    df_a = pd.DataFrame({"id": [f"a{i}" for i in range(100)], "col": "common"}).set_index("id")
    df_b = pd.DataFrame({"id": [f"b{i}" for i in range(100)], "col": "common"}).set_index("id")
    
    # max_block_size 100 < 100*100=10000
    pairs = block_token(df_a, df_b, cols=["col"], max_block_size=100)
    assert pairs == set()


def test_block_tfidf_knn(dummy_dfs):
    df_a, df_b = dummy_dfs
    # We just want to ensure it runs and returns a set of candidate pairs.
    # a1 ("Rahul Kumar Bengaluru 123 main road") and b1 ("R. Kumar Bengaluru 123 main rd")
    pairs = block_tfidf_knn(df_a, df_b, cols=["name", "city", "address"], k=2, n_gram=3)
    assert isinstance(pairs, set)
    assert len(pairs) > 0
    # Because there are only 3 records, A1 should find B1 in top 2.
    assert ("a1", "b1") in pairs


def test_combine_blocks():
    b1 = {("a1", "b1")}
    b2 = {("a1", "b1"), ("a2", "b2")}
    b3 = {("a3", "b3")}
    combined = combine_blocks(b1, b2, b3)
    assert combined == {("a1", "b1"), ("a2", "b2"), ("a3", "b3")}
